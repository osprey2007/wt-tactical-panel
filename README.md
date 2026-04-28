# WT Tactical Panel

Interface tactique locale pour War Thunder basee sur les donnees exposees via `http://localhost:8111`.

## Fonctions

- Telemetrie vehicule (vitesse, regime moteur, temperature, acceleration, altitude)
- Mini-carte tactique (joueur + objets detectes)
- Suivi des vehicules detruits (allies / ennemis) avec historique recent
- Acces depuis un autre PC du meme reseau Wi-Fi

## Prerequis

- War Thunder lance avec l'API locale active (`localhost:8111`)
- Python 3.10+

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

Depuis le PC de jeu: `http://localhost:8000`

Depuis un autre PC du meme Wi-Fi: `http://IP_DU_PC_DE_JEU:8000`

Pour trouver ton IP locale Windows:

```powershell
ipconfig
```

Prends l'adresse IPv4 de ta carte Wi-Fi.

## Note importante

Cet outil n'utilise que les donnees exposees volontairement par War Thunder via son endpoint local. Verifie toujours les regles du jeu et d'evenements/serveurs que tu utilises.
