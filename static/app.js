const els = {
  status: document.getElementById("statusBadge"),
  speed: document.getElementById("speed"),
  throttle: document.getElementById("throttle"),
  rpm: document.getElementById("rpm"),
  temp: document.getElementById("temp"),
  altitude: document.getElementById("altitude"),
  accel: document.getElementById("accel"),
  allyLoss: document.getElementById("allyLoss"),
  enemyLoss: document.getElementById("enemyLoss"),
  eventsList: document.getElementById("eventsList"),
  unitCount: document.getElementById("unitCount"),
};

const canvas = document.getElementById("mapCanvas");
const ctx = canvas.getContext("2d");

function n(v, digits = 0) {
  const num = Number(v);
  if (!Number.isFinite(num)) return "0";
  return num.toFixed(digits);
}

function setVehicle(v) {
  els.speed.textContent = `${n(v.speed_kmh)} km/h`;
  els.throttle.textContent = `${n(v.throttle_pct)} %`;
  els.rpm.textContent = `${n(v.rpm)} rpm`;
  els.temp.textContent = `${n(v.engine_temp)} C`;
  els.altitude.textContent = `${n(v.altitude_m)} m`;
  els.accel.textContent = `${n(v.accel_g, 2)} g`;
}

function setEvents(events) {
  els.eventsList.innerHTML = "";
  if (!events.length) {
    const li = document.createElement("li");
    li.textContent = "Aucun evenement detecte pour le moment.";
    els.eventsList.appendChild(li);
    return;
  }

  events.forEach((ev) => {
    const li = document.createElement("li");
    li.className = ev.side;
    const dt = new Date(ev.ts * 1000);
    li.textContent = `[${dt.toLocaleTimeString()}] ${ev.side.toUpperCase()} - ${ev.label}`;
    els.eventsList.appendChild(li);
  });
}

function mapBounds(units) {
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;

  units.forEach((u) => {
    const x = Number(u.x) || 0;
    const y = Number(u.y) || 0;
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  });

  if (!units.length || minX === maxX || minY === maxY) {
    return { minX: -1, maxX: 1, minY: -1, maxY: 1 };
  }

  return { minX, maxX, minY, maxY };
}

function drawMap(units) {
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = "rgba(140, 192, 230, 0.18)";
  ctx.lineWidth = 1;

  for (let x = 0; x <= w; x += w / 10) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }

  for (let y = 0; y <= h; y += h / 10) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  const b = mapBounds(units);
  const pad = 30;

  const sx = (x) => pad + ((x - b.minX) / (b.maxX - b.minX)) * (w - pad * 2);
  const sy = (y) => h - (pad + ((y - b.minY) / (b.maxY - b.minY)) * (h - pad * 2));

  units.forEach((u, idx) => {
    const x = sx(Number(u.x) || 0);
    const y = sy(Number(u.y) || 0);

    let color = "#58d66c";
    if (u.side === "enemy") color = "#ff5a5f";
    if (idx === 0) color = "#55a9ff";

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, idx === 0 ? 6 : 4, 0, Math.PI * 2);
    ctx.fill();

    if (u.destroyed) {
      ctx.strokeStyle = "#fefefe";
      ctx.beginPath();
      ctx.moveTo(x - 5, y - 5);
      ctx.lineTo(x + 5, y + 5);
      ctx.moveTo(x + 5, y - 5);
      ctx.lineTo(x - 5, y + 5);
      ctx.stroke();
    }
  });
}

async function tick() {
  try {
    const res = await fetch("/api/snapshot", { cache: "no-store" });
    const data = await res.json();

    if (!data.online) {
      els.status.textContent = `Hors ligne: ${data.last_error || "API indisponible"}`;
      els.status.style.borderColor = "#ff5a5f";
      return;
    }

    els.status.textContent = "Connecte a War Thunder";
    els.status.style.borderColor = "#58d66c";

    setVehicle(data.vehicle || {});
    els.allyLoss.textContent = `${data.destroyed?.ally ?? 0}`;
    els.enemyLoss.textContent = `${data.destroyed?.enemy ?? 0}`;
    setEvents(data.recent_events || []);

    const units = data.map?.units || [];
    els.unitCount.textContent = `${units.length} unites`;
    drawMap(units);
  } catch (err) {
    els.status.textContent = `Erreur client: ${err.message}`;
    els.status.style.borderColor = "#ff5a5f";
  }
}

tick();
setInterval(tick, 700);
