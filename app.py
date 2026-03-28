# ============================================================
# app.py — La aplicacion principal de Listify
# ============================================================
# Este es el archivo que ARRANCA todo. Cuando corras
# "streamlit run app.py" en la terminal, se abre una
# pagina web con toda la interfaz.
#
# Streamlit funciona asi: vos escribis Python y el lo
# convierte en una pagina web automaticamente.
# Cada vez que el usuario hace algo (click, escribir),
# Streamlit RE-EJECUTA todo el archivo de arriba a abajo.
# ============================================================

import streamlit as st
import os
import json
import database
from agents import orchestrator

# ============================================================
# CONFIGURACION INICIAL
# ============================================================
# Esto se ejecuta UNA sola vez al arrancar la app.
# Crea las tablas en la base de datos si no existen,
# y crea la carpeta "uploads" para guardar las fotos.
# ============================================================

# Crear tablas si es la primera vez
database.crear_tablas()

# Crear carpeta para guardar las fotos subidas
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Configurar la pagina (titulo, icono, layout)
st.set_page_config(
    page_title="Listify — Publica con IA",
    page_icon="🚀",
    layout="wide"
)

# ============================================================
# BARRA LATERAL — Navegacion entre pantallas
# ============================================================
# st.sidebar crea un menu a la izquierda.
# El usuario elige en que pantalla quiere estar.
# ============================================================

st.sidebar.title("🚀 Listify")
st.sidebar.markdown("*Tu asistente de ecommerce con IA*")
st.sidebar.markdown("---")

# Esto crea los botones de navegacion
pantalla = st.sidebar.radio(
    "Navegación",
    ["📸 Nuevo producto", "✏️ Revisar productos", "📦 Publicar"],
    label_visibility="collapsed"
)

# Mostrar cuantos productos hay en cada estado
pendientes = database.obtener_pendientes()
aprobados = [p for p in database.obtener_todos() if p["estado"] == "aprobado"]
publicados = [p for p in database.obtener_todos() if p["estado"] == "publicado"]

st.sidebar.markdown("---")
st.sidebar.markdown(f"⏳ Pendientes: **{len(pendientes)}**")
st.sidebar.markdown(f"✅ Aprobados: **{len(aprobados)}**")
st.sidebar.markdown(f"📦 Publicados: **{len(publicados)}**")


# ============================================================
# PANTALLA 1: NUEVO PRODUCTO
# ============================================================
# Aca el usuario sube la foto y la IA genera todo.
# Es la "puerta de entrada" de la fabrica.
# ============================================================

