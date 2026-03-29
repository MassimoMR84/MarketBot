import streamlit as st
import os

# Cuando la app está en Streamlit Cloud, lee de los "Secrets"
# Si falla (por ejemplo, en tu compu local), intenta leer variables de entorno o usa un default
try:
    # Agregá acá todas las variables que tu app necesite
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