import os
import requests
import yt_dlp
from openai import OpenAI
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# 1. CONFIGURATION
load_dotenv(".env")
app = App(token=os.getenv("SLACK_BOT_TOKEN"))
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- GÉNÉRATION DE FICHIERS ---

def creer_word(texte, nom_fichier):
    doc = Document()
    doc.add_heading('Transcription Vidéo', 0)
    doc.add_paragraph(texte)
    path = f"{nom_fichier}.docx"
    doc.save(path)
    return path

def creer_pdf(texte, nom_fichier):
    path = f"{nom_fichier}.pdf"
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph("Transcription Vidéo", styles['Title']), Spacer(1, 12)]
    # Formatage des sauts de ligne pour le moteur PDF
    elements.append(Paragraph(texte.replace('\n', '<br/>'), styles['Normal']))
    doc.build(elements)
    return path

# --- IA : RÉSUMÉ & TRANSCRIPTION ---

def generer_resume(texte_brut):
    try:
        reponse = client_openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Résume cette transcription avec un titre et 3 points clés de manière professionnelle."},
                {"role": "user", "content": texte_brut}
            ]
        )
        return reponse.choices[0].message.content
    except Exception:
        return "Résumé IA indisponible pour le moment."

def transcrire(chemin):
    with open(chemin, "rb") as f:
        return client_openai.audio.transcriptions.create(model="whisper-1", file=f).text

# --- LOGIQUE DE TRAITEMENT LOURD (LAZY LISTENER) ---

def do_heavy_lifting(event, say, client):
    """Effectue le travail lourd en tâche de fond pour éviter les timeouts Slack."""
    files = event.get("files", [])
    text = event.get("text", "")
    channel = event["channel"]

    try:
        # CAS A : Vidéo importée du PC
        if files and files[0]["mimetype"].startswith("video/"):
            say("📥 Vidéo reçue ! Analyse en cours...")
            headers = {"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
            r = requests.get(files[0]["url_private"], headers=headers)
            with open("temp.mp4", "wb") as f: 
                f.write(r.content)
            os.system("ffmpeg -i temp.mp4 -q:a 0 -map a audio.mp3 -y")
            transcription = transcrire("audio.mp3")

        # CAS B : Lien (YouTube, etc.)
        elif text and "http" in text:
            url = text.replace("<", "").replace(">", "").split("|")[0].split("?")[0]
            say("⏳ Lien détecté ! Téléchargement de l'audio...")
            opts = {
                'format': 'bestaudio/best', 
                'outtmpl': 'audio', 
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
                'overwrites': True
            }
            # Correction de l'indentation ici
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            transcription = transcrire("audio.mp3")
        else:
            return

        # 1. Génération du résumé par GPT-4o
        resume = generer_resume(transcription)
        say(f"📝 *RÉSUMÉ ET POINTS CLÉS* :\n\n{resume}")

        # 2. Envoi de la transcription avec boutons (limite de 1900 car. pour Slack)
        client.chat_postMessage(
            channel=channel,
            blocks=[
                {
                    "type": "section", 
                    "text": {"type": "mrkdwn", "text": f"✅ *Transcription terminée* :\n\n{transcription[:2000]}..."}
                },
                {
                    "type": "actions", 
                    "elements": [
                        {
                            "type": "button", 
                            "text": {"type": "plain_text", "text": "Format Word 🟦"}, 
                            "action_id": "gen_word", 
                            "value": transcription[:1900] # Sécurité pour éviter l'erreur invalid_blocks
                        },
                        {
                            "type": "button", 
                            "text": {"type": "plain_text", "text": "Format PDF 🟥"}, 
                            "action_id": "gen_pdf", 
                            "value": transcription[:1900] # Sécurité pour éviter l'erreur invalid_blocks
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        say(f"❌ Erreur lors du traitement : {str(e)}")

# Utilisation du mode lazy pour répondre immédiatement à Slack
app.event("message")(ack=lambda ack: ack(), lazy=[do_heavy_lifting])

# --- ACTIONS DES BOUTONS ---

@app.action("gen_word")
def handle_word(ack, body, client):
    ack()
    texte_bouton = body["actions"][0]["value"]
    path = creer_word(texte_bouton, "Transcription_Boss")
    client.files_upload_v2(channel=body["channel"]["id"], file=path, title="Transcription.docx")

@app.action("gen_pdf")
def handle_pdf(ack, body, client):
    ack()
    texte_bouton = body["actions"][0]["value"]
    path = creer_pdf(texte_bouton, "Transcription_Boss")
    client.files_upload_v2(channel=body["channel"]["id"], file=path, title="Transcription.pdf")

# --- LANCEMENT ---
if __name__ == "__main__":
    print("⚡ Bot professionnel activé sur ton HP EliteBook !")
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()