if pantalla == "📸 Nuevo producto":

    st.title("📸 Nuevo producto")
    st.markdown("Subí una foto de tu producto y la IA se encarga del resto.")

    # --- Zona de subir imagen ---
    # st.file_uploader crea un boton de "subir archivo"
    # Limitamos a imagenes (jpg, png, webp)
    imagen = st.file_uploader(
        "Arrastrá o seleccioná la foto del producto",
        type=["jpg", "jpeg", "png", "webp"],
        help="Subi una foto clara del producto. Mejor con fondo limpio."
    )

    # --- Campo de contexto opcional ---
    contexto = st.text_area(
        "Contexto adicional (opcional)",
        placeholder="Ej: Es una campera marca X, talle M, la use 2 veces...",
        help="Si agregas contexto, la IA va a ser mas precisa.",
        max_chars=500
    )

    # --- Mostrar preview de la imagen ---
    if imagen is not None:
        # Mostrar la foto que subio el usuario
        st.image(imagen, caption="Vista previa", width=300)

        # --- Boton para procesar ---
        if st.button("🚀 Generar publicación", type="primary", use_container_width=True):

            # Leer los bytes de la imagen
            imagen_bytes = imagen.getvalue()

            # Guardar la imagen en disco
            nombre_archivo = f"uploads/{imagen.name}"
            with open(nombre_archivo, "wb") as f:
                f.write(imagen_bytes)

            # Mostrar un spinner mientras la IA trabaja
            # (esto puede tardar 10-20 segundos)
            with st.spinner("🧠 La IA está analizando tu producto... Esto puede tardar unos segundos."):

                # ACA ES DONDE PASA LA MAGIA
                # El orchestrator llama a Vision → SEO + Pricing + Copy
                producto_id, resultados = orchestrator.procesar_producto(
                    imagen_bytes=imagen_bytes,
                    contexto_usuario=contexto
                )

            # --- Mostrar resultados ---
            if producto_id:
                st.success(f"✅ ¡Producto procesado! ID: {producto_id}")

                # Actualizar la ruta de la imagen en la base de datos
                database.actualizar_producto(producto_id, {
                    "imagen_path": nombre_archivo
                })

                # Mostrar lo que genero cada agente en columnas
                # st.columns divide la pantalla en columnas lado a lado
                col1, col2 = st.columns(2)

                with col1:
                    # --- Vision ---
                    st.subheader("🔍 Atributos detectados")
                    vision = resultados.get("vision", {})
                    st.markdown(f"**Producto:** {vision.get('nombre_producto', 'N/A')}")
                    st.markdown(f"**Categoría:** {vision.get('categoria', 'N/A')}")
                    st.markdown(f"**Marca:** {vision.get('marca', 'N/A')}")
                    st.markdown(f"**Estado:** {vision.get('estado', 'N/A')}")
                    st.markdown(f"**Confianza IA:** {vision.get('confianza', 0):.0%}")

                    # --- SEO ---
                    st.subheader("🔎 SEO")
                    seo_r = resultados.get("seo", {})
                    st.markdown(f"**Título:** {seo_r.get('titulo', 'N/A')}")
                    st.markdown(f"**Keywords:** {', '.join(seo_r.get('keywords', []))}")

                with col2:
                    # --- Pricing ---
                    st.subheader("💰 Análisis de precios")
                    pricing_r = resultados.get("pricing", {})

                    # Indicar fuente de datos
                    if pricing_r.get("fuente") == "estimacion IA":
                        st.caption("⚠️ Precios estimados por IA (MeLi API no disponible)")
                        if pricing_r.get("nota"):
                            st.caption(f"ℹ️ {pricing_r.get('nota')}")
                    elif pricing_r.get("productos_analizados", 0) > 0:
                        st.caption(f"✅ Datos reales de MercadoLibre ({pricing_r.get('productos_analizados')} productos analizados)")

                    st.markdown(f"**Precio sugerido:** ${pricing_r.get('precio_sugerido', 'N/A')}")
                    st.markdown(f"**Rango:** ${pricing_r.get('precio_minimo', 0)} — ${pricing_r.get('precio_maximo', 0)}")
                    st.markdown(f"**Promedio mercado:** ${pricing_r.get('precio_promedio', 0)}")
                    st.markdown(f"**Mediana:** ${pricing_r.get('precio_mediana', 0)}")

                    # --- Copy ---
                    st.subheader("✍️ Copy de marketing")
                    copy_r = resultados.get("copy", {})
                    st.markdown(f"**CTA:** {copy_r.get('cta', 'N/A')}")

                # Descripcion completa abajo (ocupa mas espacio)
                st.subheader("📝 Descripción generada")
                st.text_area(
                    "Descripción",
                    value=copy_r.get("descripcion", ""),
                    height=200,
                    disabled=True,
                    label_visibility="collapsed"
                )

                # Mensaje para ir a revisar
                st.info("👉 Andá a **Revisar productos** en el menú de la izquierda para editar y aprobar.")

                # Mostrar errores si hubo
                if resultados.get("errores"):
                    with st.expander("⚠️ Errores durante el proceso"):
                        for error in resultados["errores"]:
                            st.warning(error)
            else:
                # Mostrar razon especifica si la hay
                errores = resultados.get("errores", [])
                no_producto = [e for e in errores if "No es un producto" in e]
                if no_producto:
                    st.warning("⚠️ " + no_producto[0])
                    st.info("Subí una foto de un producto que quieras vender (un objeto físico: ropa, electrónica, muebles, etc.)")
                else:
                    st.error("❌ Hubo un problema procesando el producto.")
                    if errores:
                        for error in errores:
                            st.warning(error)


# ============================================================
# PANTALLA 2: REVISAR PRODUCTOS (Human in the Loop)
# ============================================================
# Esta es la pantalla CLAVE del producto.
# Aca el humano revisa lo que genero la IA,
# puede editar cualquier campo, y aprueba.
# ============================================================

