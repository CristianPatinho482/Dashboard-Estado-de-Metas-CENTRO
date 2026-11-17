# -*- coding: utf-8 -*-
"""Genera las páginas y visuales PBIR del tablero ASTIN."""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

BASE = Path(r"C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN")
REPORT = BASE / "ASTIN_Metas.Report"
DEF = REPORT / "definition"
PAGES = DEF / "pages"

SCHEMA_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
SCHEMA_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_PAGES = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"

VERDE = "#39A900"
VERDE_OSC = "#1E6B00"
GRIS = "#F5F7F5"
GRIS_TXT = "#4A4A4A"
AMARILLO = "#F2A900"
ROJO = "#C0392B"
AZUL = "#0078D4"

PAGINAS = [
    ("resumen", "Resumen ejecutivo"),
    ("metas", "Metas y cumplimiento"),
    ("pe04", "PE-04 Fichas"),
    ("pe14", "PE-14 Caracterización"),
    ("comparativo", "Comparativo multitemporal"),
    ("calidad", "Calidad y auditoría"),
]


def pid(nombre: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"astin-page-{nombre}").hex[:20]


def vid(nombre: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"astin-visual-{nombre}").hex[:20]


def lit(valor: str) -> dict:
    return {"expr": {"Literal": {"Value": valor}}}


def medida(nombre: str, etiqueta: str | None = None) -> dict:
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Medidas_ASTIN"}}, "Property": nombre}},
        "queryRef": f"_Medidas_ASTIN.{nombre}",
        "nativeQueryRef": etiqueta or nombre,
    }


def columna(entidad: str, propiedad: str, etiqueta: str | None = None) -> dict:
    return {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": entidad}}, "Property": propiedad}},
        "queryRef": f"{entidad}.{propiedad}",
        "nativeQueryRef": etiqueta or propiedad,
    }


def titulo(texto: str, tam: int = 12, color: str = "#1A1A1A", alineacion: str = "left") -> dict:
    return {
        "title": [{
            "properties": {
                "show": lit("true"),
                "text": lit("'" + texto.replace("'", "''") + "'"),
                "fontSize": lit(f"{tam}D"),
                "bold": lit("true"),
                "alignment": lit(f"'{alineacion}'"),
                "fontColor": {"solid": {"color": lit(f"'{color}'")}},
            }
        }]
    }


def visual(nombre: str, tipo: str, x: float, y: float, w: float, h: float, roles: dict | None = None,
           rotulo: str | None = None, objetos: dict | None = None, contenedor: dict | None = None,
           z: int = 1000, tab: int = 1000) -> dict:
    v = {
        "$schema": SCHEMA_VISUAL,
        "name": vid(nombre),
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": tab},
        "visual": {
            "visualType": tipo,
            "drillFilterOtherVisuals": True,
        },
    }
    if roles:
        v["visual"]["query"] = {"queryState": {rol: {"projections": proy} for rol, proy in roles.items()}}
    if objetos:
        v["visual"]["objects"] = objetos
    cont = contenedor or {}
    if rotulo:
        cont.update(titulo(rotulo))
    if cont:
        v["visual"]["visualContainerObjects"] = cont
    return v


def texto(nombre: str, x: float, y: float, w: float, h: float, contenido: str, tam: int = 12,
          color: str = "#1A1A1A", bold: bool = False, fondo: str | None = None) -> dict:
    estilo = {"fontFamily": "Segoe UI", "fontSize": f"{tam}pt", "color": color}
    if bold:
        estilo["fontWeight"] = "bold"
    obj = {
        "general": [{
            "properties": {
                "paragraphs": [{
                    "textRuns": [{"value": contenido, "textStyle": estilo}],
                    "horizontalTextAlignment": "left",
                }]
            }
        }]
    }
    cont = {"visualContainerObjects": {"padding": [{"properties": {"left": lit("8D"), "right": lit("8D"), "top": lit("6D"), "bottom": lit("6D")}}]}}
    v = visual(nombre, "textbox", x, y, w, h, objetos=obj, z=100, tab=100)
    v["visual"]["visualContainerObjects"] = cont["visualContainerObjects"]
    if fondo:
        v["visual"]["visualContainerObjects"]["background"] = [{
            "properties": {
                "show": lit("true"),
                "color": {"solid": {"color": lit(f"'{fondo}'")}},
                "transparency": lit("0D"),
            }
        }]
    return v


