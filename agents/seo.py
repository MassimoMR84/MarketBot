# ============================================================
# agents/seo.py — SEO Node (El posicionador)
# ============================================================
# Este agente toma los atributos del producto y genera:
# - Titulo optimizado para MercadoLibre (max 60 caracteres)
# - Descripcion con keywords estrategicas
# - Lista de keywords relevantes
#
# MercadoLibre tiene reglas especificas para titulos:
# - Maximo 60 caracteres
# - Formato: Producto + Marca + Modelo + Caracteristica clave
# - No usar signos de exclamacion, mayusculas completas, ni emojis
# ============================================================

import anthropic
import json
import config


def generar_seo(atributos):
    """
    FUNCION PRINCIPAL del SEO Node.
    
    Recibe:
    - atributos: diccionario generado por el Vision Node
      (nombre_producto, categoria, marca, color, etc.)
    
    Retorna:
    - Diccionario con titulo, descripcion y keywords
    """

    # Convertimos los atributos a texto para que Claude los entienda
    info_producto = json.dumps(atributos, ensure_ascii=False, indent=2)

    prompt = f"""Sos un experto en SEO para MercadoLibre Argentina.
Te doy los atributos de un producto y necesito que generes contenido optimizado para posicionamiento.

ATRIBUTOS DEL PRODUCTO:
{info_producto}

REGLAS DE MERCADOLIBRE PARA TITULOS:
- Maximo 60 caracteres (OBLIGATORIO, no te pases)
- Formato ideal: [Producto] [Marca] [Modelo] [Caracteristica clave]
- NO usar signos de exclamacion (!)
- NO usar todo en mayusculas
- NO usar palabras como "oferta", "increible", "unico"
- NO usar emojis
- SI usar palabras clave que la gente busca

REGLAS PARA DESCRIPCION SEO:
- Entre 150 y 300 palabras
- Incluir keywords naturalmente (sin forzarlas)
- Estructura: parrafo de apertura + caracteristicas + beneficios
- Pensar en que buscaria un comprador en MercadoLibre

Responde UNICAMENTE con un JSON valido (sin texto adicional, sin markdown):
{{
    "titulo": "titulo optimizado (max 60 caracteres)",
    "descripcion": "descripcion SEO completa",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "titulo_caracteres": 45,
    "score_seo": 8.5
}}

El campo "titulo_caracteres" es la cantidad de caracteres del titulo.
El campo "score_seo" es tu estimacion del 1 al 10 de que tan bien posicionaria."""

    # Llamar a Claude
    cliente = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    mensaje = cliente.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    # Parsear respuesta
    respuesta_texto = mensaje.content[0].text
    respuesta_limpia = respuesta_texto.strip()
    if respuesta_limpia.startswith("```"):
        respuesta_limpia = respuesta_limpia.split("\n", 1)[1]
    if respuesta_limpia.endswith("```"):
        respuesta_limpia = respuesta_limpia.rsplit("```", 1)[0]
    respuesta_limpia = respuesta_limpia.strip()

    try:
        seo_data = json.loads(respuesta_limpia)
    except json.JSONDecodeError:
        seo_data = {
            "titulo": atributos.get("nombre_producto", "Producto"),
            "descripcion": "Descripcion no disponible",
            "keywords": [],
            "score_seo": 0,
            "error": "No se pudo generar SEO"
        }

    # Validar que el titulo no supere 60 caracteres
    if len(seo_data.get("titulo", "")) > 60:
        seo_data["titulo"] = seo_data["titulo"][:57] + "..."
        seo_data["titulo_truncado"] = True

    return seo_data


if __name__ == "__main__":
    print("SEO Node listo.")
    print("Para probar, usa: generar_seo(atributos_dict)")
