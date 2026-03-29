# ============================================================
# agents/pricing.py — Pricing Node (El analista de mercado)
# ============================================================
# Este agente busca precios REALES scrapeando la web publica
# de marketplaces. No usa APIs privadas ni tokens.
#
# Flujo: Scraping web → error honesto si falla.
# No inventamos precios. Si no hay datos, lo decimos.
#
# Arquitectura multi-plataforma: cada marketplace tiene su
# funcion de scraping. Para agregar uno nuevo, solo hay que
# crear una funcion buscar_PLATAFORMA() y agregarla al dict.
# ============================================================

import requests
import json
import re
from bs4 import BeautifulSoup
import config

# ============================================================
# CONFIGURACION POR PLATAFORMA / PAIS
# ============================================================

SITE_CONFIG = {
    "MLA": {
        "url_busqueda": "https://listado.mercadolibre.com.ar/{}",
        "moneda": "ARS",
        "pais": "Argentina",
        "plataforma": "MercadoLibre",
    },
    "MLB": {
        "url_busqueda": "https://lista.mercadolivre.com.br/{}",
        "moneda": "BRL",
        "pais": "Brasil",
        "plataforma": "MercadoLivre",
    },
    "MLC": {
        "url_busqueda": "https://listado.mercadolibre.cl/{}",
        "moneda": "CLP",
        "pais": "Chile",
        "plataforma": "MercadoLibre",
    },
    "MLM": {
        "url_busqueda": "https://listado.mercadolibre.com.mx/{}",
        "moneda": "MXN",
        "pais": "Mexico",
        "plataforma": "MercadoLibre",
    },
    "MCO": {
        "url_busqueda": "https://listado.mercadolibre.com.co/{}",
        "moneda": "COP",
        "pais": "Colombia",
        "plataforma": "MercadoLibre",
    },
    "MLU": {
        "url_busqueda": "https://listado.mercadolibre.com.uy/{}",
        "moneda": "UYU",
        "pais": "Uruguay",
        "plataforma": "MercadoLibre",
    },
    "MPE": {
        "url_busqueda": "https://listado.mercadolibre.com.pe/{}",
        "moneda": "PEN",
        "pais": "Peru",
        "plataforma": "MercadoLibre",
    },
}


def obtener_config_sitio():
    """Obtiene la config del sitio segun MELI_SITE_ID."""
    site_id = getattr(config, "MELI_SITE_ID", "MLA")
    return SITE_CONFIG.get(site_id, SITE_CONFIG["MLA"])


# ============================================================
# SCRAPING DE MERCADOLIBRE WEB
# ============================================================