elif pantalla == "✏️ Revisar productos":

    st.title("✏️ Revisar productos")
    st.markdown("Revisá, editá y aprobá los productos generados por la IA.")

    # Traer productos pendientes de la base de datos
    pendientes = database.obtener_pendientes()

    if not pendientes:
        st.info("No hay productos pendientes de revisión. Subí uno nuevo desde '📸 Nuevo producto'.")
    else:
        st.markdown(f"Tenés **{len(pendientes)}** producto(s) para revisar.")

        # Mostrar cada producto pendiente
        for producto in pendientes:

            # st.expander crea una seccion colapsable
            with st.expander(
                f"📦 {producto.get('titulo', 'Sin título')} — ID: {producto['id']}",
                expanded=(len(pendientes) == 1)  # Si hay uno solo, abrirlo
            ):

                # Dividir en dos columnas: imagen a la izquierda, datos a la derecha
                col_img, col_datos = st.columns([1, 2])

                with col_img:
                    # Mostrar la imagen del producto
                    if producto.get("imagen_path") and os.path.exists(producto["imagen_path"]):
                        st.image(producto["imagen_path"], width=250)
                    else:
                        st.markdown("*Imagen no disponible*")

                    # Mostrar atributos detectados
                    st.markdown("**Atributos IA:**")
                    try:
                        attrs = json.loads(producto.get("atributos", "{}"))
                        st.markdown(f"- Categoría: {attrs.get('categoria', 'N/A')}")
                        st.markdown(f"- Marca: {attrs.get('marca', 'N/A')}")
                        st.markdown(f"- Estado: {attrs.get('estado', 'N/A')}")
                        st.markdown(f"- Confianza: {attrs.get('confianza', 0):.0%}")
                    except (json.JSONDecodeError, TypeError):
                        st.markdown("*No disponible*")

                with col_datos:
                    # --- CAMPOS EDITABLES ---
                    # Cada st.text_input / st.number_input crea un campo
                    # que el usuario puede modificar.
                    # Usamos key=f"campo_{id}" para que Streamlit
                    # no se confunda si hay varios productos.

                    st.markdown("#### SEO")
                    nuevo_titulo = st.text_input(
                        "Título (max 60 caracteres)",
                        value=producto.get("titulo", ""),
                        max_chars=60,
                        key=f"titulo_{producto['id']}"
                    )

                    nuevas_keywords = st.text_input(
                        "Keywords (separadas por coma)",
                        value=producto.get("keywords", "[]").replace("[", "").replace("]", "").replace('"', ''),
                        key=f"keywords_{producto['id']}"
                    )

                    st.markdown("#### Precio")
                    # Mostrar fuente de datos
                    try:
                        datos_m = json.loads(producto.get("datos_mercado", "{}"))
                        if datos_m.get("fuente") == "estimacion IA":
                            st.caption("⚠️ Precios estimados por IA (MeLi API no disponible)")
                            if datos_m.get("nota"):
                                st.caption(f"ℹ️ {datos_m['nota']}")
                        else:
                            st.caption("✅ Datos reales de MercadoLibre")
                    except (json.JSONDecodeError, TypeError):
                        pass

                    # Mostrar estadisticas de mercado
                    precio_cols = st.columns(4)
                    with precio_cols[0]:
                        st.metric("Mínimo", f"${producto.get('precio_minimo', 0):,.0f}")
                    with precio_cols[1]:
                        st.metric("Promedio", f"${producto.get('precio_promedio', 0):,.0f}")
                    with precio_cols[2]:
                        st.metric("Mediana", f"${producto.get('precio_mediana', 0):,.0f}")
                    with precio_cols[3]:
                        st.metric("Máximo", f"${producto.get('precio_maximo', 0):,.0f}")

                    nuevo_precio = st.number_input(
                        "Precio final de venta (ARS)",
                        min_value=0.0,
                        value=float(producto.get("precio_sugerido", 0) or 0),
                        step=100.0,
                        key=f"precio_{producto['id']}"
                    )

                    st.markdown("#### Descripción de marketing")
                    nueva_descripcion = st.text_area(
                        "Descripción",
                        value=producto.get("descripcion_marketing", ""),
                        height=200,
                        key=f"desc_{producto['id']}"
                    )

                    nuevo_cta = st.text_input(
                        "Call to Action",
                        value=producto.get("call_to_action", ""),
                        key=f"cta_{producto['id']}"
                    )

                    # --- BOTONES DE ACCION ---
                    btn_col1, btn_col2 = st.columns(2)

                    with btn_col1:
                        # Boton GUARDAR: guarda los cambios sin aprobar
                        if st.button("💾 Guardar cambios", key=f"guardar_{producto['id']}"):
                            database.actualizar_producto(producto["id"], {
                                "titulo": nuevo_titulo,
                                "precio_sugerido": nuevo_precio,
                                "descripcion_marketing": nueva_descripcion,
                                "call_to_action": nuevo_cta,
                            })
                            st.success("Cambios guardados.")
                            st.rerun()

                    with btn_col2:
                        # Boton APROBAR: guarda + marca como aprobado
                        if st.button("✅ Aprobar y listo", key=f"aprobar_{producto['id']}", type="primary"):
                            database.actualizar_producto(producto["id"], {
                                "titulo": nuevo_titulo,
                                "precio_sugerido": nuevo_precio,
                                "descripcion_marketing": nueva_descripcion,
                                "call_to_action": nuevo_cta,
                            })
                            database.aprobar_producto(producto["id"])
                            st.success("¡Producto aprobado! Pasá a '📦 Publicar' para subirlo.")
                            st.rerun()


