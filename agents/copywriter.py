# ============================================================
# agents/copywriter.py — Copy Node (El marketinero)
# ============================================================
# Este agente genera:
# - Descripcion de marketing atractiva y persuasiva
# - Call to Action (CTA) para cerrar la venta
# Piensen en el como el redactor publicitario del equipo.
# ============================================================

import anthropic
import json
import config


def generar_copy(atributos, seo_data=None):
    """
    FUNCION PRINCIPAL del Copy Node.
    
    Recibe:
    - atributos: diccionario del Vision Node
    - seo_data: diccionario del SEO Node (opcional, para coherencia)
    
    Retorna:
    - Diccionario con descripcion marketing y CTA
    """

    info_producto = json.dumps(atributos, ensure_ascii=False, indent=2)
    
    # Si tenemos datos SEO, los usamos para que todo sea coherente
    contexto_seo = ""
    if seo_data:
        contexto_seo = f"""
DATOS SEO YA GENERADOS (mantene coherencia con estos):
- Titulo: {seo_data.get('titulo', '')}
- Keywords: {json.dumps(seo_data.get('keywords', []), ensure_ascii=False)}
"""

    prompt = f"""Sos un copywriter experto en ecommerce para MercadoLibre Argentina.
Escribis descripciones que VENDEN. Tu tono es profesional pero cercano.

ATRIBUTOS DEL PRODUCTO:
{info_producto}
{contexto_seo}

Genera una descripcion de venta y un CTA siguiendo estas reglas:

PARA LA DESCRIPCION:
- Entre 200 y 400 palabras
- Arrancar con un gancho que capture atencion
- Destacar beneficios, no solo caracteristicas
- Usar lenguaje argentino natural (vos, tuteo)
- Incluir especificaciones tecnicas si aplica
- Cerrar con urgencia sutil (sin ser spam)
- Usar saltos de linea para que sea facil de leer
- NO usar emojis
- NO mentir ni exagerar

PARA EL CTA:
- Una frase corta y directa que invite a comprar
- Ejemplos: "Llevalo hoy con envio gratis", "Dale, sumalo a tu carrito"
- Maximo 10 palabras

Responde UNICAMENTE con un JSON valido (sin texto adicional, sin markdown):
{{
    "descripcion": "la descripcion completa de marketing",
    "cta": "el call to action",
    "tono": "profesional | casual | premium | juvenil",
    "gancho_apertura": "la primera frase gancho usada"
}}"""

    # Llamar a Claude
    cliente = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    mensaje = cliente.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1500,
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
        copy_data = json.loads(respuesta_limpia)
    except json.JSONDecodeError:
        copy_data = {
            "descripcion": "Descripcion no disponible",
            "cta": "Compralo ahora",
            "error": "No se pudo generar el copy"
        }

    return copy_data


if __name__ == "__main__":
    print("Copy Node listo.")
    print("Para probar, usa: generar_copy(atributos_dict)")
