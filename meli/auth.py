# ============================================================
# meli/auth.py — Autenticacion con MercadoLibre (OAuth2)
# ============================================================
# MercadoLibre necesita que el usuario "permita" a nuestra app
# acceder a su cuenta. Esto se hace con OAuth2.
#
# El flujo es:
# 1. Generamos un link para que el usuario se loguee en MeLi
# 2. MeLi redirige al usuario de vuelta con un "codigo"
# 3. Cambiamos ese codigo por un "token" (la llave real)
# 4. Con ese token podemos publicar productos
# ============================================================

import requests
import config


def obtener_url_autorizacion():
    """
    Genera el link donde el usuario tiene que ir
    para autorizar nuestra app en MercadoLibre.
    
    Retorna: URL como string
    """
    url = (
        f"https://auth.mercadolibre.com.ar/authorization"
        f"?response_type=code"
        f"&client_id={config.APP_ID}"
        f"&redirect_uri={config.MELI_REDIRECT_URI}"
    )
    return url


def obtener_token(codigo_autorizacion):
    """
    Cambia el codigo de autorizacion por un access_token.
    
    El codigo lo recibimos cuando MeLi redirige al usuario
    de vuelta a nuestra app. Es de UN solo uso.
    
    Recibe:
    - codigo_autorizacion: el codigo que MeLi nos dio
    
    Retorna:
    - dict con access_token, refresh_token, etc.
    - None si fallo
    """
    url = "https://api.mercadolibre.com/oauth/token"

    datos = {
        "grant_type": "authorization_code",
        "client_id": config.APP_ID,
        "client_secret": config.APP_SECRET,
        "code": codigo_autorizacion,
        "redirect_uri": config.MELI_REDIRECT_URI,
    }

    try:
        respuesta = requests.post(url, json=datos, timeout=10)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.RequestException as e:
        print(f"Error obteniendo token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Detalle: {e.response.text}")
        return None


def refrescar_token(refresh_token):
    """
    Renueva un token vencido usando el refresh_token.
    Los tokens de MeLi duran 6 horas. Despues hay que renovar.
    
    Retorna: dict con nuevo access_token
    """
    url = "https://api.mercadolibre.com/oauth/token"

    datos = {
        "grant_type": "refresh_token",
        "client_id": config.APP_ID,
        "client_secret": config.APP_SECRET,
        "refresh_token": refresh_token,
    }

    try:
        respuesta = requests.post(url, json=datos, timeout=10)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.RequestException as e:
        print(f"Error refrescando token: {e}")
        return None
