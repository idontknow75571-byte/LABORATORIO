#!/usr/bin/env python3
"""
Script de automatización:
- Lee las prácticas definidas en practicas_ejemplo.json
- Genera PDFs ya rellenados con equipos, materiales, reactivos, etc.
- Deja en blanco (o con fondo destacado) solo: FECHA, HORA y FIRMAS
  para que se completen en el momento de uso.

Uso:
  python3 generar_formularios_semana.py P01
  python3 generar_formularios_semana.py P02 --alumno "Uliana Valentino Haidy" --codigo "6058145"
  python3 generar_formularios_semana.py --list   # muestra prácticas disponibles
"""

import json
import argparse
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, IndirectObject

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "practicas_ejemplo.json")
TEMPLATE_FICHA = os.path.join(SCRIPT_DIR, "Ficha_Oficial_Exacta_Rellenable.pdf")
TEMPLATE_MANT = os.path.join(SCRIPT_DIR, "Registro_Mantenimiento_Exacto_Rellenable.pdf")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "generados")


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def list_practicas(data):
    print("\nPrácticas disponibles:\n")
    for p in data["practicas"]:
        print(f"  {p['id']}: {p['nombre']}")
        print(f"       Equipos   → {p['equipos']}")
        print(f"       Materiales→ {p['materiales']}")
        print(f"       Reactivos → {p['reactivos']}\n")


def fill_pdf(template_path, output_path, field_values):
    """Rellena un PDF con campos AcroForm."""
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.append(reader)

    # Necesario para que los campos se vean rellenados en algunos lectores
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"].update(
            {NameObject("/NeedAppearances"): BooleanObject(True)}
        )

    writer.update_page_form_field_values(writer.pages[0], field_values)

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"  → {output_path}")


def generar(practica_id, alumno="", codigo="", fecha="", hora=""):
    data = load_data()
    practica = next((p for p in data["practicas"] if p["id"] == practica_id), None)
    if not practica:
        print(f"❌ No se encontró la práctica '{practica_id}'. Usa --list para ver opciones.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    defaults = data.get("defaults", {})

    print(f"\n Generando formularios para: {practica['nombre']} ({practica_id})")

    # --- Ficha de Uso ---
    ficha_values = {
        "docente": practica.get("docente", defaults.get("docente_responsable", "")),
        "modulo": practica.get("modulo", ""),
        "practica": practica.get("nombre", ""),
        "laboratorio": practica.get("laboratorio", ""),
        "alumno": alumno,
        "codigo": codigo,
        "fecha": fecha,          # se deja vacío o se pasa por parámetro
        "horario": hora,
        "equipos": practica.get("equipos", ""),
        "materiales": practica.get("materiales", ""),
        "reactivos": practica.get("reactivos", ""),
        "observaciones": practica.get("observaciones", ""),
        "atendido_por": "",
        "firma_usuario": "",
    }
    out_ficha = os.path.join(OUTPUT_DIR, f"Ficha_Uso_{practica_id}_{alumno.replace(' ', '_') or 'alumno'}.pdf")
    fill_pdf(TEMPLATE_FICHA, out_ficha, ficha_values)

    # --- Registro de Mantenimiento ---
    mant_values = {
        "facultad": defaults.get("facultad", "Ciencias Agrarias"),
        "escuela": defaults.get("escuela", "Ingeniería Agroindustrial"),
        "laboratorio": practica.get("laboratorio", "Microbiología"),
        "alumno": alumno,
        "practica": practica.get("nombre", ""),
        "codigo_equipo": "",
        "fecha": fecha,
        "hora": hora,
        "materiales_empleados": practica.get("materiales_mantenimiento", ""),
        "observacion": "",
        "nombre_tecnico": defaults.get("tecnico", "Amparo Factor Lopez"),
        "nombre_docente": defaults.get("docente_responsable", "Me. Eva Orizano Ponce"),
        "firma_tecnico": "",
        "firma_docente": "",
    }
    out_mant = os.path.join(OUTPUT_DIR, f"Mantenimiento_{practica_id}_{alumno.replace(' ', '_') or 'alumno'}.pdf")
    fill_pdf(TEMPLATE_MANT, out_mant, mant_values)

    print("\n✅ Listo. Abre los PDFs y completa solo FECHA, HORA y FIRMAS.")
    print("   (Los campos de fecha/hora aparecen con fondo amarillo para identificarlos fácilmente.)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera formularios de laboratorio pre-rellenados")
    parser.add_argument("practica", nargs="?", help="ID de la práctica (ej: P01)")
    parser.add_argument("--alumno", default="", help="Nombre del alumno")
    parser.add_argument("--codigo", default="", help="DNI o código de estudiante")
    parser.add_argument("--fecha", default="", help="Fecha (opcional, si ya la sabes)")
    parser.add_argument("--hora", default="", help="Hora (opcional)")
    parser.add_argument("--list", action="store_true", help="Listar prácticas disponibles")
    args = parser.parse_args()

    data = load_data()
    if args.list or not args.practica:
        list_practicas(data)
        if not args.practica:
            print("Ejemplo de uso:")
            print('  python3 generar_formularios_semana.py P01 --alumno "Uliana Valentino Haidy" --codigo "6058145"')
    else:
        generar(args.practica, args.alumno, args.codigo, args.fecha, args.hora)
