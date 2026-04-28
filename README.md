# WT Tactical Panel

Interface tactique pour War Thunder basee sur les donnees exposees via `http://localhost:8111`.

## Fonctions

- Telemetrie vehicule (vitesse, regime moteur, temperature, acceleration, altitude)
- Mini-carte tactique (joueur + objets detectes)
- Suivi des vehicules detruits (allies / ennemis) avec historique recent
- Acces depuis un autre PC du meme reseau Wi-Fi

## Prerequis

- War Thunder lance avec l'API locale active (`localhost:8111`)
- Python 3.10+

## Architecture conseillee (ton cas)

- PC Windows: fait tourner War Thunder
- PC Fedora: fait tourner cette application web

Important: `localhost:8111` est local au PC Windows. Le PC Fedora ne peut pas y acceder directement.

Solution: lancer un mini relay HTTP sur Windows, puis faire pointer Fedora dessus.

## Installation

```powershell
cd D:\Users\jean\Documents\wt-tactical-panel
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement

```powershell
uvicorn app:app --host 0.0.0.0 --port 8000
```

Tu peux aussi definir la source WT a lire (par defaut: `http://localhost:8111`):

```bash
WT_BASE_URL=http://IP_WINDOWS:8112 python app.py
```

## Setup Windows -> Fedora

### 1) Sur le PC Windows (War Thunder)

Dans le repo, lance le relay:

```powershell
python scripts\wt_relay.py
```

Le relay expose uniquement:
- `/state`
- `/indicators`
- `/map_info.json`
- `/map_obj.json`

Adresse relay attendue: `http://IP_WINDOWS:8112`

### 2) Sur le PC Fedora (application)

Lance le panel en pointant vers l'IP du Windows:

```bash
WT_BASE_URL=http://IP_WINDOWS:8112 python app.py
```

Puis ouvre:
- Depuis Fedora: `http://localhost:8000`
- Depuis un autre device du Wi-Fi: `http://IP_FEDORA:8000`

Pour trouver ton IP locale Windows:

```powershell
ipconfig
```

Prends l'adresse IPv4 de ta carte Wi-Fi.

## Note importante

Cet outil n'utilise que les donnees exposees volontairement par War Thunder via son endpoint local. Verifie toujours les regles du jeu et d'evenements/serveurs que tu utilises.
