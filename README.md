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

- PC Windows: fait tourner War Thunder et le relay local
- PC Fedora: fait tourner le tableau de bord

Important: `localhost:8111` est local au PC Windows. Le PC Fedora ne peut pas y acceder directement, donc il passe par le relay Windows.

## Installation

```powershell
cd D:\Users\jean\Documents\wt-tactical-panel
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Mise en place rapide

Une seule fois:

1. Copie [config.example.env](config.example.env) en `config.env`
2. Sur Fedora, rends le script exécutable: `chmod +x start-fedora.sh`

Ensuite, a chaque session:

1. Sur Windows, lance [start-windows-relay.bat](start-windows-relay.bat)
2. Sur Fedora, lance [start-fedora.sh](start-fedora.sh)

## Lancement manuel

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

## Commandes courtes

- Fedora: `./start-fedora.sh`
- Windows relay: `start-windows-relay.bat`
- L'IP Windows est deja fixee sur `10.88.92.208` dans la config de demarrage
- Si `8000` est deja pris, le dashboard saute automatiquement sur `8001`, `8002`, etc.

## Ce que fait chaque fichier

- [start-windows-relay.bat](start-windows-relay.bat): expose l'API WT du PC Windows sur le port `8112`
- [start-fedora.sh](start-fedora.sh): lance le dashboard Fedora avec `config.env`
- [config.env](config.env): garde l'adresse du PC Windows sans la retaper

## Note importante

Cet outil n'utilise que les donnees exposees volontairement par War Thunder via son endpoint local. Verifie toujours les regles du jeu et d'evenements/serveurs que tu utilises.