def banda(nombre: str, x: float, y: float, w: float, h: float, color: str = VERDE) -> dict:
    obj = {
        "shape": [{"properties": {"tileShape": lit("'rectangle'")}}],
        "fill": [{
            "properties": {
                "fillColor": {"solid": {"color": lit(f"'{color}'")}},
                "transparency": lit("0D"),
            },
            "selector": {"id": "default"},
        }],
        "outline": [{"properties": {"lineColor": {"solid": {"color": lit(f"'{color}'")}}}, "selector": {"id": "default"}}],
    }
    v = visual(nombre, "shape", x, y, w, h, objetos=obj, z=10, tab=10)
    v["howCreated"] = "InsertVisualButton"
    return v


def tarjeta(nombre: str, x: float, y: float, w: float, h: float, medida_nombre: str, rotulo: str,
            color: str = VERDE, tam: int = 22) -> dict:
    objetos = {
        "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "divider": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "label": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "value": [
            {
                "properties": {
                    "fontFamily": lit("'Segoe UI'"),
                    "fontSize": lit(f"{tam}D"),
                    "bold": lit("true"),
                    "fontColor": {"solid": {"color": lit(f"'{color}'")}},
                    "horizontalAlignment": lit("'left'"),
                    "labelDisplayUnits": lit("0D"),
                },
                "selector": {"id": "default"},
            },
            {
                "properties": {"labelDisplayUnits": lit("0D")},
                "selector": {"metadata": f"_Medidas_ASTIN.{medida_nombre}"},
            },
        ],
    }
    cont = {
        "background": [{"properties": {"show": lit("true"), "color": {"solid": {"color": lit("'#FFFFFF'")}}, "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true"), "color": {"solid": {"color": lit("'#E3E7E3'")}}, "radius": lit("8D")}}],
        "visualHeader": [{"properties": {"show": lit("false")}}],
        "padding": [{"properties": {"left": lit("12D"), "right": lit("12D"), "top": lit("10D"), "bottom": lit("8D")}}],
        "title": [{
            "properties": {
                "show": lit("true"),
                "text": lit("'" + rotulo.replace("'", "''") + "'"),
                "fontSize": lit("10D"),
                "bold": lit("false"),
                "fontColor": {"solid": {"color": lit("'#6B6B6B'")}},
                "alignment": lit("'left'"),
            }
        }],
    }
    return visual(nombre, "cardVisual", x, y, w, h, {"Data": [medida(medida_nombre)]}, objetos=objetos, contenedor=cont, z=200, tab=200)


def slicer(nombre: str, x: float, y: float, w: float, h: float, entidad: str, propiedad: str, rotulo: str) -> dict:
    objetos = {"data": [{"properties": {"mode": lit("'Dropdown'")}}]}
    return visual(nombre, "slicer", x, y, w, h, {"Values": [columna(entidad, propiedad)]}, rotulo=rotulo,
                  objetos=objetos, z=150, tab=150)


def encabezado(pagina: str, subtitulo: str) -> list[dict]:
    return [
        banda(f"{pagina}-banda", 0, 0, 1280, 72),
        texto(f"{pagina}-titulo", 20, 4, 920, 38, "Estado de las metas · Centro ASTIN", 17, "#FFFFFF", True),
        texto(f"{pagina}-sub", 20, 44, 1000, 24, subtitulo, 9, "#E8F5E0"),
        texto(f"{pagina}-fecha", 980, 24, 280, 24, "Corte multitemporal 2026", 9, "#E8F5E0"),
    ]


