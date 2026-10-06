#!/usr/bin/env python3
"""
Genera PDFs rellenables para:
1. Ficha para Uso de Laboratorio
2. Registro de Mantenimiento e Higiene Básico
Universidad Nacional Hermilio Valdizán - Facultad de Ciencias Agrarias
Escuela Profesional de Ingeniería Agroindustrial
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white, gray
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfform
from reportlab.lib import colors
import os

OUTPUT_DIR = "/home/workdir/artifacts/lab_forms"

# Colores institucionales aproximados
AZUL_OSCURO = HexColor("#1a365d")
AZUL_MEDIO = HexColor("#2c5282")
GRIS_CLARO = HexColor("#f7fafc")
GRIS_BORDE = HexColor("#a0aec0")
VERDE = HexColor("#276749")

def crear_ficha_uso_laboratorio(path):
    """Crea la Ficha para Uso de Laboratorio con campos rellenables."""
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4  # 595.27 x 841.89

    # --- Encabezado ---
    c.setFillColor(AZUL_OSCURO)
    c.rect(0, height - 35*mm, width, 35*mm, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width/2, height - 12*mm, "UNIVERSIDAD NACIONAL HERMILIO VALDIZÁN")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, height - 18*mm, "FACULTAD DE CIENCIAS AGRARIAS")
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width/2, height - 24*mm, "ESCUELA PROFESIONAL DE INGENIERÍA AGROINDUSTRIAL")

    # Título del formulario
    c.setFillColor(AZUL_MEDIO)
    c.rect(15*mm, height - 48*mm, width - 30*mm, 10*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 45*mm, "FICHA PARA USO DE LABORATORIO")

    # --- Datos del encabezado (campos rellenables) ---
    y = height - 58*mm
    label_x = 20*mm
    field_x = 70*mm
    field_w = 120*mm
    field_h = 6*mm
    line_h = 9*mm

    campos_header = [
        ("DOCENTE RESPONSABLE", "docente"),
        ("MÓDULO / ASIGNATURA / CURSO", "modulo"),
        ("NOMBRE DE LA PRÁCTICA", "practica"),
        ("LABORATORIO", "laboratorio"),
        ("USUARIO / ALUMNO", "alumno"),
        ("DNI / CÓDIGO DE ESTUDIANTE", "codigo"),
        ("FECHA", "fecha"),
        ("HORARIO", "horario"),
    ]

    c.setFillColor(black)
    form = c.acroForm

    for i, (label, name) in enumerate(campos_header):
        yy = y - i * line_h
        c.setFont("Helvetica-Bold", 8)
        c.drawString(label_x, yy + 1.5*mm, label + " :")
        # Campo de texto
        form.textfield(
            name=name,
            tooltip=label,
            x=field_x,
            y=yy,
            width=field_w,
            height=field_h,
            borderWidth=0.5,
            borderColor=GRIS_BORDE,
            fillColor=HexColor("#fffbeb"),  # fondo amarillo claro para campos editables
            textColor=black,
            forceBorder=True,
            fontSize=9,
        )

    # --- Secciones numeradas ---
    y_sec = y - len(campos_header) * line_h - 8*mm

    def seccion_caja(titulo, nombre_campo, y_pos, altura=22*mm):
        c.setStrokeColor(AZUL_OSCURO)
        c.setLineWidth(1.2)
        c.setFillColor(GRIS_CLARO)
        c.roundRect(15*mm, y_pos - altura, width - 30*mm, altura, 3, fill=1, stroke=1)

        c.setFillColor(AZUL_OSCURO)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(18*mm, y_pos - 5*mm, titulo)

        form.textfield(
            name=nombre_campo,
            tooltip=titulo,
            x=18*mm,
            y=y_pos - altura + 3*mm,
            width=width - 36*mm,
            height=altura - 10*mm,
            borderWidth=0.5,
            borderColor=GRIS_BORDE,
            fillColor=white,
            textColor=black,
            forceBorder=True,
            fontSize=9,
            fieldFlags="multiline",
        )
        return y_pos - altura - 5*mm

    y_sec = seccion_caja("1. EQUIPOS:", "equipos", y_sec, 20*mm)
    y_sec = seccion_caja("2. MATERIALES Y/O UTENSILIOS:", "materiales", y_sec, 18*mm)
    y_sec = seccion_caja("3. REACTIVOS QUÍMICOS:", "reactivos", y_sec, 18*mm)

    # Observaciones
    c.setStrokeColor(AZUL_OSCURO)
    c.setFillColor(GRIS_CLARO)
    c.roundRect(15*mm, y_sec - 25*mm, width - 30*mm, 25*mm, 3, fill=1, stroke=1)
    c.setFillColor(AZUL_OSCURO)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(18*mm, y_sec - 5*mm, "OBSERVACIONES:")
    form.textfield(
        name="observaciones",
        tooltip="Observaciones",
        x=18*mm,
        y=y_sec - 22*mm,
        width=width - 36*mm,
        height=15*mm,
        borderWidth=0.5,
        borderColor=GRIS_BORDE,
        fillColor=white,
        textColor=black,
        forceBorder=True,
        fontSize=9,
        fieldFlags="multiline",
    )
    y_sec -= 32*mm

    # Atendido por
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(black)
    c.drawString(18*mm, y_sec, "ATENDIDO POR :")
    form.textfield(
        name="atendido_por",
        tooltip="Atendido por",
        x=50*mm,
        y=y_sec - 1*mm,
        width=80*mm,
        height=6*mm,
        borderWidth=0.5,
        borderColor=GRIS_BORDE,
        fillColor=HexColor("#fffbeb"),
        textColor=black,
        forceBorder=True,
        fontSize=9,
    )
    y_sec -= 12*mm

    # Nota de responsabilidad
    c.setFillColor(HexColor("#fef3c7"))
    c.roundRect(15*mm, y_sec - 28*mm, width - 30*mm, 28*mm, 2, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(18*mm, y_sec - 4*mm, "Nota:")
    c.setFont("Helvetica", 6.5)
    notas = [
        "• Revisar el equipo, material, utensilios y reactivos químicos al recibir.",
        "• Manipular el equipo, material, utensilios y reactivos químicos con sumo cuidado al realizar su práctica.",
        "• Todo equipo, material, utensilios y reactivos químicos quedará bajo su responsabilidad; del mismo modo la reposición corre bajo",
        "  la responsabilidad del usuario que haya ocasionado el incidente.",
    ]
    for i, n in enumerate(notas):
        c.drawString(18*mm, y_sec - 9*mm - i*4*mm, n)

    y_sec -= 38*mm

    # Firma del usuario
    c.setStrokeColor(AZUL_OSCURO)
    c.setLineWidth(1)
    c.line(width/2 - 40*mm, y_sec, width/2 + 40*mm, y_sec)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width/2, y_sec - 5*mm, "FIRMA DEL USUARIO")

    # Campo para firma digital (opcional)
    form.textfield(
        name="firma_usuario",
        tooltip="Firma digital o nombre",
        x=width/2 - 40*mm,
        y=y_sec + 2*mm,
        width=80*mm,
        height=8*mm,
        borderWidth=0,
        fillColor=white,
        textColor=black,
        fontSize=9,
    )

    # Pie de página
    c.setFillColor(AZUL_OSCURO)
    c.rect(0, 0, width, 12*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica", 7)
    c.drawCentredString(width/2, 4*mm, "Universidad Nacional Hermilio Valdizán  |  Laboratorio de Microbiología  |  Página 1 de 1")

    c.save()
    print(f"✓ Creado: {path}")


def crear_registro_mantenimiento(path):
    """Crea el Registro de Mantenimiento e Higiene Básico con checklist rellenable."""
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # --- Encabezado superior con códigos ---
    c.setFillColor(AZUL_OSCURO)
    c.rect(0, height - 28*mm, width, 28*mm, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(12*mm, height - 10*mm, "REGISTRO DE MANTENIMIENTO E")
    c.drawString(12*mm, height - 15*mm, "HIGIENE BÁSICO")

    # Caja de códigos a la derecha
    c.setFillColor(HexColor("#2d3748"))
    c.rect(width - 85*mm, height - 28*mm, 85*mm, 28*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica", 6)
    codigos = [
        "CÓDIGO DE LABORATORIO: SL02LA012",
        "CÓDIGO DE FORMATO: RMHB-LMIC-V01",
        "VERSIÓN: 01",
        "FECHA DE APROBACIÓN: 10/04/2026",
        "PÁGINA: 1 de 1",
        "ID DE TRAZABILIDAD: ________-2026-II",
    ]
    for i, cod in enumerate(codigos):
        c.drawString(width - 83*mm, height - 6*mm - i*3.5*mm, cod)

    # --- Sección DATOS ---
    y = height - 35*mm
    c.setFillColor(AZUL_MEDIO)
    c.rect(10*mm, y - 5*mm, width - 20*mm, 6*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(12*mm, y - 3.5*mm, "I. DATOS")

    y -= 12*mm
    form = c.acroForm
    label_w = 45*mm
    field_w = 50*mm
    col2_x = 110*mm

    # Fila 1
    campos = [
        (12*mm, "FACULTAD:", "facultad", "Ciencias Agrarias"),
        (col2_x, "ESCUELA PROFESIONAL:", "escuela", "Ing. Agroindustrial"),
    ]
    for x, lab, name, default in campos:
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x, y, lab)
        form.textfield(name=name, tooltip=lab, x=x + 38*mm if "FACULTAD" in lab else x + 48*mm,
                       y=y - 1*mm, width=40*mm, height=5*mm,
                       borderWidth=0.4, borderColor=GRIS_BORDE, fillColor=HexColor("#fffbeb"),
                       textColor=black, forceBorder=True, fontSize=8, value=default)

    y -= 8*mm
    c.setFont("Helvetica-Bold", 7)
    c.drawString(12*mm, y, "LABORATORIO:")
    form.textfield(name="laboratorio", tooltip="Laboratorio", x=40*mm, y=y-1*mm, width=55*mm, height=5*mm,
                   borderWidth=0.4, borderColor=GRIS_BORDE, fillColor=HexColor("#fffbeb"),
                   textColor=black, forceBorder=True, fontSize=8, value="Microbiología")

    c.drawString(col2_x, y, "NOMBRE DEL ALUMNO(A):")
    form.textfield(name="alumno", tooltip="Nombre del alumno", x=col2_x + 45*mm, y=y-1*mm, width=50*mm, height=5*mm,
                   borderWidth=0.4, borderColor=GRIS_BORDE, fillColor=HexColor("#fffbeb"),
                   textColor=black, forceBorder=True, fontSize=8)

    y -= 8*mm
    c.drawString(12*mm, y, "NOMBRE DE LA PRÁCTICA:")
    form.textfield(name="practica", tooltip="Nombre de la práctica", x=52*mm, y=y-1*mm, width=55*mm, height=5*mm,
                   borderWidth=0.4, borderColor=GRIS_BORDE, fillColor=HexColor("#fffbeb"),
                   textColor=black, forceBorder=True, fontSize=8)

    c.drawString(col2_x, y, "CÓDIGO EQUIPO (POEI):")
    form.textfield(name="codigo_equipo", tooltip="Código equipo", x=col2_x + 45*mm, y=y-1*mm, width=50*mm, height=5*mm,
                   borderWidth=0.4, borderColor=GRIS_BORDE, fillColor=HexColor("#fffbeb"),
                   textColor=black, forceBorder=True, fontSize=8)

    y -= 8*mm
    c.drawString(12*mm, y, "FECHA DE LA PRÁCTICA:")
    form.textfield(name="fecha", tooltip="Fecha", x=52*mm, y=y-1*mm, width=30*mm, height=5*mm,
                   borderWidth=0.4, borderColor=GRIS_BORDE, fillColor=HexColor("#fef3c7"),
                   textColor=black, forceBorder=True, fontSize=8)

    c.drawString(col2_x, y, "HORA DE LA PRÁCTICA:")
    form.textfield(name="hora", tooltip="Hora", x=col2_x + 42*mm, y=y-1*mm, width=30*mm, height=5*mm,
                   borderWidth=0.4, borderColor=GRIS_BORDE, fillColor=HexColor("#fef3c7"),
                   textColor=black, forceBorder=True, fontSize=8)

    # --- Checklist ---
    y -= 12*mm
    c.setFillColor(AZUL_MEDIO)
    c.rect(10*mm, y - 5*mm, width - 20*mm, 6*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(12*mm, y - 3.5*mm, "II. CHECKLIST Y DESCRIPCIÓN DE ACTIVIDADES")

    y -= 10*mm

    # Encabezado de tabla
    c.setFillColor(HexColor("#e2e8f0"))
    c.rect(10*mm, y - 5*mm, width - 20*mm, 6*mm, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(12*mm, y - 3.5*mm, "ACTIVIDAD")
    c.drawString(55*mm, y - 3.5*mm, "DESCRIPCIÓN DE LA ACTIVIDAD")
    c.drawCentredString(width - 35*mm, y - 3.5*mm, "CONFORMIDAD")
    c.setFont("Helvetica", 6)
    c.drawString(width - 48*mm, y - 3.5*mm, "SI")
    c.drawString(width - 38*mm, y - 3.5*mm, "NO")
    c.drawString(width - 28*mm, y - 3.5*mm, "NA")

    actividades = [
        ("Apagado y desconexión segura",
         "El equipo apagado desde el panel y desconectado de la red eléctrica (si aplica)."),
        ("Retiro de muestras",
         "Se retiran los restos de biomasa, líquidos o reactivos del interior del equipo."),
        ("Limpieza interna del equipo",
         "Se realiza limpieza interna con paño seco o ligeramente humedecido con agua de caño para quitar polvo, grasa o residuos."),
        ("Limpieza externa (carcasa)",
         "Se realiza limpieza externa con paño seco o ligeramente humedecido con agua de caño para quitar polvo, grasa o residuos."),
        ("Limpieza y enjuague de sensores",
         "Se realiza limpieza y enjuague de sensores con agua destilada y secado con papel tisú (si aplica)."),
        ("Lavado de accesorios",
         "Se realiza lavado de accesorios del equipo con agua del caño y detergente neutro (si aplica)."),
        ("Enjuague final",
         "Se elimina resto de detergente usando solo agua del caño."),
        ("Descontaminación del equipo",
         "Se aplicó alcohol isopropílico (70%) con un paño en los botones, pantallas táctiles e interior del equipo."),
        ("Limpieza y orden del área",
         "Se realiza limpieza y orden de la mesa de trabajo; quedó seco, limpio y libre de materiales de desecho."),
    ]

    row_h = 11*mm
    for i, (act, desc) in enumerate(actividades):
        yy = y - 6*mm - i * row_h
        # Fondo alternado
        if i % 2 == 0:
            c.setFillColor(HexColor("#f8fafc"))
            c.rect(10*mm, yy - row_h + 1*mm, width - 20*mm, row_h, fill=1, stroke=0)

        c.setStrokeColor(GRIS_BORDE)
        c.setLineWidth(0.3)
        c.rect(10*mm, yy - row_h + 1*mm, width - 20*mm, row_h, fill=0, stroke=1)

        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 6.5)
        # Actividad (puede ser multilinea corta)
        c.drawString(12*mm, yy - 4*mm, act[:28])
        if len(act) > 28:
            c.drawString(12*mm, yy - 7.5*mm, act[28:])

        c.setFont("Helvetica", 5.5)
        # Descripción
        words = desc.split()
        lines = []
        current = ""
        for w in words:
            if len(current + " " + w) < 72:
                current = (current + " " + w).strip()
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        for j, line in enumerate(lines[:3]):
            c.drawString(55*mm, yy - 3.5*mm - j*3*mm, line)

        # Checkboxes SI / NO / NA
        cb_size = 4*mm
        for k, val in enumerate(["SI", "NO", "NA"]):
            cx = width - 50*mm + k * 10*mm
            form.checkbox(
                name=f"act_{i+1}_{val.lower()}",
                tooltip=f"{act} - {val}",
                x=cx,
                y=yy - 6*mm,
                size=cb_size,
                borderWidth=0.8,
                borderColor=AZUL_OSCURO,
                fillColor=white,
                checked=False,
            )

    y = y - 6*mm - len(actividades) * row_h - 3*mm

    # Leyenda
    c.setFont("Helvetica", 6)
    c.setFillColor(black)
    c.drawString(12*mm, y, "LEYENDA:  NA = NO APLICA")

    # --- Materiales empleados ---
    y -= 8*mm
    c.setFillColor(AZUL_MEDIO)
    c.rect(10*mm, y - 5*mm, width - 20*mm, 6*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(12*mm, y - 3.5*mm, "III. MATERIALES, ACCESORIOS Y CONSUMIBLES EMPLEADOS")

    y -= 7*mm
    form.textfield(
        name="materiales_empleados",
        tooltip="Materiales empleados",
        x=12*mm, y=y - 12*mm,
        width=width - 24*mm, height=12*mm,
        borderWidth=0.5, borderColor=GRIS_BORDE, fillColor=white,
        textColor=black, forceBorder=True, fontSize=8, fieldFlags="multiline",
    )

    # Observación
    y -= 18*mm
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(12*mm, y, "OBSERVACIÓN:")
    form.textfield(
        name="observacion",
        tooltip="Observación",
        x=40*mm, y=y - 1*mm,
        width=width - 52*mm, height=6*mm,
        borderWidth=0.5, borderColor=GRIS_BORDE, fillColor=HexColor("#fffbeb"),
        textColor=black, forceBorder=True, fontSize=8,
    )

    # Firmas
    y -= 15*mm
    c.setStrokeColor(AZUL_OSCURO)
    c.setLineWidth(0.8)

    # Técnico
    c.line(15*mm, y, 70*mm, y)
    c.setFont("Helvetica", 6)
    c.drawCentredString(42.5*mm, y - 4*mm, "Técnico y/o especialista de laboratorio")
    form.textfield(name="firma_tecnico", tooltip="Firma técnico", x=15*mm, y=y+1*mm,
                   width=55*mm, height=6*mm, borderWidth=0, fillColor=white, fontSize=8)
    form.textfield(name="nombre_tecnico", tooltip="Nombre técnico", x=15*mm, y=y-10*mm,
                   width=55*mm, height=5*mm, borderWidth=0.4, borderColor=GRIS_BORDE,
                   fillColor=HexColor("#fffbeb"), forceBorder=True, fontSize=7,
                   value="Amparo Factor Lopez")

    # Docente
    c.line(width - 80*mm, y, width - 20*mm, y)
    c.drawCentredString(width - 50*mm, y - 4*mm, "Docente Responsable")
    form.textfield(name="firma_docente", tooltip="Firma docente", x=width-80*mm, y=y+1*mm,
                   width=60*mm, height=6*mm, borderWidth=0, fillColor=white, fontSize=8)
    form.textfield(name="nombre_docente", tooltip="Nombre docente", x=width-80*mm, y=y-10*mm,
                   width=60*mm, height=5*mm, borderWidth=0.4, borderColor=GRIS_BORDE,
                   fillColor=HexColor("#fffbeb"), forceBorder=True, fontSize=7,
                   value="Me. Eva Orizano Ponce")

    # Pie
    c.setFillColor(AZUL_OSCURO)
    c.rect(0, 0, width, 10*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica", 6)
    c.drawCentredString(width/2, 3.5*mm, "UNHEVAL  |  Laboratorio de Microbiología  |  Registro de Mantenimiento e Higiene Básico")

    c.save()
    print(f"✓ Creado: {path}")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    crear_ficha_uso_laboratorio(os.path.join(OUTPUT_DIR, "Ficha_Uso_Laboratorio_Rellenable.pdf"))
    crear_registro_mantenimiento(os.path.join(OUTPUT_DIR, "Registro_Mantenimiento_Higiene_Rellenable.pdf"))
    print("\n✅ Ambos formularios rellenables generados correctamente.")
