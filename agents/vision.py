# ============================================================
# agents/vision.py — Vision Node (Los ojos de la IA)
# ============================================================
# Este agente recibe una foto y deduce todos los atributos
# del producto: que es, color, marca, estado, categoria, etc.
# Usa Claude Vision API (puede "ver" imagenes).
# ============================================================

import anthropic
import base64
import json
import config


def codificar_imagen(imagen_bytes):
    """
    Convierte la imagen a base64.
    ¿Que es base64? Es una forma de convertir una imagen
    en texto para poder enviarla por internet.
    Piensen en ello como "traducir una foto a un idioma
    que la API puede leer".
    """
    return base64.standard_b64encode(imagen_bytes).decode("utf-8")


def detectar_tipo_imagen(imagen_bytes):
    """
    Detecta si la imagen es JPG, PNG, GIF o WEBP
    mirando los primeros bytes del archivo.
    Es como leer la "firma" del archivo.
    """
    if imagen_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    elif imagen_bytes[:2] == b'\xff\xd8':
        return "image/jpeg"
    elif imagen_bytes[:4] == b'GIF8':
        return "image/gif"
    elif imagen_bytes[:4] == b'RIFF' and imagen_bytes[8:12] == b'WEBP':
        return "image/webp"
    else:
        return "image/jpeg"  # Por defecto asumimos JPG


def analizar_producto(imagen_bytes, contexto_usuario=""):
    """
    FUNCION PRINCIPAL del Vision Node.
    
    Recibe:
    - imagen_bytes: UNA foto (bytes) o LISTA de fotos ([bytes, bytes, ...])
    - contexto_usuario: texto opcional que escribio el usuario
      (ej: "es una campera de mi marca, talle M")
    
    Retorna:
    - Un diccionario con todos los atributos detectados
    """

    # 1. Preparar imagen(es) para enviarlas a Claude
    # Soporta una imagen sola (backwards compatible) o multiples
    if isinstance(imagen_bytes, list):
        lista_imagenes = imagen_bytes
    else:
        lista_imagenes = [imagen_bytes]

    # Construir los bloques de imagen para el mensaje
    bloques_imagenes = []
    for img_bytes in lista_imagenes:
        img_base64 = codificar_imagen(img_bytes)
        tipo_img = detectar_tipo_imagen(img_bytes)
        bloques_imagenes.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": tipo_img,
                "data": img_base64,
            },
        })

    # 2. Construir el prompt (la instruccion para Claude)
    #    Este prompt es CLAVE. Le decimos exactamente que queremos.
    cantidad_fotos = len(lista_imagenes)
    intro_fotos = (
        "Analiza la siguiente imagen de un producto."
        if cantidad_fotos == 1
        else f"Analiza las siguientes {cantidad_fotos} imagenes del MISMO producto. "
             f"Usa TODAS las fotos para obtener la mayor cantidad de detalles posibles "
             f"(frente, dorso, etiquetas, detalles, estado, etc)."
    )

    prompt = f"""Sos un experto en ecommerce y analisis de productos.

{intro_fotos}

"""

    prompt += """PRIMERO evalua si la imagen muestra un PRODUCTO VENDIBLE (algo que se pueda vender en un marketplace como MercadoLibre). 
NO son productos vendibles: selfies, paisajes, capturas de pantalla, memes, mascotas, fotos borrosas irreconocibles, comida preparada casera.
SI son productos vendibles: cualquier objeto fisico (electronica, ropa, muebles, juguetes, alimentos envasados, bebidas comerciales, etc).

Si la imagen NO es un producto vendible, responde con este JSON:
{
    "es_producto": false,
    "nombre_producto": "No identificado",
    "razon": "explicacion breve de por que no es vendible",
    "confianza": 0.0
}

Si la imagen SI es un producto vendible, responde con este JSON:
{
    "es_producto": true,
    "nombre_producto": "nombre descriptivo del producto",
    "categoria": "categoria principal (ej: Electronica, Ropa, Hogar, etc)",
    "subcategoria": "subcategoria mas especifica",
    "marca": "marca si es visible, sino 'Genérica'",
    "modelo": "modelo si es visible, sino null",
    "color": "color principal",
    "colores_secundarios": ["otros colores si los hay"],
    "material": "material principal si se puede deducir",
    "estado": "Nuevo | Usado - Como nuevo | Usado - Buen estado | Usado - Aceptable",
    "condicion_detalle": "descripcion breve del estado fisico",
    "tamano_aproximado": "pequeño | mediano | grande",
    "caracteristicas_visibles": ["lista de caracteristicas que se ven en la foto"],
    "posibles_usos": ["para que sirve este producto"],
    "publico_objetivo": "a quien le serviria este producto",
    "busqueda_marketplace": ["3 a 5 formas diferentes de buscar este producto en MercadoLibre, de mas especifica a mas generica"],
    "confianza": 0.85
}

IMPORTANTE sobre "busqueda_marketplace": son las palabras que usaria un comprador para buscar este producto.
Ejemplo para una Red Bull: ["Red Bull 250ml", "Red Bull energia", "bebida energizante Red Bull", "bebida energizante", "energizante lata"]
Ejemplo para un iPhone 13: ["iPhone 13 128gb", "iPhone 13 Apple", "celular iPhone 13", "celular Apple", "smartphone Apple"]

Responde UNICAMENTE con JSON valido (sin texto adicional, sin markdown).
Si algo no se puede determinar con certeza, ponelo como null.
Se preciso y profesional."""

    # Si el usuario agrego contexto, lo incorporamos
    if contexto_usuario:
        prompt += f"\n\nContexto adicional del vendedor: {contexto_usuario}"

    # 3. Llamar a la API de Claude con la(s) imagen(es)
    cliente = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Armar contenido: todas las imagenes + el prompt de texto
    contenido = bloques_imagenes + [{"type": "text", "text": prompt}]

    mensaje = cliente.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": contenido,
            }
        ],
    )

    # 4. Extraer y parsear la respuesta
    respuesta_texto = mensaje.content[0].text

    # Limpiar por si Claude agrega ```json ... ```
    respuesta_limpia = respuesta_texto.strip()
    if respuesta_limpia.startswith("```"):
        respuesta_limpia = respuesta_limpia.split("\n", 1)[1]
    if respuesta_limpia.endswith("```"):
        respuesta_limpia = respuesta_limpia.rsplit("```", 1)[0]
    respuesta_limpia = respuesta_limpia.strip()

    try:
        atributos = json.loads(respuesta_limpia)
    except json.JSONDecodeError:
        # Si Claude no devolvio JSON valido, creamos uno basico
        atributos = {
            "nombre_producto": "Producto no identificado",
            "categoria": "General",
            "error": "No se pudo parsear la respuesta de la IA",
            "respuesta_cruda": respuesta_texto,
            "confianza": 0.0
        }

    return atributos


# ============================================================
# Test rapido: si ejecutan este archivo solo, prueba con
# una imagen de ejemplo
# ============================================================
if __name__ == "__main__":
    print("Vision Node listo.")
    print("Para probar, usa: analizar_producto(imagen_bytes)")
    print("Se necesita la API key de Anthropic en config.py")