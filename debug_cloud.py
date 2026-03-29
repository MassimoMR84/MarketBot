"""
Corré esto con: streamlit run debug_cloud.py
O: python debug_cloud.py
Muestra qué ve el scraper cuando busca en MercadoLibre.
"""

import requests
from bs4 import BeautifulSoup
import re

query = "mouse logitech pebble"
query_url = query.replace(" ", "-")
url = f"https://listado.mercadolibre.com.ar/{query_url}"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.5",
}

print(f"URL: {url}")

try:
    resp = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"HTML length: {len(resp.text)}")
    
    # Verificar si hay redirect o captcha
    if "captcha" in resp.text.lower():
        print("⚠️ CAPTCHA detectado — MeLi está bloqueando")
    elif "robot" in resp.text.lower()[:2000]:
        print("⚠️ Detección de bot — MeLi está bloqueando")
    elif len(resp.text) < 5000:
        print("⚠️ HTML muy corto — probablemente redirect")
        print(f"Primeros 500 chars: {resp.text[:500]}")
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Buscar cards
    cards = soup.find_all(
        "div",
        class_=lambda c: c and "poly-card" in c and "poly-card__content" not in c
    )
    print(f"Cards encontradas: {len(cards)}")
    
    # Buscar precios
    precios_divs = soup.find_all("div", class_="poly-price__current")
    print(f"Divs de precio: {len(precios_divs)}")
    
    # Extraer productos
    productos = []
    for card in cards:
        titulo_elem = card.find("a", class_="poly-component__title")
        titulo = titulo_elem.get_text(strip=True) if titulo_elem else ""
        
        precio = None
        precio_div = card.find("div", class_="poly-price__current")
        if precio_div:
            amount_span = precio_div.find("span", attrs={"aria-label": True})
            if amount_span:
                aria = amount_span.get("aria-label", "")
                nums = re.findall(r"(\d+)", aria)
                if nums:
                    precio = int(nums[0])
        
        if titulo and precio:
            productos.append({"titulo": titulo, "precio": precio})
    
    print(f"\nProductos extraidos: {len(productos)}")
    for p in productos[:10]:
        print(f"  ${p['precio']:>10,}  |  {p['titulo'][:60]}")

    if not productos:
        print("\n--- DEBUG: texto visible (sin scripts) ---")
        for s in soup(["script", "style"]):
            s.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        print(f"Lineas visibles: {len(lines)}")
        for line in lines[:30]:
            print(f"  [{line[:100]}]")

except Exception as e:
    print(f"ERROR: {e}")