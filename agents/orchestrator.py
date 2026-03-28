# ============================================================
# agents/orchestrator.py — El Orquestador
# ============================================================
# Este es el JEFE. Coordina a todos los agentes.
# Flujo: Imagen → Vision → [SEO + Pricing + Copy] → Guardar
#
# Primero corre Vision (necesitamos saber QUE es el producto).
# Despues corre SEO, Pricing y Copy (pueden ir en paralelo
# porque los 3 dependen solo de los atributos de Vision).
# ============================================================

import concurrent.futures
from agents import vision, seo, pricing, copywriter
import database


def procesar_producto(imagen_bytes, contexto_usuario=""):
    """
    FUNCION PRINCIPAL — Orquesta todo el flujo end-to-end.
    
    Recibe:
    - imagen_bytes: la foto del producto
    - contexto_usuario: texto opcional del usuario
    
    Retorna:
    - producto_id: el ID en la base de datos
    - resultados: dict con todo lo generado por cada agente
    """

    resultados = {
        "vision": None,
        "seo": None,
        "pricing": None,
        "copy": None,
        "errores": []
    }

    # ========================================
    # FASE 1: Vision Node (debe ir PRIMERO)
    # ========================================
    # Sin saber que es el producto, los otros agentes
    # no pueden hacer nada. Por eso va primero y solo.
    print("🔍 Vision Node: analizando imagen...")
    try:
        resultados["vision"] = vision.analizar_producto(
            imagen_bytes, contexto_usuario
        )
        print(f"   ✓ Producto detectado: {resultados['vision'].get('nombre_producto', '?')}")
    except Exception as e:
        error = f"Vision Node fallo: {str(e)}"
        resultados["errores"].append(error)
        print(f"   ✗ {error}")
        # Sin vision, no podemos continuar
        return None, resultados

    atributos = resultados["vision"]

    # Verificar si la imagen es realmente un producto vendible
    if not atributos.get("es_producto", True):
        razon = atributos.get("razon", "No se pudo identificar un producto vendible")
        resultados["errores"].append(f"No es un producto vendible: {razon}")
        print(f"   ✗ No es un producto: {razon}")
        return None, resultados

    # ========================================
    # FASE 2: SEO + Pricing + Copy (EN PARALELO)
    # ========================================
    # Aca esta la magia: los 3 agentes corren AL MISMO TIEMPO.
    # En vez de esperar que termine uno para arrancar otro,
    # los lanzamos juntos. Esto ahorra MUCHO tiempo.
    #
    # concurrent.futures es como tener 3 empleados trabajando
    # al mismo tiempo en vez de uno solo haciendo todo.
    print("🚀 Lanzando SEO + Pricing + Copy en paralelo...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        # Lanzar las 3 tareas
        tarea_seo = pool.submit(seo.generar_seo, atributos)
        tarea_pricing = pool.submit(pricing.analizar_precios, atributos)
        tarea_copy_fn = lambda: copywriter.generar_copy(atributos)
        tarea_copy = pool.submit(tarea_copy_fn)

        # Esperar a que terminen y recoger resultados
        # SEO
        try:
            resultados["seo"] = tarea_seo.result(timeout=30)
            print(f"   ✓ SEO: {resultados['seo'].get('titulo', '?')}")
        except Exception as e:
            resultados["errores"].append(f"SEO Node fallo: {str(e)}")
            resultados["seo"] = {
                "titulo": atributos.get("nombre_producto", "Producto"),
                "descripcion": "",
                "keywords": []
            }
            print(f"   ✗ SEO fallo: {e}")

        # PRICING
        try:
            resultados["pricing"] = tarea_pricing.result(timeout=30)
            print(f"   ✓ Pricing: ${resultados['pricing'].get('precio_sugerido', '?')}")
        except Exception as e:
            resultados["errores"].append(f"Pricing Node fallo: {str(e)}")
            resultados["pricing"] = {
                "precio_sugerido": None,
                "precio_minimo": 0,
                "precio_maximo": 0,
                "precio_promedio": 0,
                "precio_mediana": 0
            }
            print(f"   ✗ Pricing fallo: {e}")

        # COPY
        try:
            resultados["copy"] = tarea_copy.result(timeout=30)
            print(f"   ✓ Copy generado ({resultados['copy'].get('tono', '?')})")
        except Exception as e:
            resultados["errores"].append(f"Copy Node fallo: {str(e)}")
            resultados["copy"] = {
                "descripcion": "",
                "cta": "Compralo ahora"
            }
            print(f"   ✗ Copy fallo: {e}")

    # ========================================
    # FASE 3: Guardar en base de datos
    # ========================================
    print("💾 Guardando en base de datos...")
    try:
        producto_id = database.guardar_producto(
            imagen_path="uploads/temp.jpg",  # La app actualiza esto
            contexto=contexto_usuario,
            atributos=resultados["vision"],
            seo=resultados["seo"],
            pricing=resultados["pricing"],
            copy_data=resultados["copy"]
        )
        print(f"   ✓ Producto guardado con ID: {producto_id}")
    except Exception as e:
        resultados["errores"].append(f"Error guardando: {str(e)}")
        producto_id = None
        print(f"   ✗ Error guardando: {e}")

    # Resumen
    total_errores = len(resultados["errores"])
    if total_errores == 0:
        print("✅ Proceso completo sin errores")
    else:
        print(f"⚠️ Proceso completo con {total_errores} error(es)")

    return producto_id, resultados


if __name__ == "__main__":
    print("Orchestrator listo.")
    print("Para probar, usa: procesar_producto(imagen_bytes, contexto)")
