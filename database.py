# ============================================================
# database.py — Base de datos de productos (SQLite)
# ============================================================
# Piensen en esto como un Excel automatico.
# Cada producto es una fila, cada dato es una columna.
# SQLite guarda todo en UN archivo (listify.db).
# ============================================================

import sqlite3
from datetime import datetime
import json
import config


def conectar():
    """
    Abre la conexion a la base de datos.
    Si el archivo no existe, SQLite lo CREA automaticamente.
    """
    conexion = sqlite3.connect(config.DATABASE_NAME)
    # Esto hace que las filas se puedan leer como diccionarios
    # En vez de fila[0], podemos hacer fila["titulo"]
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas():
    """
    Crea la tabla de productos si no existe.
    Esto se ejecuta UNA sola vez al arrancar la app.
    Piensen en esto como "crear las columnas del Excel".
    """
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Datos originales del usuario
            imagen_path     TEXT NOT NULL,
            contexto        TEXT,
            
            -- Lo que genera el Vision Node
            atributos       TEXT,
            
            -- Lo que genera el SEO Node  
            titulo          TEXT,
            descripcion_seo TEXT,
            keywords        TEXT,
            
            -- Lo que genera el Pricing Node
            precio_sugerido REAL,
            precio_minimo   REAL,
            precio_maximo   REAL,
            precio_promedio REAL,
            precio_mediana  REAL,
            datos_mercado   TEXT,
            
            -- Lo que genera el Copy Node
            descripcion_marketing TEXT,
            call_to_action  TEXT,
            
            -- Control de estado
            estado          TEXT DEFAULT 'pendiente',
            fecha_creacion  TEXT,
            fecha_aprobacion TEXT,
            meli_item_id    TEXT,
            
            -- Plataforma destino (para escalabilidad futura)
            plataforma      TEXT DEFAULT 'mercadolibre'
        )
    """)

    conexion.commit()
    conexion.close()


def guardar_producto(imagen_path, contexto, atributos, seo, pricing, copy_data):
    """
    Guarda un producto NUEVO con todos los datos generados por la IA.
    Se llama despues de que el Orchestrator termina su trabajo.
    
    Parametros:
    - imagen_path: ruta donde se guardo la foto
    - contexto: texto opcional que escribio el usuario
    - atributos: dict con lo que detecto el Vision Node
    - seo: dict con titulo, descripcion, keywords
    - pricing: dict con precios sugeridos
    - copy_data: dict con texto marketing y CTA
    
    Retorna: el ID del producto creado
    """
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO productos (
            imagen_path, contexto, atributos,
            titulo, descripcion_seo, keywords,
            precio_sugerido, precio_minimo, precio_maximo,
            precio_promedio, precio_mediana, datos_mercado,
            descripcion_marketing, call_to_action,
            estado, fecha_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendiente', ?)
    """, (
        imagen_path,
        contexto,
        json.dumps(atributos, ensure_ascii=False),
        seo.get("titulo", ""),
        seo.get("descripcion", ""),
        json.dumps(seo.get("keywords", []), ensure_ascii=False),
        pricing.get("precio_sugerido"),
        pricing.get("precio_minimo"),
        pricing.get("precio_maximo"),
        pricing.get("precio_promedio"),
        pricing.get("precio_mediana"),
        json.dumps(pricing.get("datos_mercado", {}), ensure_ascii=False),
        copy_data.get("descripcion", ""),
        copy_data.get("cta", ""),
        datetime.now().isoformat()
    ))

    producto_id = cursor.lastrowid
    conexion.commit()
    conexion.close()
    return producto_id


def obtener_pendientes():
    """
    Trae todos los productos que estan esperando revision humana.
    Esto alimenta la pantalla de "Human in the Loop".
    """
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM productos WHERE estado = 'pendiente' ORDER BY fecha_creacion DESC"
    )
    productos = [dict(row) for row in cursor.fetchall()]
    conexion.close()
    return productos


def obtener_producto(producto_id):
    """Trae UN producto por su ID."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    producto = cursor.fetchone()
    conexion.close()
    return dict(producto) if producto else None


def actualizar_producto(producto_id, campos):
    """
    Actualiza los campos que el humano edito.
    'campos' es un diccionario, ej: {"titulo": "Nuevo titulo", "precio_sugerido": 15000}
    """
    conexion = conectar()
    cursor = conexion.cursor()

    # Construye el SQL dinamicamente segun que campos se editaron
    sets = ", ".join(f"{key} = ?" for key in campos.keys())
    valores = list(campos.values()) + [producto_id]

    cursor.execute(f"UPDATE productos SET {sets} WHERE id = ?", valores)
    conexion.commit()
    conexion.close()


def aprobar_producto(producto_id):
    """
    Marca un producto como aprobado y listo para publicar.
    Se llama cuando el humano aprieta "Aprobar" en la interfaz.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE productos 
        SET estado = 'aprobado', fecha_aprobacion = ? 
        WHERE id = ?
    """, (datetime.now().isoformat(), producto_id))
    conexion.commit()
    conexion.close()


def marcar_publicado(producto_id, meli_item_id):
    """
    Marca un producto como publicado en MercadoLibre.
    Guarda el ID que MeLi le asigno para referencia futura.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE productos 
        SET estado = 'publicado', meli_item_id = ? 
        WHERE id = ?
    """, (meli_item_id, producto_id))
    conexion.commit()
    conexion.close()


def obtener_todos():
    """Trae TODOS los productos sin importar el estado."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY fecha_creacion DESC")
    productos = [dict(row) for row in cursor.fetchall()]
    conexion.close()
    return productos


# ============================================================
# Si ejecutan este archivo solo (python database.py),
# crea las tablas. Util para la primera vez.
# ============================================================
if __name__ == "__main__":
    crear_tablas()
    print("Base de datos creada exitosamente: " + config.DATABASE_NAME)
