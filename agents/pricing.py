# ============================================================
# agents/pricing.py — Pricing Node (El analista de mercado)
# ============================================================
# Este agente hace DOS cosas:
# 1. Busca productos similares en MercadoLibre (API publica)
# 2. Analiza los precios y da recomendaciones
#
# La busqueda en MeLi es PUBLICA (no necesita autenticacion)
# Solo la publicacion necesita login.
# ============================================================

import requests
import json
import anthropic
import config


def obtener_token_app():
    """
    Obtiene un token de aplicacion (sin usuario) para buscar en MeLi.
    Esto es diferente al OAuth del usuario — es solo para leer datos.
    """
    try:
        respuesta = requests.post(
            "https://api.mercadolibre.com/oauth/token",
            json={
                "grant_type": "client_credentials",
                "client_id": config.APP_ID,
                "client_secret": config.APP_SECRET,
            },
            timeout=10
        )
        if respuesta.status_code == 200:
            return respuesta.json().get("access_token")
    except requests.RequestException:
        pass
    return None


def buscar_productos_similares(nombre_producto, categoria="", limite=20):
    """
    Busca productos similares en MercadoLibre.
    Intenta con token de app, si falla intenta sin token.
    """
    url = f"https://api.mercadolibre.com/sites/{config.MELI_SITE_ID}/search"

    parametros = {
        "q": nombre_producto,
        "limit": limite,
        "sort": "relevance"
    }

    headers = {
        "User-Agent": "Listify/1.0",
        "Accept": "application/json",
    }

    # Intentar con token de app
    token = obtener_token_app()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        respuesta = requests.get(url, params=parametros, headers=headers, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()

        productos = []
        for item in datos.get("results", []):
            productos.append({
                "titulo": item.get("title", ""),
                "precio": item.get("price", 0),
                "moneda": item.get("currency_id", "ARS"),
                "estado": item.get("condition", ""),
                "vendidos": item.get("sold_quantity", 0),
                "envio_gratis": item.get("shipping", {}).get("free_shipping", False),
                "permalink": item.get("permalink", ""),
            })

        return productos

    except requests.RequestException as e:
        print(f"Error buscando en MeLi: {e}")
        return []


def estimar_precios_con_ia(atributos):
    """
    PLAN B: Si MeLi API no responde, le pedimos a Claude
    que estime precios basandose en su conocimiento del
    mercado argentino. No es tan preciso como datos reales
    pero es MUCHO mejor que mostrar ceros.
    """
    info = json.dumps(atributos, ensure_ascii=False, indent=2)

    prompt = f"""Sos un experto en ecommerce en Argentina, especificamente en MercadoLibre.

Necesito que estimes los precios de mercado para este producto en PESOS ARGENTINOS (ARS):

{info}

Basandote en tu conocimiento del mercado argentino actual, estima:
- precio_minimo: el precio mas bajo al que se vende algo asi
- precio_maximo: el precio mas alto razonable
- precio_promedio: el precio tipico
- precio_mediana: el precio donde esta la mayoria de ventas
- precio_sugerido: el precio al que VOS lo publicarias para vender rapido

Responde UNICAMENTE con JSON valido (sin texto, sin markdown):
{{
    "precio_minimo": 0,
    "precio_maximo": 0,
    "precio_promedio": 0,
    "precio_mediana": 0,
    "precio_sugerido": 0,
    "fuente": "estimacion IA",
    "nota": "breve justificacion de 1 linea"
}}

Solo numeros enteros, sin decimales, sin simbolo $."""

    try:
        cliente = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        mensaje = cliente.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        respuesta = mensaje.content[0].text.strip()
        if respuesta.startswith("```"):
            respuesta = respuesta.split("\n", 1)[1]
        if respuesta.endswith("```"):
            respuesta = respuesta.rsplit("```", 1)[0]

        return json.loads(respuesta.strip())

    except Exception as e:
        print(f"Error estimando precios con IA: {e}")
        return None


def calcular_estadisticas(productos):
    """
    Calcula estadisticas basicas de los precios encontrados.
    Esto es matematica simple, no necesita IA.
    
    Retorna: dict con min, max, promedio, mediana
    """
    if not productos:
        return {
            "precio_minimo": 0,
            "precio_maximo": 0,
            "precio_promedio": 0,
            "precio_mediana": 0,
            "cantidad_encontrados": 0
        }

    precios = [p["precio"] for p in productos if p["precio"] > 0]

    if not precios:
        return {
            "precio_minimo": 0,
            "precio_maximo": 0,
            "precio_promedio": 0,
            "precio_mediana": 0,
            "cantidad_encontrados": 0
        }

    precios.sort()
    n = len(precios)

    # La mediana es el valor del medio cuando ordenas de menor a mayor
    if n % 2 == 0:
        mediana = (precios[n // 2 - 1] + precios[n // 2]) / 2
    else:
        mediana = precios[n // 2]

    return {
        "precio_minimo": min(precios),
        "precio_maximo": max(precios),
        "precio_promedio": round(sum(precios) / n, 2),
        "precio_mediana": round(mediana, 2),
        "cantidad_encontrados": n
    }


def analizar_precios(atributos):
    """
    FUNCION PRINCIPAL del Pricing Node.
    
    Recibe:
    - atributos: diccionario del Vision Node
    
    Retorna:
    - Diccionario con estadisticas y precio sugerido
    """

    # 1. Armar lista de busquedas inteligentes
    # Usamos las sugerencias del Vision Node si existen
    busquedas = atributos.get("busqueda_marketplace", [])
    
    # Si Vision no dio sugerencias, armamos busquedas nosotros
    if not busquedas:
        nombre = atributos.get("nombre_producto", "producto")
        marca = atributos.get("marca", "")
        categoria = atributos.get("subcategoria", "")
        busquedas = [
            f"{nombre} {marca}".strip(),
            nombre,
            f"{nombre} {categoria}".strip(),
        ]

    # 2. Probar cada busqueda hasta encontrar resultados con precios
    productos_encontrados = []
    query_usada = ""

    for query in busquedas:
        if not query:
            continue
        productos_encontrados = buscar_productos_similares(query)
        stats_temp = calcular_estadisticas(productos_encontrados)
        
        # Si encontramos productos con precios reales, usamos estos
        if stats_temp["cantidad_encontrados"] > 0 and stats_temp["precio_promedio"] > 0:
            query_usada = query
            print(f"   📊 Pricing: encontro {stats_temp['cantidad_encontrados']} resultados con '{query}'")
            break
    
    if not query_usada:
        query_usada = busquedas[0] if busquedas else "producto"
        print(f"   ⚠️ Pricing: MeLi API no disponible, usando estimacion IA...")

        # PLAN B: Estimar precios con Claude
        estimacion = estimar_precios_con_ia(atributos)
        if estimacion:
            print(f"   📊 Pricing (IA): estimado ${estimacion.get('precio_sugerido', '?')}")
            resultado = {
                "precio_sugerido": estimacion.get("precio_sugerido"),
                "precio_minimo": estimacion.get("precio_minimo", 0),
                "precio_maximo": estimacion.get("precio_maximo", 0),
                "precio_promedio": estimacion.get("precio_promedio", 0),
                "precio_mediana": estimacion.get("precio_mediana", 0),
                "productos_analizados": 0,
                "query_busqueda": query_usada,
                "fuente": estimacion.get("fuente", "estimacion IA"),
                "nota": estimacion.get("nota", ""),
                "datos_mercado": {
                    "fuente": "estimacion IA",
                    "nota": estimacion.get("nota", "")
                }
            }
            return resultado

    # 3. Calcular estadisticas
    stats = calcular_estadisticas(productos_encontrados)

    # 3. Si encontramos productos, pedirle a Claude que sugiera un precio
    if stats["cantidad_encontrados"] > 0:
        precio_sugerido = sugerir_precio_con_ia(atributos, stats, productos_encontrados[:5])
    else:
        precio_sugerido = None

    # 4. Armar el resultado final
    resultado = {
        "precio_sugerido": precio_sugerido,
        "precio_minimo": stats["precio_minimo"],
        "precio_maximo": stats["precio_maximo"],
        "precio_promedio": stats["precio_promedio"],
        "precio_mediana": stats["precio_mediana"],
        "productos_analizados": stats["cantidad_encontrados"],
        "query_busqueda": query_usada,
        "datos_mercado": {
            "top_5_resultados": productos_encontrados[:5]
        }
    }

    return resultado


def sugerir_precio_con_ia(atributos, stats, top_productos):
    """
    Usa Claude para analizar los datos de mercado y sugerir
    el MEJOR precio para maximizar ventas.
    """
    info = json.dumps({
        "producto": atributos,
        "estadisticas": stats,
        "competencia": top_productos
    }, ensure_ascii=False, indent=2)

    prompt = f"""Sos un experto en pricing para ecommerce en Argentina (MercadoLibre).

Analiza estos datos de mercado y sugeri UN precio optimo.

DATOS:
{info}

Considera:
- El estado del producto (nuevo vs usado)
- La competencia directa
- Que el precio sea competitivo pero rentable
- Los productos mas vendidos suelen estar cerca de la mediana

Responde UNICAMENTE con un numero (el precio sugerido en ARS).
Sin texto, sin simbolo $, sin puntos de miles. Solo el numero.
Ejemplo: 25500"""

    try:
        cliente = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        mensaje = cliente.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )

        precio_texto = mensaje.content[0].text.strip()
        # Limpiar cualquier caracter no numerico
        precio_limpio = "".join(c for c in precio_texto if c.isdigit() or c == ".")
        return float(precio_limpio) if precio_limpio else stats["precio_mediana"]

    except Exception:
        # Si falla la IA, usamos la mediana como precio sugerido
        return stats["precio_mediana"]


if __name__ == "__main__":
    print("Pricing Node listo.")
    print("Para probar, usa: analizar_precios(atributos_dict)")