def pagina_resumen() -> list[dict]:
    vs = encabezado("resumen", "Resumen ejecutivo · metas, ejecución y aprendizaje")
    tarjetas = [
        ("Meta_Actual", "Meta vigente", VERDE_OSC),
        ("Ejecucion_Actual", "Ejecución acumulada", VERDE),
        ("Cumplimiento_Actual", "Cumplimiento", AMARILLO),
        ("Matriculados_Ultimo", "Aprendices matriculados", AZUL),
        ("PE14_Ultimo", "Aprendices caracterizados", "#6A4C93"),
        ("Desplazados_Ultimo", "Desplazados por violencia", ROJO),
    ]
    for i, (m, r, c) in enumerate(tarjetas):
        vs.append(tarjeta(f"resumen-kpi-{i}", 20 + i * 207, 78, 195, 86, m, r, c, 20))
    vs += [
        slicer("resumen-slicer-periodo", 20, 176, 240, 40, "DimPeriodo", "PeriodoTexto", "Periodo"),
        slicer("resumen-slicer-nivel", 270, 176, 240, 40, "DimNivelFormacion", "NombreNivelFormacion", "Nivel de formación"),
        slicer("resumen-slicer-estrategia", 520, 176, 240, 40, "DimEstrategia", "NombreEstrategia", "Estrategia"),
        visual("resumen-linea", "lineChart", 20, 228, 760, 242, {
            "Category": [columna("DimPeriodo", "PeriodoTexto", "Periodo")],
            "Y": [medida("Meta_Total", "Meta"), medida("Ejecucion_Total", "Ejecución")],
        }, "Meta vs ejecución por periodo", z=300, tab=300),
        visual("resumen-donut", "donutChart", 800, 228, 460, 242, {
            "Category": [columna("Fact_PE04_Fichas", "NOMBRE_JORNADA", "Jornada")],
            "Y": [medida("Matriculados_Ultimo", "Matriculados")],
        }, "Matriculados por jornada", z=300, tab=301),
        visual("resumen-barras", "clusteredBarChart", 20, 486, 600, 210, {
            "Category": [columna("DimNivelFormacion", "NombreNivelFormacion", "Nivel")],
            "Y": [medida("Porc_Cumplimiento_Metas", "Cumplimiento")],
        }, "Cumplimiento de metas por nivel", z=300, tab=302),
        visual("resumen-tabla", "tableEx", 640, 486, 620, 210, {
            "Values": [
                columna("Dim_Ficha_Programa", "NOMBRE_PROGRAMA", "Programa"),
                medida("Matriculados_Ultimo", "Matriculados"),
                medida("Activos_Ultimo", "Activos"),
                medida("Tasa_Activos_Ultimo", "Tasa activos"),
            ],
        }, "Programas con más aprendices", objetos={
            "columnWidth": [
                {"properties": {"value": lit("300D")}, "selector": {"metadata": "Dim_Ficha_Programa.NOMBRE_PROGRAMA"}},
                {"properties": {"value": lit("85D")}, "selector": {"metadata": "_Medidas_ASTIN.Total_Matriculados"}},
                {"properties": {"value": lit("75D")}, "selector": {"metadata": "_Medidas_ASTIN.Total_Activos"}},
                {"properties": {"value": lit("85D")}, "selector": {"metadata": "_Medidas_ASTIN.Tasa_Activos"}},
            ]
        }, z=300, tab=303),
    ]
    return vs


def pagina_metas() -> list[dict]:
    vs = encabezado("metas", "Metas y cumplimiento · formación titulada y complementaria")
    for i, (m, r, c) in enumerate([
        ("Meta_Actual", "Meta vigente", VERDE_OSC),
        ("Ejecucion_Actual", "Ejecución", VERDE),
        ("Cumplimiento_Actual", "Cumplimiento", AMARILLO),
        ("Brecha_Actual", "Brecha meta - ejecución", ROJO),
    ]):
        vs.append(tarjeta(f"metas-kpi-{i}", 20 + i * 308, 78, 288, 78, m, r, c, 19))
    vs += [
        visual("metas-pivot", "pivotTable", 20, 172, 800, 524, {
            "Rows": [columna("DimNivelFormacion", "NombreNivelFormacion", "Nivel"), columna("DimEstrategia", "NombreEstrategia", "Estrategia")],
            "Values": [
                medida("Meta_Actual", "Meta"),
                medida("Ejecucion_Actual", "Ejecución"),
                medida("Cumplimiento_Actual", "Cumplimiento"),
                medida("Brecha_Actual", "Brecha"),
            ],
        }, "Matriz de metas por nivel y estrategia", z=300, tab=300),
        visual("metas-barras", "clusteredColumnChart", 840, 172, 420, 250, {
            "Category": [columna("DimNivelFormacion", "NombreNivelFormacion", "Nivel")],
            "Y": [medida("Meta_Actual", "Meta"), medida("Ejecucion_Actual", "Ejecución")],
        }, "Meta vs ejecución por nivel", z=300, tab=301),
        visual("metas-linea", "lineChart", 840, 438, 420, 258, {
            "Category": [columna("DimPeriodo", "PeriodoTexto", "Periodo")],
            "Y": [medida("Porc_Cumplimiento_Metas", "Cumplimiento")],
        }, "Evolución del cumplimiento", z=300, tab=302),
    ]
    return vs


