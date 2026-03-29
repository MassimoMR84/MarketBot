import streamlit as st
import os

# --- Variables no secretas (pueden ir a GitHub sin problema) ---
DATABASE_NAME = "database.db"  # <- AGREGA ESTA LÍNEA (chequeá si le habías puesto otro nombre)
CLAUDE_MODEL = "claude-3-5-sonnet-20240620" 

# --- Variables secretas ---
try:
    CLAUDE_API_KEY = st.secrets["CLAUDE_API_KEY"]
    MELI_APP_ID = st.secrets.get("MELI_APP_ID", "")
    MELI_CLIENT_SECRET = st.secrets.get("MELI_CLIENT_SECRET", "")
    MELI_SITE_ID = st.secrets.get("MELI_SITE_ID", "MLA")
except (FileNotFoundError, KeyError):
    # Valores de prueba para cuando corrés la app localmente en VS Code
    CLAUDE_API_KEY = "sk-ant-aca-pones-tu-clave-local-para-probar"
    MELI_APP_ID = "tu-app-id-local"
    MELI_CLIENT_SECRET = "tu-secret-local"
    MELI_SITE_ID = "MLA"
    

    # ... el resto de tu código ...