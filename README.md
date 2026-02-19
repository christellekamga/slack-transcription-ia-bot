# Bot de transcription & résumé (Slack + OpenAI)

## Description du projet
Ce projet est un bot Slack qui récupère une vidéo (fichier envoyé depuis le PC) ou un lien (YouTube / autres plateformes), extrait l’audio, transcrit le contenu avec Whisper, puis génère un résumé avec GPT‑4o. Il permet ensuite d’exporter la transcription en **Word (.docx)** ou **PDF (.pdf)**.

## Fonctionnalités
- **Transcription Whisper** : transcription automatique à partir d’un fichier audio (MP3) extrait d’une vidéo.
- **Résumé GPT-4o** : génération d’un résumé professionnel + 3 points clés.
- **Export Word/PDF** : création d’un document Word et d’un PDF à partir de la transcription.
- **Support fichiers PC & Liens** : prise en charge des vidéos uploadées dans Slack et des liens (YouTube, etc.).

## Installation

### Prérequis
- **Python 3.10+** (recommandé)
- **FFmpeg** (indispensable pour convertir les vidéos en MP3)

Sur Ubuntu/Debian :

```bash
sudo apt update
sudo apt install -y ffmpeg
```

### Installation des dépendances Python
Depuis la racine du projet :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration (.env)
Créez un fichier `.env` à la racine du projet (il est ignoré par Git) :

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
OPENAI_API_KEY=sk-...
```

## Utilisation

Lancez le bot depuis la racine du projet :

```bash
python src/main.py
```

Ensuite, dans Slack :
- **Envoyez une vidéo** dans un canal où le bot est présent (upload direct).
- Ou **postez un lien** (YouTube, etc.) dans un message.

Le bot :
1. Extrait l’audio (FFmpeg)
2. Transcrit avec Whisper
3. Génère un résumé avec GPT‑4o
4. Propose l’export **Word** ou **PDF** via des boutons