def buscar_mercadolibre(query, max_resultados=48):
    """
    Scrapea la web publica de MercadoLibre.
    No usa API, no necesita token. Simula un usuario buscando.
    
    Estructura del HTML de MeLi (verificada marzo 2026):
    - div.poly-card = cada producto
    - a.poly-component__title = titulo del producto
    - div.poly-price__current > span[aria-label] = precio
      El aria-label tiene formato: "Ahora: 9596 pesos argentinos"
    """
    site_config = obtener_config_sitio()

    # MeLi usa guiones en la URL para espacios
    query_url = query.replace(" ", "-")
    url = site_config["url_busqueda"].format(query_url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    try:
        respuesta = requests.get(url, headers=headers, timeout=15)
        respuesta.raise_for_status()

        soup = BeautifulSoup(respuesta.text, "html.parser")
        productos = []

        # Buscar todas las cards de producto
        cards = soup.find_all(
            "div",
            class_=lambda c: c and "poly-card" in c and "poly-card__content" not in c
        )

        for card in cards:
            # --- TITULO ---
            titulo = ""
            titulo_elem = card.find("a", class_="poly-component__title")
            if titulo_elem:
                titulo = titulo_elem.get_text(strip=True)

            # --- PRECIO (via aria-label, lo mas confiable) ---
            precio = None
            precio_div = card.find("div", class_="poly-price__current")
            if precio_div:
                amount_span = precio_div.find("span", attrs={"aria-label": True})
                if amount_span:
                    aria = amount_span.get("aria-label", "")
                    nums = re.findall(r"(\d+)", aria)
                    if nums:
                        precio = int(nums[0])

            if titulo and precio and precio > 0:
                productos.append({
                    "titulo": titulo,
                    "precio": precio,
                    "moneda": site_config["moneda"],
                    "fuente": site_config["plataforma"],
                })

            if len(productos) >= max_resultados:
                break

        print(f"   🔍 {site_config['plataforma']}: {len(productos)} resultados para '{query}'")
        return productos

    except requests.RequestException as e:
        print(f"   ❌ Error buscando en {site_config['plataforma']}: {e}")
        return []
    except Exception as e:
        print(f"   ❌ Error parseando {site_config['plataforma']}: {e}")
        return []


# ============================================================
# ESTADISTICAS Y PRECIO SUGERIDO
# ============================================================

def calcular_estadisticas(productos):
    """
    Calcula estadisticas basicas de los precios encontrados.
    Filtra outliers para dar datos mas representativos.
    """
    if not productos:
        return {
            "precio_minimo": 0,
            "precio_maximo": 0,
            "precio_promedio": 0,
            "precio_mediana": 0,
            "cantidad_encontrados": 0
        }

    precios = [p["precio"] for p in productos if p.get("precio", 0) > 0]

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

    # Filtrar outliers: sacar el 10% mas extremo de cada punta
    if n >= 5:
        corte = max(1, n // 10)
        precios_filtrados = precios[corte:-corte]
        if precios_filtrados:
            precios = precios_filtrados

    n = len(precios)

    # Mediana
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


def sugerir_precio(stats):
    """
    Sugiere un precio competitivo basado en estadisticas.
    5% debajo de la mediana para ser competitivo.
    Sin IA — formula simple y predecible.
    """
    if stats["cantidad_encontrados"] == 0 or stats["precio_mediana"] == 0:
        return None

    sugerido = round(stats["precio_mediana"] * 0.95, -1)

    if sugerido < stats["precio_minimo"]:
        sugerido = stats["precio_minimo"]

    return sugerido


# ============================================================
# FUNCION PRINCIPAL
# ============================================================

def analizar_precios(atributos):
    """
    FUNCION PRINCIPAL del Pricing Node.
    
    Recibe:
    - atributos: diccionario del Vision Node
    
    Retorna:
    - Diccionario con estadisticas y precio sugerido
      (compatible con app.py y orchestrator.py)
    """

    # 1. Armar lista de busquedas inteligentes
    busquedas = atributos.get("busqueda_marketplace", [])

    if not busquedas:
        nombre = atributos.get("nombre_producto", "producto")
        marca = atributos.get("marca", "")
        categoria = atributos.get("subcategoria", "")
        busquedas = [
            f"{nombre} {marca}".strip(),
            nombre,
            f"{nombre} {categoria}".strip(),
        ]

    # 2. Probar cada busqueda hasta encontrar resultados
    productos_encontrados = []
    query_usada = ""

    for query in busquedas:
        if not query:
            continue
        productos_encontrados = buscar_mercadolibre(query)
        stats_temp = calcular_estadisticas(productos_encontrados)

        if stats_temp["cantidad_encontrados"] > 0 and stats_temp["precio_promedio"] > 0:
            query_usada = query
            print(f"   📊 Pricing: {stats_temp['cantidad_encontrados']} precios reales con '{query}'")
            break

    # 3. Si no encontramos nada, error honesto
    if not query_usada:
        print("   ⚠️ Pricing: no se pudieron obtener precios reales")
        return {
            "precio_sugerido": None,
            "precio_minimo": 0,
            "precio_maximo": 0,
            "precio_promedio": 0,
            "precio_mediana": 0,
            "productos_analizados": 0,
            "query_busqueda": busquedas[0] if busquedas else "producto",
            "fuente": "sin datos",
            "nota": "No se pudieron obtener precios. Ingresa un precio manualmente.",
            "datos_mercado": {
                "fuente": "sin datos",
                "nota": "No se pudieron obtener precios reales."
            }
        }

    # 4. Calcular estadisticas
    stats = calcular_estadisticas(productos_encontrados)

    # 5. Sugerir precio (sin IA)
    precio_sugerido = sugerir_precio(stats)

    # 6. Resultado final
    site_config = obtener_config_sitio()
    resultado = {
        "precio_sugerido": precio_sugerido,
        "precio_minimo": stats["precio_minimo"],
        "precio_maximo": stats["precio_maximo"],
        "precio_promedio": stats["precio_promedio"],
        "precio_mediana": stats["precio_mediana"],
        "productos_analizados": stats["cantidad_encontrados"],
        "query_busqueda": query_usada,
        "fuente": site_config["plataforma"],
        "moneda": site_config["moneda"],
        "pais": site_config["pais"],
        "datos_mercado": {
            "fuente": site_config["plataforma"],
            "top_5_resultados": productos_encontrados[:5]
        }
    }

    return resultado


if __name__ == "__main__":
    site = obtener_config_sitio()
    print(f"Pricing Node listo — {site['plataforma']} ({site['pais']})")
    print("Para probar, usa: analizar_precios(atributos_dict)")