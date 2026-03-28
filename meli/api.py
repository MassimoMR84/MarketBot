# ============================================================
# meli/api.py — Publicar productos en MercadoLibre
# ============================================================
# Este archivo se encarga de:
# 1. Subir la imagen del producto a MeLi
# 2. Crear la publicacion con todos los datos
#
# Necesita un access_token valido (viene de auth.py)
# ============================================================

import requests
import json
import config


def subir_imagen(access_token, imagen_path):
    """
    Sube una imagen a los servidores de MercadoLibre.
    MeLi no acepta links externos, hay que subir la foto
    a SUS servidores primero.
    
    Retorna: el ID de la imagen en MeLi (ej: "MLA-123456-1")
    """
    url = "https://api.mercadolibre.com/pictures/items/upload"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        with open(imagen_path, "rb") as imagen:
            archivos = {"file": (imagen_path, imagen, "image/jpeg")}
            respuesta = requests.post(
                url, headers=headers, files=archivos, timeout=30
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
            return datos.get("id")
    except requests.RequestException as e:
        print(f"Error subiendo imagen: {e}")
        return None


def publicar_producto(access_token, producto, imagen_id=None):
    """
    FUNCION PRINCIPAL — Crea una publicacion en MercadoLibre.
    
    Recibe:
    - access_token: token de autorizacion
    - producto: dict con los datos del producto (de nuestra DB)
    - imagen_id: ID de la imagen ya subida a MeLi (opcional)
    
    Retorna:
    - dict con la respuesta de MeLi (incluye el ID de la publicacion)
    - None si fallo
    """
    url = "https://api.mercadolibre.com/items"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Armar el cuerpo de la publicacion
    # Estos son los campos que MeLi necesita como MINIMO
    publicacion = {
        "title": producto.get("titulo", "Producto"),
        "category_id": "MLA1055",  # Categoria generica - en produccion habria que mapear
        "price": producto.get("precio_sugerido", 0),
        "currency_id": "ARS",
        "available_quantity": 1,
        "buying_mode": "buy_it_now",
        "condition": "new",  # new | used
        "listing_type_id": "gold_special",  # Tipo de publicacion
        "description": {
            "plain_text": producto.get("descripcion_marketing", "")
        },
        "sale_terms": [],
        "pictures": [],
    }

    # Agregar imagen si la tenemos
    if imagen_id:
        publicacion["pictures"] = [{"id": imagen_id}]

    # Mapear el estado del producto
    try:
        atributos = json.loads(producto.get("atributos", "{}"))
        estado = atributos.get("estado", "Nuevo")
        if "usado" in estado.lower():
            publicacion["condition"] = "used"
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        respuesta = requests.post(
            url, headers=headers, json=publicacion, timeout=30
        )
        datos = respuesta.json()

        if respuesta.status_code in (200, 201):
            print(f"✅ Publicado exitosamente! ID: {datos.get('id')}")
            print(f"   Link: {datos.get('permalink', 'N/A')}")
            return datos
        else:
            print(f"❌ Error publicando: {datos}")
            return datos

    except requests.RequestException as e:
        print(f"Error de conexion: {e}")
        return None


def obtener_categorias_sugeridas(nombre_producto):
    """
    Le pregunta a MeLi que categoria sugiere para un producto.
    Esto es GRATIS y no necesita autenticacion.
    Util para mapear la categoria correcta.
    """
    url = f"https://api.mercadolibre.com/sites/{config.MELI_SITE_ID}/domain_discovery/search"
    
    try:
        respuesta = requests.get(
            url, params={"q": nombre_producto}, timeout=10
        )
        respuesta.raise_for_status()
        categorias = respuesta.json()
        if categorias:
            return categorias[0].get("category_id", "MLA1055")
        return "MLA1055"
    except requests.RequestException:
        return "MLA1055"  # Categoria generica como fallback