def pagina_pe04() -> list[dict]:
    vs = encabezado("pe04", "PE-04 · fichas, matrícula, activos y horas")
    for i, (m, r, c) in enumerate([
        ("Matriculados_Ultimo", "Matriculados", AZUL),
        ("Activos_Ultimo", "Activos", VERDE),
        ("Cancelados_Ultimo", "No activos (derivado)", ROJO),
        ("Horas_Ultimo", "Horas de fichas", "#6A4C93"),
    ]):
        vs.append(tarjeta(f"pe04-kpi-{i}", 20 + i * 308, 78, 288, 78, m, r, c, 19))
    vs += [
        visual("pe04-programas", "clusteredBarChart", 20, 172, 620, 524, {
            "Category": [columna("Dim_Ficha_Programa", "NOMBRE_PROGRAMA", "Programa")],
            "Y": [medida("Matriculados_Ultimo", "Matriculados")],
        }, "Programas con más aprendices", z=300, tab=300),
        visual("pe04-jornada", "clusteredColumnChart", 660, 172, 300, 240, {
            "Category": [columna("Fact_PE04_Fichas", "NOMBRE_JORNADA", "Jornada")],
            "Y": [medida("Matriculados_Ultimo", "Matriculados")],
        }, "Matriculados por jornada", z=300, tab=301),
        visual("pe04-modalidad", "donutChart", 976, 172, 284, 240, {
            "Category": [columna("Fact_PE04_Fichas", "MODALIDAD_FORMACION", "Modalidad")],
            "Y": [medida("Matriculados_Ultimo", "Matriculados")],
        }, "Por modalidad", z=300, tab=302),
        visual("pe04-horas", "clusteredBarChart", 660, 428, 600, 268, {
            "Category": [columna("Dim_Ficha_Programa", "NOMBRE_PROGRAMA", "Programa")],
            "Y": [medida("Horas_Ultimo", "Horas")],
        }, "Programas con más horas de formación", z=300, tab=303),
    ]
    return vs


def pagina_pe14() -> list[dict]:
    vs = encabezado("pe14", "PE-14 · caracterización de poblaciones")
    for i, (m, r, c) in enumerate([
        ("PE14_Ultimo", "Aprendices caracterizados", "#6A4C93"),
        ("Desplazados_Ultimo", "Desplazados por violencia", ROJO),
        ("Vulnerable_Ultimo", "Población vulnerable", AMARILLO),
        ("Cobertura_Ultimo", "Cobertura PE-14 / PE-04", VERDE),
    ]):
        vs.append(tarjeta(f"pe14-kpi-{i}", 20 + i * 308, 78, 288, 78, m, r, c, 18))
    vs += [
        visual("pe14-barras", "clusteredBarChart", 20, 172, 900, 524, {
            "Category": [columna("DimPoblacion", "NombreAmigable", "Población")],
            "Y": [medida("Vulnerable_Ultimo", "Aprendices")],
        }, "Aprendices en poblaciones vulnerables", z=300, tab=300),
        visual("pe14-grupo", "donutChart", 940, 172, 320, 240, {
            "Category": [columna("DimPoblacion", "GrupoPoblacional", "Grupo")],
            "Y": [medida("Vulnerable_Ultimo", "Aprendices")],
        }, "Por grupo", z=300, tab=301),
        visual("pe14-linea", "lineChart", 940, 428, 320, 268, {
            "Category": [columna("DimPeriodo", "PeriodoTexto", "Periodo")],
            "Y": [medida("Total_Aprendices_PE14", "Aprendices")],
        }, "Evolución", z=300, tab=303),
    ]
    return vs


def pagina_comparativo() -> list[dict]:
    vs = encabezado("comparativo", "Comparativo multitemporal · PE-04 vs PE-14")
    vs += [
        visual("comp-linea", "lineChart", 20, 84, 1240, 320, {
            "Category": [columna("DimPeriodo", "PeriodoTexto", "Periodo")],
            "Y": [medida("Total_Matriculados", "PE-04 matriculados"), medida("Total_Aprendices_PE14", "PE-14 caracterizados")],
        }, "Matriculados y caracterizados por mes", z=300, tab=300),
        visual("comp-tabla", "tableEx", 20, 418, 800, 278, {
            "Values": [
                columna("DimPeriodo", "PeriodoTexto", "Periodo"),
                medida("Meta_Total", "Meta"),
                medida("Ejecucion_Total", "Ejecución"),
                medida("Total_Matriculados", "PE-04"),
                medida("Total_Aprendices_PE14", "PE-14"),
            ],
        }, "Detalle por periodo", z=300, tab=301),
        visual("comp-barras", "clusteredColumnChart", 840, 418, 420, 278, {
            "Category": [columna("DimPeriodo", "PeriodoTexto", "Periodo")],
            "Y": [medida("Ejecucion_Total", "Ejecución acumulada")],
        }, "Ejecución acumulada por periodo", z=300, tab=302),
    ]
    return vs


