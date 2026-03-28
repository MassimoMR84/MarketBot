# 🚀 Listify — Publicá con IA en segundos

**Listify** es un orquestador de agentes de IA que transforma una simple foto de un producto en una publicación profesional de ecommerce lista para vender. Subís una foto, la IA genera todo, vos revisás y publicás. Así de simple.

> 🏆 Proyecto desarrollado en hackathon — MVP funcional en 28 horas.

---

## 🎯 El problema

Millones de personas en Latinoamérica quieren vender online pero se quedan paralizadas en el proceso de publicación: no saben qué título poner, cómo describir el producto, a qué precio venderlo, ni cómo hacer que su publicación aparezca en las búsquedas. Este **cuello de botella operativo** impide que pequeños vendedores, emprendedores y personas comunes accedan al ecommerce profesional.

## 💡 La solución

Listify elimina la parálisis operativa con un sistema de **agentes de IA especializados** que trabajan en paralelo:

1. **Subís una foto** de tu producto (y opcionalmente un contexto breve)
2. **4 agentes de IA trabajan en simultáneo** para generar todo lo necesario
3. **Revisás, editás y aprobás** con total control (Human in the Loop)
4. **Publicás con un click** en MercadoLibre

Lo que antes tomaba 30-60 minutos, ahora toma 30 segundos + tu revisión.

---

## 🧠 Arquitectura de agentes

Listify funciona como un **orquestador de agentes especializados**, cada uno experto en una tarea:

```
                    ┌─────────────┐
                    │   📸 INPUT  │
                    │  Foto + ctx │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ 🔍 VISION  │
                    │  Detecta    │
                    │  atributos  │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
     │  🔎 SEO     │ │ 💰 PRICE │ │  ✍️ COPY    │
     │  Título +   │ │ Análisis │ │  Marketing  │
     │  keywords   │ │ mercado  │ │  + CTA      │
     └──────┬──────┘ └────┬─────┘ └──────┬──────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
                    ┌──────▼──────┐
                    │ ✏️ HUMAN   │
                    │ IN THE LOOP│
                    │ Revisar +  │
                    │ Aprobar    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ 📦 PUBLISH │
                    │ MercadoLibre│
                    └─────────────┘
```

### Agentes detallados

| Agente | Función | Tecnología |
|--------|---------|------------|
| **Vision Node** | Analiza la foto y extrae atributos del producto (categoría, marca, estado, color, etc.) | Claude Vision API |
| **SEO Node** | Genera título optimizado (max 60 chars) + keywords para posicionamiento en marketplace | Claude + reglas MeLi |
| **Pricing Node** | Busca precios reales en MercadoLibre + análisis estadístico (min, max, promedio, mediana, sugerido) | MeLi API + Claude |
| **Copy Node** | Escribe descripción de marketing persuasiva + Call to Action | Claude |
| **Orchestrator** | Coordina los agentes: Vision primero, luego SEO + Pricing + Copy en paralelo | Python concurrent.futures |

### Características clave

- **Ejecución en paralelo**: SEO, Pricing y Copy corren simultáneamente, reduciendo el tiempo total
- **Validación inteligente**: Detecta si la foto no es un producto vendible antes de procesar
- **Búsqueda adaptativa**: Prueba múltiples variantes de búsqueda en MeLi para encontrar los mejores datos de mercado
- **Resiliencia**: Si la API de MeLi no responde, estima precios con IA y le avisa al usuario
- **Transparencia**: Indica claramente si los precios son datos reales o estimaciones
- **Human in the Loop**: El usuario siempre tiene la última palabra antes de publicar

---

## 🛠️ Stack tecnológico

| Componente | Tecnología | Por qué |
|------------|------------|---------|
| IA / LLM | Claude API (Anthropic) | Vision + texto en una sola API |
| Frontend | Streamlit | App web profesional con Python puro |
| Base de datos | SQLite | Sin servidor, portable, incluida en Python |
| Marketplace | MercadoLibre API | El marketplace más grande de Latam |
| Backend | Python | Simple, versátil, ideal para prototipos |

---

## 🚀 Instalación y uso

### Prerrequisitos

- Python 3.10+
- API key de [Anthropic](https://console.anthropic.com)
- App de desarrollador en [MercadoLibre](https://developers.mercadolibre.com.ar)

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/listify.git
cd listify

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar API keys
cp config_example.py config.py
# Editar config.py con tus keys reales

# 4. Inicializar base de datos
python database.py

# 5. Lanzar la app
streamlit run app.py
```

La app se abre automáticamente en `http://localhost:8501`.

### Uso

1. Ir a **"📸 Nuevo producto"**
2. Subir una foto del producto
3. (Opcional) Agregar contexto como marca, talle, estado
4. Click en **"🚀 Generar publicación"**
5. Ir a **"✏️ Revisar productos"** para editar y aprobar
6. Ir a **"📦 Publicar"** para subir a MercadoLibre

---

## 📁 Estructura del proyecto

```
listify/
├── app.py                  # Aplicación principal (Streamlit)
├── config.py               # API keys (NO se sube a git)
├── config_example.py       # Template de configuración
├── database.py             # Base de datos SQLite
├── requirements.txt        # Dependencias Python
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py     # Orquestador de agentes
│   ├── vision.py           # Vision Node (análisis de imagen)
│   ├── seo.py              # SEO Node (título + keywords)
│   ├── pricing.py          # Pricing Node (precios de mercado)
│   └── copywriter.py       # Copy Node (marketing + CTA)
└── meli/
    ├── __init__.py
    ├── auth.py             # Autenticación OAuth2 con MeLi
    └── api.py              # Publicación de productos en MeLi
```

---

## 🌎 Escalabilidad y visión

Listify fue diseñado desde el día cero para ser **agnóstico a plataformas e idiomas**:

- **Multi-plataforma**: La arquitectura modular permite agregar nuevos marketplaces (Tiendanube, Facebook Marketplace, Amazon, Shopify) creando un nuevo módulo en la carpeta correspondiente sin tocar el resto del código.
- **Multi-idioma**: Claude maneja +50 idiomas nativamente. Cambiar el mercado es tan simple como cambiar `MELI_SITE_ID` en la configuración (MLA → Argentina, MLB → Brasil, MLM → México).
- **Modelo SaaS Freemium**: Tier gratuito con límite de publicaciones mensuales, tier Pro con acceso ilimitado y analytics avanzados.

### Roadmap

- [ ] Illustration Node (generación de imágenes mejoradas con IA)
- [ ] Dashboard de analytics (rendimiento de publicaciones)
- [ ] Integración con Tiendanube y Facebook Marketplace
- [ ] Publicación en lote (múltiples productos a la vez)
- [ ] App móvil (foto directo desde el celular)

---

## 👥 Equipo

Desarrollado con 💪 en un hackathon de 28 horas.

---

## 📄 Licencia

MIT License — libre para usar, modificar y distribuir.
