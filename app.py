from __future__ import annotations

import os
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

WT_BASE_URL = os.getenv("WT_BASE_URL", "http://10.88.92.208:8112")
WT_PANEL_HOST = os.getenv("WT_PANEL_HOST", "0.0.0.0")
WT_PANEL_PORT = int(os.getenv("WT_PANEL_PORT", "8000"))
POLL_INTERVAL = 0.6
EVENT_MEMORY = 30
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@dataclass
class DestroyEvent:
    ts: float
    side: str
    label: str


class WTCollector:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._lock = threading.Lock()
        self._snapshot: dict[str, Any] = {
            "online": False,
            "last_error": "Waiting for first poll",
            "vehicle": {},
            "map": {},
            "destroyed": {"ally": 0, "enemy": 0},
            "recent_events": [],
            "updated_at": 0,
        }
        self._seen_destroyed: set[str] = set()
        self._events: deque[DestroyEvent] = deque(maxlen=EVENT_MEMORY)

    def _fetch_json(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        response = requests.get(url, timeout=0.5)
        response.raise_for_status()
        return response.json()

    def _extract_vehicle(self, state: dict[str, Any], indicators: dict[str, Any]) -> dict[str, Any]:
        return {
            "speed_kmh": state.get("TAS, km/h") or indicators.get("speed") or 0,
            "throttle_pct": state.get("throttle 1, %") or indicators.get("throttle") or 0,
            "rpm": state.get("RPM throttle 1, rpm") or indicators.get("rpm") or 0,
            "engine_temp": state.get("water temp, C") or state.get("oil temp, C") or 0,
            "altitude_m": state.get("H, m") or 0,
            "accel_g": state.get("Ny") or 0,
        }

    def _classify_side(self, obj: dict[str, Any]) -> str:
        relation = str(obj.get("relation", "")).lower()
        color = str(obj.get("color", "")).lower()
        if "enemy" in relation or color in {"#ff0000", "#f00", "red"}:
            return "enemy"
        if "ally" in relation or color in {"#00ff00", "#0f0", "green"}:
            return "ally"
        # Heuristique: rouge proche d'ennemi dans certaines APIs de jeu
        if "f00" in color or "ff3" in color:
            return "enemy"
        return "ally"

    def _extract_destroyed(self, map_obj: dict[str, Any]) -> tuple[dict[str, int], list[dict[str, Any]], list[DestroyEvent]]:
        ally = 0
        enemy = 0
        all_units: list[dict[str, Any]] = []
        new_events: list[DestroyEvent] = []

        groups = []
        if isinstance(map_obj, dict):
            for key in ("aircraft", "ground", "ships", "units", "markers", "objects"):
                bucket = map_obj.get(key)
                if isinstance(bucket, list):
                    groups.extend(bucket)

            # Certains dumps WT utilisent une liste principale sous "map_obj"
            generic_bucket = map_obj.get("map_obj")
            if isinstance(generic_bucket, list):
                groups.extend(generic_bucket)

        now = time.time()
        for obj in groups:
            if not isinstance(obj, dict):
                continue

            side = self._classify_side(obj)
            obj_id = str(obj.get("id") or obj.get("guid") or obj.get("name") or f"anon-{len(all_units)}")
            is_destroyed = bool(obj.get("isDead") or obj.get("dead") or obj.get("destroyed") or obj.get("state") == "dead")

            x = obj.get("x") or obj.get("sx") or obj.get("lon") or 0
            y = obj.get("y") or obj.get("sy") or obj.get("lat") or 0
            label = str(obj.get("name") or obj.get("icon") or "unit")

            all_units.append(
                {
                    "id": obj_id,
                    "side": side,
                    "destroyed": is_destroyed,
                    "x": x,
                    "y": y,
                    "label": label,
                    "icon": obj.get("icon", ""),
                }
            )

            if not is_destroyed:
                continue

            if side == "enemy":
                enemy += 1
            else:
                ally += 1

            if obj_id not in self._seen_destroyed:
                self._seen_destroyed.add(obj_id)
                new_events.append(DestroyEvent(ts=now, side=side, label=label))

        return {"ally": ally, "enemy": enemy}, all_units, new_events

    def poll_once(self) -> None:
        try:
            state = self._fetch_json("/state")
            indicators = self._fetch_json("/indicators")
            map_info = self._fetch_json("/map_info.json")
            map_obj = self._fetch_json("/map_obj.json")

            vehicle = self._extract_vehicle(state if isinstance(state, dict) else {}, indicators if isinstance(indicators, dict) else {})
            destroyed, units, new_events = self._extract_destroyed(map_obj if isinstance(map_obj, dict) else {})

            for event in new_events:
                self._events.appendleft(event)

            snapshot = {
                "online": True,
                "last_error": "",
                "vehicle": vehicle,
                "map": {
                    "info": map_info,
                    "units": units,
                },
                "destroyed": destroyed,
                "recent_events": [
                    {"ts": e.ts, "side": e.side, "label": e.label}
                    for e in list(self._events)
                ],
                "updated_at": time.time(),
            }
        except Exception as exc:  # noqa: BLE001 - on veut garder l'UI vivante meme en cas d'erreur API
            with self._lock:
                self._snapshot = {
                    **self._snapshot,
                    "online": False,
                    "last_error": str(exc),
                    "updated_at": time.time(),
                }
            return

        with self._lock:
            self._snapshot = snapshot

    def read_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._snapshot)


collector = WTCollector(WT_BASE_URL)
@asynccontextmanager
async def lifespan(_: FastAPI):
    def loop() -> None:
        while True:
            collector.poll_once()
            time.sleep(POLL_INTERVAL)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    yield


app = FastAPI(title="WT Tactical Panel", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/snapshot")
def snapshot() -> JSONResponse:
    return JSONResponse(content=collector.read_snapshot())


if __name__ == "__main__":
    uvicorn.run("app:app", host=WT_PANEL_HOST, port=WT_PANEL_PORT)