# ============================================================
# PANTALLA 3: PUBLICAR EN MERCADOLIBRE
# ============================================================
# Muestra los productos aprobados listos para publicar.
# Por ahora muestra un resumen y un boton (la conexion
# real con MeLi la hacemos en meli/api.py).
# ============================================================

elif pantalla == "📦 Publicar":

    st.title("📦 Publicar en MercadoLibre")
    st.markdown("Productos aprobados y listos para subir.")

    # ==== PASO 1: Autenticacion con MercadoLibre ====
    # El usuario necesita conectar su cuenta de MeLi UNA vez.
    # Despues el token queda guardado en la sesion.

    from meli import auth, api

    # Verificar si ya tenemos token
    # st.session_state es como una "memoria" de Streamlit
    # que sobrevive entre clicks del usuario
    if "meli_token" not in st.session_state:
        st.session_state.meli_token = None

    # Verificar si MeLi nos mando un codigo en la URL
    # (esto pasa cuando el usuario vuelve de loguearse en MeLi)
    params = st.query_params
    codigo_meli = params.get("code")

    if codigo_meli and not st.session_state.meli_token:
        with st.spinner("Conectando con MercadoLibre..."):
            token_data = auth.obtener_token(codigo_meli)
            if token_data and "access_token" in token_data:
                st.session_state.meli_token = token_data["access_token"]
                st.success("✅ ¡Cuenta de MercadoLibre conectada!")
                # Limpiar el codigo de la URL
                st.query_params.clear()
                st.rerun()
            else:
                st.error("❌ Error conectando con MercadoLibre. Intentá de nuevo.")

    # Mostrar estado de conexion y boton de login
    if not st.session_state.meli_token:
        st.warning("⚠️ Necesitás conectar tu cuenta de MercadoLibre para publicar.")
        url_auth = auth.obtener_url_autorizacion()
        st.link_button(
            "🔗 Conectar con MercadoLibre",
            url_auth,
            type="primary",
            use_container_width=True
        )
        st.markdown("*Se va a abrir MercadoLibre para que inicies sesión y autorices la app.*")
    else:
        st.success("✅ Cuenta de MercadoLibre conectada")

    st.markdown("---")

    # ==== PASO 2: Mostrar productos para publicar ====
    aprobados = [p for p in database.obtener_todos() if p["estado"] == "aprobado"]

    if not aprobados:
        st.info("No hay productos aprobados. Revisá y aprobá desde '✏️ Revisar productos'.")
    else:
        for producto in aprobados:
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 1])

                with col1:
                    if producto.get("imagen_path") and os.path.exists(producto["imagen_path"]):
                        st.image(producto["imagen_path"], width=150)

                with col2:
                    st.markdown(f"### {producto.get('titulo', 'Sin título')}")
                    st.markdown(f"**Precio:** ${producto.get('precio_sugerido', 0):,.0f}")
                    st.markdown(f"**CTA:** {producto.get('call_to_action', '')}")

                with col3:
                    # Solo mostrar boton si estamos conectados a MeLi
                    if st.session_state.meli_token:
                        if st.button(
                            "🚀 Publicar",
                            key=f"publicar_{producto['id']}",
                            type="primary"
                        ):
                            with st.spinner("Publicando en MercadoLibre..."):
                                token = st.session_state.meli_token

                                # 1. Subir imagen
                                imagen_id = None
                                if producto.get("imagen_path") and os.path.exists(producto["imagen_path"]):
                                    imagen_id = api.subir_imagen(token, producto["imagen_path"])

                                # 2. Publicar producto
                                resultado = api.publicar_producto(token, producto, imagen_id)

                                if resultado and resultado.get("id"):
                                    item_id = resultado["id"]
                                    permalink = resultado.get("permalink", "")
                                    database.marcar_publicado(producto["id"], item_id)
                                    st.success(f"✅ ¡Publicado! ID: {item_id}")
                                    if permalink:
                                        st.markdown(f"[🔗 Ver publicación en MercadoLibre]({permalink})")
                                    st.rerun()
                                else:
                                    error_msg = resultado.get("message", "Error desconocido") if resultado else "Sin respuesta"
                                    st.error(f"❌ Error: {error_msg}")
                    else:
                        st.markdown("*Conectá MeLi arriba*")

                st.markdown("---")

    # ==== Productos ya publicados ====
    publicados = [p for p in database.obtener_todos() if p["estado"] == "publicado"]
    if publicados:
        st.subheader("✅ Ya publicados")
        for producto in publicados:
            meli_id = producto.get("meli_item_id", "")
            st.markdown(
                f"- **{producto.get('titulo', '')}** — "
                f"[Ver en MercadoLibre](https://articulo.mercadolibre.com.ar/{meli_id})"
            )