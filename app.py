# app.py
import os
import json
import math
import base64
from io import BytesIO
from datetime import datetime

import streamlit as st
import requests
from dotenv import load_dotenv
from mistralai import Mistral
from groq import Groq

# Charger les variables d’environnement
load_dotenv()

GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
MISTRAL_API_KEY  = os.getenv("MISTRAL_API_KEY")
CLIPDROP_API_KEY = os.getenv("CLIPDROP_API_KEY")

# Vérification
if not all([GROQ_API_KEY, MISTRAL_API_KEY, CLIPDROP_API_KEY]):
    st.error("❌ Clés API manquantes. Vérifie ton fichier .env.")
    st.stop()

# Prompt d’analyse émotionnelle
PROMPT_EMOTION = """
Tu es un assistant d’analyse d’émotions. 
Tu dois renvoyer STRICTEMENT un objet JSON, sans texte explicatif, contenant six scores
numériques entre 0 et 1 (inclus) pour :
heureux, anxieux, triste, en_colere, fatigue, apeure.
Attention l'utilisateur peut faire preuve d'ironie.
Aucun autre champ, commentaire ou formatage n’est autorisé.
"""

# Fonctions utilitaires
def softmax(pred):
    exp = {k: math.exp(v * 10) for k, v in pred.items()}
    total = sum(exp.values())
    return {k: round(v / total, 3) for k, v in exp.items()}

def transcribe(audio_bytes):
    client = Groq(api_key=GROQ_API_KEY)
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_bytes.getvalue())
    with open("temp_audio.wav", "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=f,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            language="fr"
        )
    return transcription.text

def analyse_emotion(text):
    client = Mistral(api_key=MISTRAL_API_KEY)
    response = client.chat.complete(
        model="mistral-small",
        messages=[
            {"role": "system", "content": PROMPT_EMOTION},
            {"role": "user",   "content": f"Analyse ce texte : {text}"}
        ],
    )
    raw = json.loads(response.choices[0].message.content)
    return softmax(raw)

def generate_image(prompt):
    prompt = prompt.strip().replace("\n", " ")[:400]
    headers = {
        "x-api-key": CLIPDROP_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post("https://clipdrop-api.co/text-to-image/v1", headers=headers, json={"prompt": prompt})
    if response.status_code != 200:
        st.error(f"Erreur Clipdrop : {response.status_code} – {response.text}")
        response.raise_for_status()
    return response.content

def save_dream(text, emotions, image_bytes):
    img_b64 = base64.b64encode(image_bytes).decode('utf-8')
    record = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "texte": text,
        "emotions": emotions,
        "image_b64": img_b64
    }
    dreams = []
    if os.path.exists("dreams.json"):
        with open("dreams.json", "r") as f:
            dreams = json.load(f)
    dreams.append(record)
    with open("dreams.json", "w") as f:
        json.dump(dreams, f, indent=2)

def show_dashboard():
    st.header("📊 Tableau de bord des rêves")
    if not os.path.exists("dreams.json"):
        st.info("Aucun rêve enregistré pour le moment.")
        return
    with open("dreams.json", "r") as f:
        dreams = json.load(f)
    for d in reversed(dreams):
        with st.expander(f"🗓️ {d['date']}"):
            st.text_area("Texte du rêve", d["texte"], height=100, key=f"text_{d['date']}")
            st.json(d["emotions"])
            st.image(base64.b64decode(d["image_b64"]), caption="Image générée")

# Interface Streamlit
st.set_page_config(page_title="Synthétiseur de rêves", page_icon="💤")
st.title("💤 Synthétiseur de rêves")

page = st.sidebar.selectbox("Navigation", ["Synthétiseur", "Tableau de bord", "Aide"])

if page == "Synthétiseur":
    audio_option = st.radio("Saisir votre rêve :", ("Uploader un fichier audio", "Enregistrer l'audio"))
    audio_data = None

    if audio_option == "Uploader un fichier audio":
        file = st.file_uploader("Téléchargez un fichier audio (.wav, .mp3 ou .m4a)", type=["wav", "mp3", "m4a"])
        if file:
            audio_data = BytesIO(file.read())
            st.audio(audio_data)
            st.success("✅ Fichier audio chargé")
    else:
        recorded = st.audio_input("Enregistrez votre rêve")
        if recorded:
            audio_data = BytesIO(recorded.getvalue())
            st.audio(audio_data)
            st.success("✅ Audio enregistré")

    if audio_data:
        st.info("🎧 Transcription...")
        text = transcribe(audio_data)
        st.text_area("Texte extrait", text, height=150)

        st.info("🧠 Analyse des émotions...")
        emotions = analyse_emotion(text)
        st.json(emotions)

        st.info("🎨 Génération de l’image...")
        img = generate_image(text)
        st.image(img, caption="Image du rêve générée")

        save_dream(text, emotions, img)
        st.success("💾 Rêve sauvegardé !")

elif page == "Tableau de bord":
    show_dashboard()

elif page == "Aide":
    st.header("❓ Aide - Synthétiseur de rêves")
    st.markdown("""
Bienvenue dans le Synthétiseur de rêves !

### 🧾 Mode d’emploi
1. Allez dans **Synthétiseur**
2. Enregistrez ou importez votre rêve
3. L’IA :
   - transcrit,
   - analyse les émotions,
   - génère une image,
   - sauvegarde tout.

### 📊 Tableau de bord
Tous vos rêves sont listés dans **Tableau de bord**

### 🔐 Données
Les rêves sont enregistrés localement dans `dreams.json`

""")