def pagina_calidad() -> list[dict]:
    vs = encabezado("calidad", "Calidad y auditoría · conciliación de fuentes")
    vs += [
        visual("cal-tabla", "tableEx", 20, 84, 1240, 240, {
            "Values": [
                columna("DimPeriodo", "PeriodoTexto", "Periodo"),
                medida("Meta_Total", "Meta indicadores"),
                medida("Meta_Oficial_Total", "Meta oficial"),
                medida("Diferencia_Meta_Oficial", "Dif. meta"),
                medida("Ejecucion_Total", "Ejecución indicadores"),
                medida("Ejecucion_Oficial_Total", "Ejecución oficial"),
                medida("Diferencia_Ejecucion_Oficial", "Dif. ejecución"),
            ],
        }, "Conciliación metas vs control oficial", z=300, tab=300),
        visual("cal-auditoria", "tableEx", 20, 340, 660, 370, {
            "Values": [
                columna("_Auditoria_Ingesta", "Origen", "Origen"),
                columna("_Auditoria_Ingesta", "Archivo", "Archivo"),
                columna("_Auditoria_Ingesta", "Extension", "Tipo"),
                columna("_Auditoria_Ingesta", "IdPeriodo", "Periodo"),
                columna("_Auditoria_Ingesta", "FechaModificacion", "Modificado"),
                columna("_Auditoria_Ingesta", "TamanoKB", "KB"),
            ],
        }, "Archivos monitoreados en las tres carpetas", z=300, tab=301),
        texto("cal-nota", 700, 340, 560, 370,
              "Notas de calidad:\n\n"
              "1. La suma de indicadores de metas puede diferir del total oficial del encabezado por filas de estrategia (CampeSENA / FEP) que el archivo reporta por separado.\n\n"
              "2. PE-04 no trae una columna de cancelados: se calcula como matriculados menos activos y debe leerse como 'no activos'.\n\n"
              "3. Las horas son la intensidad horaria de las fichas, no horas-cronómetro.\n\n"
              "4. PE-14 es mensual; el último dato disponible puede ser anterior al de Metas.\n\n"
              "5. Al agregar un mes, ejecute scripts\\astin_etl.py y actualice el modelo.\n\n"
              "6. Desplazados por violencia: la tarjeta usa la definición estricta (violencia y variantes de cabeza de familia, incluidos afrocolombianos e indígenas desplazados) = 3.667 en agosto 2026. La barra muestra cada categoría por separado: 'Desplazados por la violencia' = 2.285. La lista original (3.465) incluía fenómenos naturales, discapacidad e indígenas generales; se ajustó.",
              9, GRIS_TXT),
    ]
    return vs


def main() -> None:
    PAGES.mkdir(parents=True, exist_ok=True)
    orden = []
    generadores = {
        "resumen": pagina_resumen,
        "metas": pagina_metas,
        "pe04": pagina_pe04,
        "pe14": pagina_pe14,
        "comparativo": pagina_comparativo,
        "calidad": pagina_calidad,
    }
    for clave, nombre in PAGINAS:
        page_id = pid(clave)
        orden.append(page_id)
        pd = PAGES / page_id
        pd.mkdir(parents=True, exist_ok=True)
        (pd / "page.json").write_text(json.dumps({
            "$schema": SCHEMA_PAGE,
            "name": page_id,
            "displayName": nombre,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        visuals = generadores[clave]()
        vdir = pd / "visuals"
        if vdir.exists():
            shutil.rmtree(vdir)
        vdir.mkdir(parents=True, exist_ok=True)
        for v in visuals:
            vd = vdir / v["name"]
            vd.mkdir(parents=True, exist_ok=True)
            (vd / "visual.json").write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")
    (PAGES / "pages.json").write_text(json.dumps({
        "$schema": SCHEMA_PAGES,
        "pageOrder": orden,
        "activePageName": orden[0],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Páginas y visuales generados en", REPORT)


if __name__ == "__main__":
    main()
