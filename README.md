# 💤 Synthétiseur de Rêves – Application Streamlit

Cette application permet :
- D’enregistrer ou importer un rêve audio
- D’en obtenir une transcription
- D’analyser les émotions contenues dans le rêve (via Mistral)
- De générer une image onirique (via Clipdrop)
- De sauvegarder et visualiser les rêves

## 🚀 Lancement local

```bash
# 1. Cloner ou copier le projet
# 2. Créer un environnement virtuel (optionnel mais recommandé)
python -m venv venv
source venv/bin/activate    # ou venv\Scripts\activate sous Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer un fichier .env avec vos clés API :
