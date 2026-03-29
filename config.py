# ============================================================
# config.py — Configuracion central de Orquesta
# ============================================================
# Lee de st.secrets (Streamlit Cloud) o usa fallbacks locales.
# IMPORTANTE: Los nombres de variables DEBEN coincidir con los
# que usan vision.py, seo.py, pricing.py, copywriter.py, auth.py y api.py
# ============================================================

import os

try:
    import streamlit as st
    _secrets = st.secrets
    _usar_secrets = True
except Exception:
    _usar_secrets = False


def _get(key, default=""):
    """Busca en st.secrets, luego en env vars, luego default."""
    if _usar_secrets:
        try:
            return _secrets[key]
        except (KeyError, AttributeError):
            pass
    return os.environ.get(key, default)


# ------ API de Anthropic (Claude) ------
# Los agentes usan: config.ANTHROPIC_API_KEY
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", "sk-ant-api03-TU_KEY_AQUI")

# Los agentes usan: config.CLAUDE_MODEL
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# ------ API de MercadoLibre ------
# auth.py y api.py usan: config.APP_ID, config.APP_SECRET
APP_ID = _get("APP_ID", "TU_APP_ID_AQUI")
APP_SECRET = _get("APP_SECRET", "TU_SECRET_AQUI")
MELI_REDIRECT_URI = _get("MELI_REDIRECT_URI", "http://localhost:8501/callback")

# ------ Base de datos ------
DATABASE_NAME = _get("DATABASE_NAME", "database.db")

# ------ Configuracion general ------
# pricing.py usa: config.MELI_SITE_ID
MELI_SITE_ID = _get("MELI_SITE_ID", "MLA")