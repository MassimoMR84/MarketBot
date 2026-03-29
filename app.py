# ============================================================
# app.py — Orquesta: Publicá con IA en segundos
# ============================================================

import streamlit as st
import os
import json
import uuid
from datetime import datetime as dt
import database
from agents import orchestrator

# ============================================================
# CONFIGURACION INICIAL
# ============================================================

MAX_IMAGE_SIZE_MB = 5
database.crear_tablas()
if not os.path.exists("uploads"):
    os.makedirs("uploads")

st.set_page_config(
    page_title="Orquesta — Publicá con IA",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE
# ============================================================

if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = None
if "producto_activo_id" not in st.session_state:
    st.session_state.producto_activo_id = None
if "recien_publicado" not in st.session_state:
    st.session_state.recien_publicado = False

# ============================================================
# CSS — Dark theme neon
# ============================================================

st.markdown("""
<style>
    .stApp { background-color: #0d0f17; }
    section[data-testid="stSidebar"] {
        background-color: #111420;
        border-right: 1px solid #1e2a3a;
    }
    .stepper-container {
        display: flex; align-items: center; justify-content: center;
        gap: 0; margin: 1rem auto 2rem auto; max-width: 300px;
    }
    .step-circle {
        width: 40px; height: 40px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 16px;
        border: 2px solid #2a3040; color: #4a5568;
        background: #161b2a; flex-shrink: 0;
    }
    .step-circle.active {
        border-color: #4ed2ff; color: #4ed2ff;
        background: rgba(78,210,255,0.1);
        box-shadow: 0 0 15px rgba(78,210,255,0.3);
    }
    .step-circle.done {
        border-color: #39ffb0; color: #0d0f17; background: #39ffb0;
    }
    .step-line { width: 40px; height: 2px; background: #2a3040; flex-shrink: 0; }
    .step-line.done { background: #39ffb0; }
    .empty-workspace {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; min-height: 500px; color: #4a5568; text-align: center;
    }
    .empty-workspace .icon { font-size: 64px; margin-bottom: 1rem; opacity: 0.4; }
    .empty-workspace .title { font-size: 20px; color: #7a8599; margin-bottom: 0.5rem; }
    .empty-workspace .subtitle { font-size: 14px; color: #4a5568; }
    .badge {
        font-size: 10px; padding: 2px 8px; border-radius: 12px;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
        display: inline-block; margin-top: 2px;
    }
    .badge-pendiente {
        background: rgba(255,140,66,0.15); color: #ff8c42;
        border: 1px solid rgba(255,140,66,0.3);
    }
    .badge-publicado {
        background: rgba(57,255,176,0.15); color: #39ffb0;
        border: 1px solid rgba(57,255,176,0.3);
    }
    .logo-text {
        font-size: 22px; font-weight: 800;
        background: linear-gradient(135deg, #4ed2ff, #a259ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; letter-spacing: -0.5px;
    }
    .success-screen { text-align: center; padding: 3rem 1rem; }
    .success-screen h1 {
        font-size: 32px;
        background: linear-gradient(135deg, #39ffb0, #4ed2ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; margin-bottom: 0.5rem;
    }
    .success-screen p { color: #7a8599; font-size: 16px; }
    .section-label {
        font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px;
        color: #4a5568; margin: 1rem 0 0.5rem 0; font-weight: 600;
    }
    .stDeployButton { display: none; }
    #MainMenu { display: none; }
    header[data-testid="stHeader"] { background: #0d0f17; }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4ed2ff, #a259ff);
        border: none; color: white; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================

def obtener_primera_imagen(producto):
    imagen_path = producto.get("imagen_path", "")
    if not imagen_path:
        return None
    try:
        paths = json.loads(imagen_path)
        if isinstance(paths, list) and paths:
            return paths[0] if os.path.exists(paths[0]) else None
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return imagen_path if os.path.exists(imagen_path) else None


def obtener_todas_imagenes(producto):
    imagen_path = producto.get("imagen_path", "")
    if not imagen_path:
        return []
    try:
        paths = json.loads(imagen_path)
        if isinstance(paths, list):
            return [p for p in paths if os.path.exists(p)]
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return [imagen_path] if os.path.exists(imagen_path) else []


def render_stepper(paso_actual):
    steps = []
    for i in range(1, 4):
        if i < paso_actual:
            steps.append('<div class="step-circle done">✓</div>')
        elif i == paso_actual:
            steps.append(f'<div class="step-circle active">{i}</div>')
        else:
            steps.append(f'<div class="step-circle">{i}</div>')
        if i < 3:
            line_class = "step-line done" if i < paso_actual else "step-line"
            steps.append(f'<div class="{line_class}"></div>')
    st.markdown(f'<div class="stepper-container">{"".join(steps)}</div>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown('<div class="logo-text">🎵 Orquesta</div>', unsafe_allow_html=True)
    st.caption("Publicá con IA en segundos")
    st.markdown("---")

    # Plataformas (decorativo)
    st.markdown('<div class="section-label">Plataformas</div>', unsafe_allow_html=True)
    p_cols = st.columns(4)
    for i, (icon, active) in enumerate([("🛒", True), ("🤝", False), ("🔵", False), ("📦", False)]):
        with p_cols[i]:
            if active:
                st.markdown(f"<div style='text-align:center;font-size:20px;opacity:1'>{icon}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center;font-size:20px;opacity:0.3'>{icon}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Buscador
    busqueda = st.text_input("🔍", placeholder="Buscar producto...", label_visibility="collapsed")

    # Botón añadir
    if st.button("➕ Añadir un Producto", use_container_width=True, type="primary"):
        st.session_state.vista_actual = "input"
        st.session_state.producto_activo_id = None
        st.session_state.recien_publicado = False
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-label">Mis Productos</div>', unsafe_allow_html=True)

    # Lista de productos
    productos = database.buscar_productos(busqueda) if busqueda else database.obtener_todos()

    if not productos:
        st.caption("No hay productos aún.")
    else:
        for producto in productos:
            titulo = producto.get("titulo", "Sin título") or "Sin título"
            estado = producto.get("estado", "pendiente")
            prod_id = producto["id"]
            titulo_corto = titulo[:20] + "…" if len(titulo) > 20 else titulo

            badge_cls = "badge-publicado" if estado == "publicado" else "badge-pendiente"
            badge_txt = "Publicado" if estado == "publicado" else "Pendiente"

            # Renderizar card del producto con HTML
            st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:space-between;
                        padding:8px 10px; margin:4px 0; border-radius:8px;
                        background:#161b2a; border:1px solid #1e2a3a;">
                <div style="flex:1; min-width:0;">
                    <div style="font-size:13px; color:#e2e8f0; white-space:nowrap;
                                overflow:hidden; text-overflow:ellipsis;">{titulo_corto}</div>
                    <span class="badge {badge_cls}">{badge_txt}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Botones funcionales debajo de la card
            btn_open, btn_del = st.columns([4, 1])
            with btn_open:
                if st.button("Abrir", key=f"o_{prod_id}", use_container_width=True):
                    st.session_state.producto_activo_id = prod_id
                    st.session_state.recien_publicado = False
                    st.session_state.vista_actual = "output" if estado == "publicado" else "checkpoint"
                    st.rerun()
            with btn_del:
                if st.button("🗑️", key=f"d_{prod_id}"):
                    for img in obtener_todas_imagenes(producto):
                        try: os.remove(img)
                        except OSError: pass
                    database.eliminar_producto(prod_id)
                    if st.session_state.producto_activo_id == prod_id:
                        st.session_state.vista_actual = None
                        st.session_state.producto_activo_id = None
                    st.rerun()

    st.markdown("---")
    st.markdown("⚙️ Configuración", help="Próximamente")


# ============================================================
# AREA DE TRABAJO
# ============================================================

vista = st.session_state.vista_actual

# --- VACIO ---
if vista is None:
    render_stepper(0)
    st.markdown("""
    <div class="empty-workspace">
        <div class="icon">🎵</div>
        <div class="title">Bienvenido a Orquesta</div>
        <div class="subtitle">Seleccioná un producto o creá uno nuevo desde la barra lateral</div>
    </div>
    """, unsafe_allow_html=True)

# --- PASO 1: INPUT ---
elif vista == "input":
    render_stepper(1)
    st.markdown("### 📸 Nuevo Producto")
    st.caption("Subí hasta 3 fotos, grabá un audio y/o escribí un contexto.")

    imagenes = st.file_uploader(
        "Fotos del producto (máx. 3)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )
    if imagenes and len(imagenes) > 3:
        st.warning("⚠️ Máximo 3 fotos.")
        imagenes = imagenes[:3]
    if imagenes:
        cols = st.columns(min(len(imagenes), 3))
        for i, img in enumerate(imagenes):
            with cols[i]:
                st.image(img, caption=f"Foto {i+1}", width=120)
                with st.popover(f"🔍 Ampliar foto {i+1}"):
                    st.image(img, use_container_width=True)

    st.markdown("**Audio (opcional):**")
    tab_g, tab_s = st.tabs(["🎙️ Grabar", "📁 Subir"])
    audio_bytes = None
    with tab_g:
        ag = st.audio_input("Grabá una descripción", key="audio_grab")
        if ag:
            audio_bytes = ag.getvalue()
            st.success(f"✅ Audio grabado ({len(audio_bytes)//1024} KB)")
    with tab_s:
        au = st.file_uploader("Subí audio", type=["wav","mp3","m4a","ogg","webm"], key="af", label_visibility="collapsed")
        if au:
            audio_bytes = au.getvalue()
            st.audio(audio_bytes)
            st.success(f"✅ Audio cargado ({len(audio_bytes)//1024} KB)")

    contexto = st.text_area(
        "Contexto escrito (opcional)",
        placeholder="Ej: Campera marca X, talle M, usada 2 veces...",
        max_chars=500
    )

    if imagenes:
        if st.button("🚀 Generar publicación", type="primary", use_container_width=True):
            lista_bytes, archivos_guardados, error = [], [], False
            for img in imagenes:
                ib = img.getvalue()
                if len(ib)/(1024*1024) > MAX_IMAGE_SIZE_MB:
                    st.error(f"❌ '{img.name}' muy pesada."); error = True; break
                lista_bytes.append(ib)
                ext = os.path.splitext(img.name)[1] or ".jpg"
                nombre = f"uploads/{uuid.uuid4().hex[:8]}_{dt.now().strftime('%Y%m%d%H%M%S')}{ext}"
                with open(nombre, "wb") as f: f.write(ib)
                archivos_guardados.append(nombre)

            if not error:
                ctx = contexto
                if audio_bytes:
                    with st.spinner("🎤 Transcribiendo..."):
                        try:
                            import speech_recognition as sr; import io
                            r = sr.Recognizer(); af = io.BytesIO(audio_bytes)
                            with sr.AudioFile(af) as src: ad = r.record(src)
                            t = r.recognize_google(ad, language="es-AR")
                            st.caption(f"🎤 *\"{t}\"*")
                            ctx = f"{ctx}\n\nAudio: {t}" if ctx else t
                        except Exception as e:
                            st.warning(f"⚠️ Audio: {e}")

                with st.spinner("🧠 Analizando producto..."):
                    entrada = lista_bytes if len(lista_bytes) > 1 else lista_bytes[0]
                    pid, res = orchestrator.procesar_producto(imagen_bytes=entrada, contexto_usuario=ctx)

                if pid:
                    pg = archivos_guardados[0] if len(archivos_guardados)==1 else json.dumps(archivos_guardados)
                    database.actualizar_producto(pid, {"imagen_path": pg})
                    st.session_state.vista_actual = "checkpoint"
                    st.session_state.producto_activo_id = pid
                    st.rerun()
                else:
                    errs = res.get("errores", [])
                    nop = [e for e in errs if "No es un producto" in e]
                    if nop: st.warning("⚠️ " + nop[0])
                    else:
                        st.error("❌ Error procesando.")
                        for e in errs: st.warning(e)
    else:
        st.info("Subí al menos una foto para continuar.")

# --- PASO 2: CHECKPOINT ---
elif vista == "checkpoint":
    render_stepper(2)
    pid = st.session_state.producto_activo_id
    if not pid: st.warning("No hay producto seleccionado."); st.stop()
    producto = database.obtener_producto(pid)
    if not producto: st.error("Producto no encontrado."); st.stop()

    st.markdown("### ✏️ Revisá y editá tu publicación")

    imgs = obtener_todas_imagenes(producto)
    if imgs:
        ic = st.columns(min(len(imgs), 3))
        for i, ip in enumerate(imgs):
            with ic[i]:
                st.image(ip, width=120)
                with st.popover(f"🔍 Ampliar"):
                    st.image(ip, use_container_width=True)

    try: attrs = json.loads(producto.get("atributos", "{}"))
    except: attrs = {}
    if attrs:
        with st.expander("🔍 Atributos IA", expanded=False):
            ac = st.columns(3)
            with ac[0]:
                st.markdown(f"**Categoría:** {attrs.get('categoria','N/A')}")
                st.markdown(f"**Marca:** {attrs.get('marca','N/A')}")
            with ac[1]:
                st.markdown(f"**Estado:** {attrs.get('estado','N/A')}")
                st.markdown(f"**Color:** {attrs.get('color','N/A')}")
            with ac[2]:
                c = attrs.get('confianza', 0)
                try: st.markdown(f"**Confianza:** {float(c):.0%}")
                except: st.markdown(f"**Confianza:** {c}")

    st.markdown("---")
    st.markdown("#### 🔎 SEO")
    cs1, cs2 = st.columns([2, 1])
    with cs1:
        nuevo_titulo = st.text_input("Título (máx 60)", value=producto.get("titulo",""), max_chars=60, key="et")
    with cs2:
        nuevas_kw = st.text_input("Keywords", value=producto.get("keywords","[]").replace("[","").replace("]","").replace('"',''), key="ek")

    st.markdown("#### 💰 Precio")
    try:
        dm = json.loads(producto.get("datos_mercado","{}"))
        if dm.get("fuente")=="sin datos": st.caption("⚠️ Sin precios reales")
        elif dm.get("fuente"): st.caption(f"✅ Datos de {dm['fuente']}")
    except: pass

    pc = st.columns(4)
    with pc[0]: st.metric("Mín", f"${producto.get('precio_minimo',0):,.0f}")
    with pc[1]: st.metric("Prom", f"${producto.get('precio_promedio',0):,.0f}")
    with pc[2]: st.metric("Med", f"${producto.get('precio_mediana',0):,.0f}")
    with pc[3]: st.metric("Máx", f"${producto.get('precio_maximo',0):,.0f}")

    nuevo_precio = st.number_input("Precio final", min_value=0.0, value=float(producto.get("precio_sugerido",0) or 0), step=100.0, key="ep")

    st.markdown("#### ✍️ Descripción")
    nueva_desc = st.text_area("Descripción marketing", value=producto.get("descripcion_marketing",""), height=200, key="ed", label_visibility="collapsed")
    nuevo_cta = st.text_input("Call to Action", value=producto.get("call_to_action",""), key="ec")

    st.markdown("---")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💾 Guardar", use_container_width=True):
            database.actualizar_producto(pid, {"titulo":nuevo_titulo,"precio_sugerido":nuevo_precio,"descripcion_marketing":nueva_desc,"call_to_action":nuevo_cta})
            st.success("Guardado."); st.rerun()
    with b2:
        if st.button("🚀 Publicar", type="primary", use_container_width=True):
            database.actualizar_producto(pid, {"titulo":nuevo_titulo,"precio_sugerido":nuevo_precio,"descripcion_marketing":nueva_desc,"call_to_action":nuevo_cta})
            database.marcar_publicado(pid, f"ORQ-{pid}")
            st.session_state.vista_actual = "output"
            st.session_state.recien_publicado = True
            st.rerun()

# --- PASO 3: OUTPUT ---
elif vista == "output":
    render_stepper(3)
    pid = st.session_state.producto_activo_id
    if not pid: st.warning("No hay producto."); st.stop()
    producto = database.obtener_producto(pid)
    if not producto: st.error("No encontrado."); st.stop()

    if st.session_state.recien_publicado:
        st.balloons()
        st.session_state.recien_publicado = False

    st.markdown("""
    <div class="success-screen">
        <h1>🎉 ¡Publicación exitosa!</h1>
        <p>Tu producto ya está listo para vender</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    oc1, oc2 = st.columns([1, 2])
    with oc1:
        img = obtener_primera_imagen(producto)
        if img: st.image(img, use_container_width=True)
    with oc2:
        st.markdown(f"**Título:** {producto.get('titulo','Sin título')}")
        st.markdown(f"**Precio:** ${producto.get('precio_sugerido',0):,.0f}")
        d = producto.get("descripcion_marketing","")
        if d: st.markdown(f"**Descripción:** {d[:200]}...")
        st.markdown(f"**CTA:** {producto.get('call_to_action','')}")

    st.markdown("---")
    ob1, ob2 = st.columns(2)
    with ob1:
        st.button("🔗 Ver publicación", use_container_width=True, disabled=True, help="Próximamente")
    with ob2:
        if st.button("➕ Crear otra publicación", type="primary", use_container_width=True):
            st.session_state.vista_actual = "input"
            st.session_state.producto_activo_id = None
            st.rerun()