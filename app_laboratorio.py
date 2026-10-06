#!/usr/bin/env python3
"""
Aplicación web para automatizar los formularios de laboratorio UNHEVAL.
Ejecutar con:  streamlit run app_laboratorio.py
"""

import streamlit as st
import json
import os
import re
from datetime import datetime, date
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject

try:
    import openpyxl
except ImportError:
    openpyxl = None

# Rutas
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "practicas_ejemplo.json")
POEI_FILE = os.path.join(SCRIPT_DIR, "Codigos_POEI_Equipos.xlsx")
TEMPLATE_FICHA = os.path.join(SCRIPT_DIR, "Ficha_Oficial_Exacta_Rellenable.pdf")
TEMPLATE_MANT = os.path.join(SCRIPT_DIR, "Registro_Mantenimiento_Exacto_Rellenable.pdf")

st.set_page_config(
    page_title="Lab Forms UNHEVAL",
    page_icon=":)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Estilos ----------
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1a365d, #2c5282);
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.6rem; }
    .main-header p { color: #bee3f8; margin: 0.3rem 0 0 0; font-size: 0.95rem; }
    .stDownloadButton button {
        background-color: #276749 !important;
        color: white !important;
        border: none !important;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ---------- Funciones de datos ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"practicas": [], "defaults": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_poei_from_workbook(wb):
    """Extrae el mapeo nombre→POEI de un workbook openpyxl."""
    mapping = {}
    ws = wb.active
    for row in ws.iter_rows(min_row=1, max_col=2, values_only=True):
        nombre, codigo = row[0], row[1]
        if not nombre or not codigo:
            continue
        # Saltar encabezado
        if str(nombre).strip().lower() in ("nombre del equipo", "nombre", "equipo"):
            continue
        if str(codigo).strip().lower() in ("código poei", "codigo poei", "poei", "código"):
            continue
        mapping[str(nombre).strip()] = str(codigo).strip()
    return mapping


def load_poei_codes(uploaded_file=None):
    """
    Carga el Excel de códigos POEI.
    Prioridad: 1) archivo subido en la app  2) archivo en la carpeta
    """
    mapping = {}
    if not openpyxl:
        return mapping, "Falta instalar openpyxl. Ejecuta: pip install openpyxl"

    # 1) Archivo subido por el usuario
    if uploaded_file is not None:
        try:
            wb = openpyxl.load_workbook(uploaded_file, read_only=True, data_only=True)
            mapping = load_poei_from_workbook(wb)
            wb.close()
            if mapping:
                return mapping, f"Excel subido: {len(mapping)} equipos"
            return mapping, "El Excel subido no tiene datos válidos (columnas Nombre / Código POEI)"
        except Exception as e:
            return mapping, f"Error al leer el Excel subido: {e}"

    # 2) Buscar en varias rutas posibles
    candidatos = [
        POEI_FILE,
        os.path.join(SCRIPT_DIR, "Codigos_POEI_Equipos.xlsx"),
        os.path.join(os.getcwd(), "Codigos_POEI_Equipos.xlsx"),
        os.path.join(os.getcwd(), "lab_forms", "Codigos_POEI_Equipos.xlsx"),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            try:
                wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
                mapping = load_poei_from_workbook(wb)
                wb.close()
                if mapping:
                    return mapping, f"Excel cargado ({os.path.basename(ruta)}): {len(mapping)} equipos"
            except Exception as e:
                return mapping, f"Error al leer {ruta}: {e}"

    return mapping, "No se encontró Codigos_POEI_Equipos.xlsx. Súbelo abajo."


def normalizar(texto):
    """Minúsculas, sin acentos raros, sin espacios extra."""
    t = texto.lower().strip()
    t = t.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def buscar_poei(nombre_equipo, poei_map):
    """Busca el código POEI que mejor coincida con el nombre del equipo."""
    if not poei_map:
        return ""
    n = normalizar(nombre_equipo)

    # 1) Coincidencia exacta
    for nom, cod in poei_map.items():
        if normalizar(nom) == n:
            return cod

    # 2) El nombre del equipo está contenido en una entrada del Excel (o al revés)
    candidatos = []
    for nom, cod in poei_map.items():
        nn = normalizar(nom)
        if n in nn or nn in n:
            candidatos.append((len(nn), cod, nom))
    if candidatos:
        candidatos.sort()  # preferir el más corto (más específico)
        return candidatos[0][1]

    # 3) Coincidencia por palabras clave principales
    palabras = set(n.split())
    best, best_score = "", 0
    for nom, cod in poei_map.items():
        nn_pal = set(normalizar(nom).split())
        comunes = palabras & nn_pal
        score = len(comunes)
        if score > best_score and score >= 1:
            best_score = score
            best = cod
    return best


def fill_pdf(template_path, field_values) -> bytes:
    """Rellena un PDF y devuelve los bytes."""
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.append(reader)

    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"].update(
            {NameObject("/NeedAppearances"): BooleanObject(True)}
        )

    writer.update_page_form_field_values(writer.pages[0], field_values)

    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ---------- Cargar datos ----------
data = load_data()
practicas = {p["id"]: p for p in data.get("practicas", [])}
defaults = data.get("defaults", {})

# ---------- Header ----------
st.markdown("""
<div class="main-header">
    <h1>Formularios de Laboratorio – UNHEVAL</h1>
    <p>Universidad Nacional Hermilio Valdizán · Facultad de Ciencias Agrarias · Ingeniería Agroindustrial</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar: Gestión de prácticas ----------
with st.sidebar:
    st.header("️ Gestión de Prácticas")
    st.caption("Aquí puedes agregar o editar las prácticas semanales.")

    tab1, tab2 = st.tabs(["Seleccionar", "Agregar / Editar"])

    with tab1:
        if not practicas:
            st.warning("No hay prácticas registradas. Agrega una en la pestaña 'Agregar / Editar'.")
            selected_id = None
        else:
            opciones = {f"{p['id']} – {p['nombre']}": p["id"] for p in data["practicas"]}
            sel_label = st.selectbox("Práctica a usar:", list(opciones.keys()))
            selected_id = opciones[sel_label]

    with tab2:
        st.subheader("Nueva práctica o editar existente")
        edit_id = st.text_input("ID (ej: P04)", value="P04", key="edit_id")
        edit_nombre = st.text_input("Nombre de la práctica", key="edit_nombre")
        edit_modulo = st.text_input("Módulo / Asignatura", value="Microbiología", key="edit_modulo")
        edit_lab = st.text_input("Laboratorio", value="Microbiología", key="edit_lab")
        edit_docente = st.text_input("Docente responsable", value=defaults.get("docente_responsable", "Amparo Factor Lopez"), key="edit_docente")
        edit_equipos = st.text_area("Equipos", height=70, key="edit_equipos")
        edit_materiales = st.text_area("Materiales / Utensilios", height=70, key="edit_materiales")
        edit_reactivos = st.text_area("Reactivos químicos", height=70, key="edit_reactivos")
        edit_obs = st.text_area("Observaciones", height=50, key="edit_obs")
        edit_mat_mant = st.text_area("Materiales para mantenimiento", height=50, key="edit_mat_mant",
                                     value="Paños, Alcohol isopropílico 70%, Agua destilada, Detergente neutro, Papel tisú")

        if st.button(" Guardar práctica", use_container_width=True):
            if not edit_id or not edit_nombre:
                st.error("ID y Nombre son obligatorios.")
            else:
                nueva = {
                    "id": edit_id.strip(),
                    "nombre": edit_nombre.strip(),
                    "modulo": edit_modulo.strip(),
                    "laboratorio": edit_lab.strip(),
                    "docente": edit_docente.strip(),
                    "equipos": edit_equipos.strip(),
                    "materiales": edit_materiales.strip(),
                    "reactivos": edit_reactivos.strip(),
                    "observaciones": edit_obs.strip(),
                    "materiales_mantenimiento": edit_mat_mant.strip(),
                }
                # Actualizar o agregar
                encontrados = [i for i, p in enumerate(data["practicas"]) if p["id"] == edit_id.strip()]
                if encontrados:
                    data["practicas"][encontrados[0]] = nueva
                    st.success(f"Práctica {edit_id} actualizada.")
                else:
                    data["practicas"].append(nueva)
                    st.success(f"Práctica {edit_id} agregada.")
                save_data(data)
                st.rerun()

        st.divider()
        st.caption("Prácticas actuales:")
        for p in data.get("practicas", []):
            st.text(f"• {p['id']}: {p['nombre']}")

# ---------- Contenido principal ----------
if not selected_id or selected_id not in practicas:
    st.info("👈 Selecciona o crea una práctica en el panel izquierdo para comenzar.")
    st.stop()

practica = practicas[selected_id]

st.subheader(f" Práctica seleccionada: **{practica['nombre']}**")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Datos del alumno / sesión")
    alumno = st.text_input("Nombre del alumno / usuario", placeholder="Ej: :P")
    codigo = st.text_input("DNI / Código de estudiante", placeholder="Ej: -------")
    fecha = st.date_input("Fecha de la práctica", value=date.today())
    hora = st.text_input("Hora / Horario", placeholder="Ej: 08:00 - 10:00", value="")
    
with col2:
    st.markdown("#### Datos de la práctica (se rellenan solos)")
    st.text_input("Docente", value=practica.get("docente", ""), disabled=True)
    st.text_input("Módulo / Asignatura", value=practica.get("modulo", ""), disabled=True)
    st.text_input("Laboratorio", value=practica.get("laboratorio", ""), disabled=True)
    st.text_area("Equipos", value=practica.get("equipos", ""), height=70, disabled=True)
    st.text_area("Materiales", value=practica.get("materiales", ""), height=70, disabled=True)
    st.text_area("Reactivos", value=practica.get("reactivos", ""), height=70, disabled=True)

st.divider()

# ---------- Equipos y códigos POEI (1 ficha de mantenimiento por equipo) ----------
st.markdown("### 🔧 Equipos y códigos POEI")
st.caption("Cada equipo genera **una** ficha de mantenimiento. Solo se permite **un** código POEI por ficha.")

# Subir Excel si no está en la carpeta
uploaded_poei = st.file_uploader(
    "Sube aquí tu Excel de códigos POEI (Codigos_POEI_Equipos.xlsx)",
    type=["xlsx", "xls"],
    key="upload_poei",
    help="Si el archivo no está en la carpeta de la app, súbelo aquí."
)

poei_map, poei_msg = load_poei_codes(uploaded_poei)
if poei_map:
    st.success(poei_msg)
else:
    st.warning(poei_msg)

equipos_raw = practica.get("equipos", "")
lista_equipos = [e.strip() for e in equipos_raw.replace(";", ",").split(",") if e.strip()]

if not lista_equipos:
    st.warning("Esta práctica no tiene equipos definidos. Agrégalos en el panel izquierdo.")
else:
    st.write(f"**{len(lista_equipos)} equipo(s)** detectados → se generarán **{len(lista_equipos)}** Registro(s) de Mantenimiento.")

poei_codes = {}
cols_poei = st.columns(min(len(lista_equipos), 3) if lista_equipos else 1)
for i, eq in enumerate(lista_equipos):
    auto_poei = buscar_poei(eq, poei_map)
    with cols_poei[i % len(cols_poei)]:
        poei_codes[eq] = st.text_input(
            f"POEI – {eq}",
            value=auto_poei,
            placeholder="No encontrado en Excel",
            key=f"poei_{i}_{eq[:20]}",
            help="Se rellenó desde el Excel. Puedes corregirlo si hace falta."
        )
        if auto_poei:
            st.caption(f"✓ Auto: {auto_poei}")
        else:
            st.caption(" Sin coincidencia en Excel")

st.divider()

# ---------- Generar formularios ----------
st.markdown("### Generar formularios")

c1, c2, c3 = st.columns([1, 1, 1])
fecha_str = fecha.strftime("%d/%m/%Y") if fecha else ""

with c1:
    generar_ficha = st.button(" Generar Ficha de Uso", use_container_width=True, type="primary")
with c2:
    generar_mant = st.button(" Generar Mantenimientos (1 por equipo)", use_container_width=True, type="primary")
with c3:
    generar_ambos = st.button(" Generar todo", use_container_width=True)

def preparar_ficha():
    return {
        "docente": practica.get("docente", defaults.get("docente_responsable", "")),
        "modulo": practica.get("modulo", ""),
        "practica": practica.get("nombre", ""),
        "laboratorio": practica.get("laboratorio", ""),
        "alumno": alumno,
        "codigo": codigo,
        "fecha": fecha_str,
        "horario": hora,
        "equipos": practica.get("equipos", ""),
        "materiales": practica.get("materiales", ""),
        "reactivos": practica.get("reactivos", ""),
    }

def preparar_mant(poei_code=""):
    return {
        "alumno": alumno,
        "practica": practica.get("nombre", ""),
        "codigo_equipo": poei_code,
        "fecha": fecha_str,
        "hora": hora,
    }

# --- Ficha de Uso (una sola) ---
if generar_ficha or generar_ambos:
    if not alumno:
        st.warning("Escribe el nombre del alumno antes de generar.")
    else:
        pdf_bytes = fill_pdf(TEMPLATE_FICHA, preparar_ficha())
        nombre_archivo = f"Ficha_Uso_{selected_id}_{alumno.replace(' ', '_')}.pdf"
        st.download_button(
            label=f" Descargar {nombre_archivo}",
            data=pdf_bytes,
            file_name=nombre_archivo,
            mime="application/pdf",
            key="dl_ficha",
        )
        st.success("Ficha de Uso generada.")

# --- Registros de Mantenimiento: UNO POR CADA EQUIPO ---
if generar_mant or generar_ambos:
    if not alumno:
        st.warning("Escribe el nombre del alumno antes de generar.")
    elif not lista_equipos:
        st.warning("No hay equipos en esta práctica.")
    else:
        st.success(f"Se generaron **{len(lista_equipos)}** Registro(s) de Mantenimiento (1 por equipo):")
        for i, eq in enumerate(lista_equipos):
            poei = poei_codes.get(eq, "").strip()
            pdf_bytes = fill_pdf(TEMPLATE_MANT, preparar_mant(poei))
            # Nombre de archivo incluye el equipo y el POEI si existe
            eq_safe = eq.replace(" ", "_")[:30]
            poei_part = f"_{poei}" if poei else ""
            nombre_archivo = f"Mantenimiento_{selected_id}_{eq_safe}{poei_part}_{alumno.replace(' ', '_')}.pdf"
            st.download_button(
                label=f" {eq}" + (f" ({poei})" if poei else " (sin POEI)"),
                data=pdf_bytes,
                file_name=nombre_archivo,
                mime="application/pdf",
                key=f"dl_mant_{i}",
            )

# ---------- Pie ----------
st.divider()
st.caption("Universidad Nacional Hermilio Valdizán · Laboratorio de Microbiología · Formularios digitales automatizados")
