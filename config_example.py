# ============================================================
# config.py — Configuracion central de Listify
# ============================================================
# INSTRUCCIONES:
# 1. Copia este archivo y renombralo a "config.py"
# 2. Reemplaza los valores con tus API keys reales
# 3. NUNCA subas config.py a GitHub (ya esta en .gitignore)
# ============================================================

# ------ API de Anthropic (Claude) ------
# Conseguila en: https://console.anthropic.com
ANTHROPIC_API_KEY = "sk-ant-api03-TU_KEY_AQUI"

# Modelo de Claude
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ------ API de MercadoLibre ------
# Conseguila en: https://developers.mercadolibre.com.ar
APP_ID = "TU_APP_ID_AQUI"
APP_SECRET = "TU_SECRET_AQUI"
MELI_REDIRECT_URI = "http://localhost:8501/callback"

# ------ Base de datos ------
DATABASE_NAME = "listify.db"

# ------ Configuracion general ------
# MLA = Argentina, MLB = Brasil, MLC = Chile, MLM = Mexico, etc.
MELI_SITE_ID = "MLA"
