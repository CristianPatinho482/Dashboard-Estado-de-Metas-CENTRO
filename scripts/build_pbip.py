# -*- coding: utf-8 -*-
"""Genera el proyecto PBIP (modelo TMDL + reporte PBIR) del tablero ASTIN."""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path

BASE = Path(r"C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN")
PQ = BASE / "powerquery"
MODEL_NAME = "ASTIN_Metas"
MODEL_DIR = BASE / f"{MODEL_NAME}.SemanticModel"
REPORT_DIR = BASE / f"{MODEL_NAME}.Report"

RUTAS_BASE = {
    "RutaFuentes": r"C:\Users\capatino\OneDrive - Servicio Nacional de Aprendizaje\BACKUP DISCO\Mis proyectos\AREA LABORAL\SENA\POWER BI\Sistema de control e información - Estado de las metas centro ASTIN",
    "RutaProyecto": str(BASE),
}

RUTAS_DERIVADAS = {
    "RutaMetas": 'RutaFuentes & "\\01_Metas"',
    "RutaPE04": 'RutaFuentes & "\\02_Reportes_PE04"',
    "RutaPE14": 'RutaFuentes & "\\03_Reportes_PE14"',
    "RutaCurados": 'RutaProyecto & "\\data\\curated"',
}


TABLAS = {
    "FactMetas": {
        "archivo": "FactMetas.m",
        "columnas": [
            ("IdPeriodo", "int64", "0", "none", None, False),
            ("IdCentro", "int64", "0", "none", None, False),
            ("IdCategoria", "int64", "0", "none", None, False),
            ("IdNivelFormacion", "int64", "0", "none", None, False),
            ("IdEstrategia", "int64", "0", "none", None, False),
            ("Indicador", "string", None, "none", None, False),
            ("Indicador_Normalizado", "string", None, "none", None, True),
            ("Meta", "int64", "#,##0", "sum", None, False),
            ("Ejecucion", "int64", "#,##0", "sum", None, False),
            ("OrigenArchivo", "string", None, "none", None, True),
            ("Hoja", "string", None, "none", None, True),
            ("DiaCorte", "int64", "0", "none", None, True),
        ],
    },
    "Fact_PE04_Fichas": {
        "archivo": "Fact_PE04_Fichas.m",
        "columnas": [
            ("ID_REGISTRO_UUID", "string", None, "none", None, True),
            ("ID_PERIODO", "int64", "0", "none", None, False),
            ("CODIGO_FICHA", "int64", "0", "none", None, False),
            ("NOMBRE_PROGRAMA", "string", None, "none", None, False),
            ("CODIGO_JORNADA", "int64", "0", "none", None, True),
            ("NOMBRE_JORNADA", "string", None, "none", None, False),
            ("MODALIDAD_FORMACION", "string", None, "none", None, False),
            ("ESTADO_CURSO", "string", None, "none", None, False),
            ("NIVEL_FORMACION", "string", None, "none", None, False),
            ("APRENDICES_MATRICULADOS", "int64", "#,##0", "sum", None, False),
            ("APRENDICES_ACTIVOS", "int64", "#,##0", "sum", None, False),
            ("APRENDICES_CANCELADOS", "int64", "#,##0", "sum", None, False),
            ("TOTAL_HORAS", "double", "#,##0.0", "sum", None, False),
            ("IdCentro", "int64", "0", "none", None, False),
            ("ORIGEN_ARCHIVO", "string", None, "none", None, True),
        ],
    },
    "Fact_PE14_Aprendices": {
        "archivo": "Fact_PE14_Aprendices.m",
        "columnas": [
            ("ID_REGISTRO_UUID", "string", None, "none", None, True),
            ("ID_PERIODO", "int64", "0", "none", None, False),
            ("IdCentro", "int64", "0", "none", None, False),
            ("CODIGO_FICHA", "int64", "0", "none", None, False),
            ("IdPoblacion", "int64", "0", "none", None, False),
            ("NombrePoblacion", "string", None, "none", None, True),
            ("Cantidad_Aprendices", "int64", "#,##0", "sum", None, False),
        ],
    },
    "DimPeriodo": {
        "archivo": "DimPeriodo.m",
        "columnas": [
            ("IdPeriodo", "int64", "0", "none", None, False),
            ("Anio", "int64", "0", "none", None, False),
            ("Mes", "int64", "0", "none", None, False),
            ("NombreMes", "string", None, "none", "Mes", False),
            ("Trimestre", "int64", "0", "none", None, False),
            ("FechaInicio", "dateTime", "dd/MM/yyyy", "none", None, False),
            ("FechaFin", "dateTime", "dd/MM/yyyy", "none", None, False),
            ("PeriodoTexto", "string", None, "none", "IdPeriodo", False),
            ("OrdenAnual", "int64", "0", "none", None, True),
        ],
    },
    "DimCategoria": {
        "archivo": "DimCategoria.m",
        "columnas": [
            ("IdCategoria", "int64", "0", "none", None, False),
            ("NombreCategoria", "string", None, "none", "Orden", False),
            ("Orden", "int64", "0", "none", None, True),
        ],
    },
    "DimNivelFormacion": {
        "archivo": "DimNivelFormacion.m",
        "columnas": [
            ("IdNivelFormacion", "int64", "0", "none", None, False),
            ("NombreNivelFormacion", "string", None, "none", "Orden", False),
            ("IdCategoria", "int64", "0", "none", None, True),
            ("Orden", "int64", "0", "none", None, True),
        ],
    },
    "DimEstrategia": {
        "archivo": "DimEstrategia.m",
        "columnas": [
            ("IdEstrategia", "int64", "0", "none", None, False),
            ("NombreEstrategia", "string", None, "none", "Orden", False),
            ("Orden", "int64", "0", "none", None, True),
        ],
    },
    "DimCentro": {
        "archivo": "DimCentro.m",
        "columnas": [
            ("IdCentro", "int64", "0", "none", None, False),
            ("NombreCentro", "string", None, "none", None, False),
            ("NombreRegional", "string", None, "none", None, False),
            ("CodigoRegional", "int64", "0", "none", None, True),
        ],
    },
    "Dim_Ficha_Programa": {
        "archivo": "Dim_Ficha_Programa.m",
        "columnas": [
            ("CODIGO_FICHA", "int64", "0", "none", None, False),
            ("NOMBRE_PROGRAMA", "string", None, "none", None, False),
            ("CODIGO_JORNADA", "int64", "0", "none", None, True),
            ("NOMBRE_JORNADA", "string", None, "none", None, False),
            ("MODALIDAD_FORMACION", "string", None, "none", None, False),
            ("NIVEL_FORMACION", "string", None, "none", None, False),
            ("IdCentro", "int64", "0", "none", None, True),
            ("UltimoPeriodo", "int64", "0", "none", None, True),
        ],
    },
    "DimPoblacion": {
        "archivo": "DimPoblacion.m",
        "columnas": [
            ("IdPoblacion", "int64", "0", "none", None, False),
            ("NombrePoblacion", "string", None, "none", None, True),
            ("NombreAmigable", "string", None, "none", "Orden", False),
            ("GrupoPoblacional", "string", None, "none", None, False),
            ("EsVulnerable", "int64", "0", "none", None, False),
            ("EsDesplazamientoViolencia", "int64", "0", "none", None, True),
            ("Orden", "int64", "0", "none", None, True),
        ],
    },
    "_Control_Metas": {
        "archivo": "_Control_Metas.m",
        "columnas": [
            ("IdPeriodo", "int64", "0", "none", None, False),
            ("Meta_Oficial", "int64", "#,##0", "none", None, False),
            ("Ejecucion_Oficial", "int64", "#,##0", "none", None, False),
            ("Fuente", "string", None, "none", None, True),
            ("OrigenArchivo", "string", None, "none", None, True),
            ("Hoja", "string", None, "none", None, True),
            ("DiaCorte", "int64", "0", "none", None, True),
        ],
    },
    "_Auditoria_Ingesta": {
        "archivo": "_Auditoria_Ingesta.m",
        "columnas": [
            ("Origen", "string", None, "none", None, False),
            ("Archivo", "string", None, "none", None, False),
            ("Extension", "string", None, "none", None, False),
            ("IdPeriodo", "int64", "0", "none", None, False),
            ("FechaModificacion", "dateTime", "dd/MM/yyyy HH:mm", "none", None, False),
            ("TamanoKB", "double", "#,##0.0", "none", None, False),
        ],
    },
}
RELACIONES = [
    ("FactMetas", "IdPeriodo", "DimPeriodo", "IdPeriodo"),
    ("Fact_PE04_Fichas", "ID_PERIODO", "DimPeriodo", "IdPeriodo"),
    ("Fact_PE14_Aprendices", "ID_PERIODO", "DimPeriodo", "IdPeriodo"),
    ("_Control_Metas", "IdPeriodo", "DimPeriodo", "IdPeriodo"),
    ("Fact_PE04_Fichas", "CODIGO_FICHA", "Dim_Ficha_Programa", "CODIGO_FICHA"),
    ("Fact_PE14_Aprendices", "CODIGO_FICHA", "Dim_Ficha_Programa", "CODIGO_FICHA"),
    ("Fact_PE14_Aprendices", "IdPoblacion", "DimPoblacion", "IdPoblacion"),
    ("FactMetas", "IdCategoria", "DimCategoria", "IdCategoria"),
    ("FactMetas", "IdNivelFormacion", "DimNivelFormacion", "IdNivelFormacion"),
    ("FactMetas", "IdEstrategia", "DimEstrategia", "IdEstrategia"),
    ("FactMetas", "IdCentro", "DimCentro", "IdCentro"),
    ("Fact_PE04_Fichas", "IdCentro", "DimCentro", "IdCentro"),
    ("Fact_PE14_Aprendices", "IdCentro", "DimCentro", "IdCentro"),
]

MEDIDAS = [
    ("Meta_Total", "SUM ( FactMetas[Meta] )", "#,##0", "01 Metas", "Meta anual del centro según los indicadores cargados."),
    ("Ejecucion_Total", "SUM ( FactMetas[Ejecucion] )", "#,##0", "01 Metas", "Ejecución acumulada reportada en el archivo de metas."),
    ("Porc_Cumplimiento_Metas", "DIVIDE ( [Ejecucion_Total], [Meta_Total], 0 )", "0.0%", "01 Metas", "Ejecución / meta."),
    ("Brecha_Metas", "[Meta_Total] - [Ejecucion_Total]", "#,##0;-#,##0;0", "01 Metas", "Meta menos ejecución."),
    ("Estado_Meta",
     'SWITCH ( TRUE (), [Porc_Cumplimiento_Metas] >= 1, "Sobre ejecución", [Porc_Cumplimiento_Metas] >= 0.9, "En ruta", [Porc_Cumplimiento_Metas] >= 0.7, "Vulnerable", "Bajo" )',
     None, "01 Metas", "Semáforo de cumplimiento."),
    ("Ejecucion_Mes_Anterior",
     'VAR p = MAX ( DimPeriodo[IdPeriodo] )\nVAR anterior = IF ( MOD ( p, 100 ) = 1, p - 89, p - 1 )\nRETURN CALCULATE ( [Ejecucion_Total], REMOVEFILTERS ( DimPeriodo ), DimPeriodo[IdPeriodo] = anterior )',
     "#,##0", "01 Metas", "Ejecución del periodo inmediatamente anterior."),
    ("Variacion_Ejecucion_MoM",
     "DIVIDE ( [Ejecucion_Total] - [Ejecucion_Mes_Anterior], [Ejecucion_Mes_Anterior] )",
     "0.0%;-0.0%;0.0%", "01 Metas", "Variación porcentual de la ejecución frente al mes anterior."),
    ("Ejecucion_Incremental",
     "[Ejecucion_Total] - [Ejecucion_Mes_Anterior]",
     "#,##0;-#,##0;0", "01 Metas", "Ejecución incremental del mes (la ejecución de Metas es acumulada)."),
    ("Meta_Oficial_Total", "SUM ( _Control_Metas[Meta_Oficial] )", "#,##0", "06 Control", "Meta oficial del encabezado del archivo, para conciliación."),
    ("Ejecucion_Oficial_Total", "SUM ( _Control_Metas[Ejecucion_Oficial] )", "#,##0", "06 Control", "Ejecución oficial del encabezado del archivo, para conciliación."),
    ("Diferencia_Meta_Oficial", "[Meta_Total] - [Meta_Oficial_Total]", "#,##0;-#,##0;0", "06 Control", "Diferencia entre suma de indicadores y meta oficial."),
    ("Diferencia_Ejecucion_Oficial", "[Ejecucion_Total] - [Ejecucion_Oficial_Total]", "#,##0;-#,##0;0", "06 Control", "Diferencia entre suma de indicadores y ejecución oficial."),
    ("Total_Matriculados", "SUM ( Fact_PE04_Fichas[APRENDICES_MATRICULADOS] )", "#,##0", "02 PE-04", "Aprendices matriculados en las fichas del periodo."),
    ("Total_Activos", "SUM ( Fact_PE04_Fichas[APRENDICES_ACTIVOS] )", "#,##0", "02 PE-04", "Aprendices activos reportados por PE-04."),
    ("Total_Cancelados", "SUM ( Fact_PE04_Fichas[APRENDICES_CANCELADOS] )", "#,##0", "02 PE-04", "Derivado: matriculados menos activos (no activos / retirados)."),
    ("Total_Horas_Ejecutadas", "SUM ( Fact_PE04_Fichas[TOTAL_HORAS] )", "#,##0.0", "02 PE-04", "Suma de la intensidad horaria de las fichas (no horas-cronómetro)."),
    ("Tasa_Activos", "DIVIDE ( [Total_Activos], [Total_Matriculados] )", "0.0%", "02 PE-04", "Activos / matriculados."),
    ("Tasa_Cancelacion", "DIVIDE ( [Total_Cancelados], [Total_Matriculados] )", "0.0%", "02 PE-04", "No activos / matriculados."),
    ("Fichas_Atendidas", "DISTINCTCOUNT ( Fact_PE04_Fichas[CODIGO_FICHA] )", "#,##0", "02 PE-04", "Fichas únicas del periodo."),
    ("Promedio_Aprendices_Ficha", "DIVIDE ( [Total_Matriculados], [Fichas_Atendidas] )", "#,##0.0", "02 PE-04", "Promedio de aprendices por ficha."),
    ("Promedio_Horas_Ficha", "DIVIDE ( [Total_Horas_Ejecutadas], [Fichas_Atendidas] )", "#,##0.0", "02 PE-04", "Promedio de intensidad horaria por ficha."),
    ("Total_Aprendices_PE14", "SUM ( Fact_PE14_Aprendices[Cantidad_Aprendices] )", "#,##0", "03 PE-14", "Suma de marcaciones de población del PE-14."),
    ("Total_Poblacion_Vulnerable",
     "CALCULATE ( [Total_Aprendices_PE14], DimPoblacion[EsVulnerable] = 1 )",
     "#,##0", "03 PE-14", "Marcaciones en poblaciones vulnerables (excluye NINGUNA)."),
    ("Total_Desplazados_Violencia",
     'CALCULATE (\n    [Total_Aprendices_PE14],\n    DimPoblacion[NombrePoblacion] IN {\n        "DESPLAZADOS_POR_LA_VIOLENCIA",\n        "DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA",\n        "AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA",\n        "AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA",\n        "INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA",\n        "INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA"\n    }\n)',
     "#,##0", "03 PE-14", "Poblaciones desplazadas estrictamente por violencia (incluye variantes de cabeza de familia; excluye fenómenos naturales, discapacidad e indígenas generales)."),
    ("Fichas_Con_Caracterizacion", "DISTINCTCOUNT ( Fact_PE14_Aprendices[CODIGO_FICHA] )", "#,##0", "03 PE-14", "Fichas con registro PE-14."),
    ("Cobertura_Caracterizacion", "DIVIDE ( [Fichas_Con_Caracterizacion], [Fichas_Atendidas] )", "0.0%", "03 PE-14", "Fichas con PE-14 / fichas PE-04."),
    ("Participacion_Vulnerable", "DIVIDE ( [Total_Poblacion_Vulnerable], [Total_Aprendices_PE14] )", "0.0%", "03 PE-14", "Peso de las poblaciones vulnerables."),
    ("Poblaciones_Con_Registro",
     "CALCULATE ( DISTINCTCOUNT ( Fact_PE14_Aprendices[IdPoblacion] ), Fact_PE14_Aprendices[Cantidad_Aprendices] > 0 )",
     "#,##0", "03 PE-14", "Poblaciones con al menos un aprendiz marcado."),
    ("Brecha_PE04_PE14", "[Total_Matriculados] - [Total_Aprendices_PE14]", "#,##0;-#,##0;0", "04 Comparativo", "Control de consistencia PE-04 vs PE-14."),
    ("Cumplimiento_PE04_vs_Meta", "DIVIDE ( [Total_Matriculados], [Meta_Total] )", "0.0%", "04 Comparativo", "Matriculados PE-04 frente a la meta."),
    ("Horas_Por_Aprendiz", "DIVIDE ( [Total_Horas_Ejecutadas], [Total_Matriculados] )", "#,##0.0", "04 Comparativo", "Intensidad horaria promedio por aprendiz."),
    ("Periodo_Actual", 'FORMAT ( MAX ( DimPeriodo[IdPeriodo] ), "000000" )', None, "05 Último corte", "Último periodo visible en el contexto de filtro."),
    ("Meta_Actual", "CALCULATE ( [Meta_Total], LASTNONBLANK ( FactMetas[IdPeriodo], [Meta_Total] ) )", "#,##0", "05 Último corte", "Meta del último periodo con archivo de metas."),
    ("Ejecucion_Actual", "CALCULATE ( [Ejecucion_Total], LASTNONBLANK ( FactMetas[IdPeriodo], [Ejecucion_Total] ) )", "#,##0", "05 Último corte", "Ejecución del último periodo con archivo de metas."),
    ("Cumplimiento_Actual", "DIVIDE ( [Ejecucion_Actual], [Meta_Actual] )", "0.0%", "05 Último corte", "Cumplimiento del último corte."),
    ("Matriculados_Actual", "CALCULATE ( [Total_Matriculados], LASTNONBLANK ( Fact_PE04_Fichas[ID_PERIODO], [Total_Matriculados] ) )", "#,##0", "05 Último corte", "Matriculados del último periodo con PE-04."),
    ("Activos_Actual", "CALCULATE ( [Total_Activos], LASTNONBLANK ( Fact_PE04_Fichas[ID_PERIODO], [Total_Activos] ) )", "#,##0", "05 Último corte", "Activos del último periodo con PE-04."),
    ("Fichas_Actual", "CALCULATE ( [Fichas_Atendidas], LASTNONBLANK ( Fact_PE04_Fichas[ID_PERIODO], [Fichas_Atendidas] ) )", "#,##0", "05 Último corte", "Fichas del último periodo con PE-04."),
    ("PE14_Actual", "CALCULATE ( [Total_Aprendices_PE14], LASTNONBLANK ( Fact_PE14_Aprendices[ID_PERIODO], [Total_Aprendices_PE14] ) )", "#,##0", "05 Último corte", "Aprendices caracterizados en el último periodo con PE-14."),
    ("Desplazados_Actual", "CALCULATE ( [Total_Desplazados_Violencia], LASTNONBLANK ( Fact_PE14_Aprendices[ID_PERIODO], [Total_Desplazados_Violencia] ) )", "#,##0", "05 Último corte", "Desplazados por violencia en el último periodo con PE-14."),
    ("Brecha_Actual", "[Meta_Actual] - [Ejecucion_Actual]", "#,##0;-#,##0;0", "05 Último corte", "Brecha del último corte de metas."),
    ("Periodo_PE04", "CALCULATE ( MAX ( Fact_PE04_Fichas[ID_PERIODO] ), ALLSELECTED ( DimPeriodo ) )", "0", "05 Último corte", "Último periodo PE-04 dentro del contexto de filtro."),
    ("Periodo_PE14", "CALCULATE ( MAX ( Fact_PE14_Aprendices[ID_PERIODO] ), ALLSELECTED ( DimPeriodo ) )", "0", "05 Último corte", "Último periodo PE-14 dentro del contexto de filtro."),
    ("Matriculados_Ultimo",
     "VAR p = [Periodo_PE04]\nRETURN CALCULATE ( [Total_Matriculados], Fact_PE04_Fichas[ID_PERIODO] = p )",
     "#,##0", "05 Último corte", "Matriculados del último corte PE-04, respetando la categoría del visual."),
    ("Activos_Ultimo",
     "VAR p = [Periodo_PE04]\nRETURN CALCULATE ( [Total_Activos], Fact_PE04_Fichas[ID_PERIODO] = p )",
     "#,##0", "05 Último corte", "Activos del último corte PE-04."),
    ("Cancelados_Ultimo",
     "VAR p = [Periodo_PE04]\nRETURN CALCULATE ( [Total_Cancelados], Fact_PE04_Fichas[ID_PERIODO] = p )",
     "#,##0", "05 Último corte", "No activos del último corte PE-04."),
    ("Horas_Ultimo",
     "VAR p = [Periodo_PE04]\nRETURN CALCULATE ( [Total_Horas_Ejecutadas], Fact_PE04_Fichas[ID_PERIODO] = p )",
     "#,##0.0", "05 Último corte", "Horas del último corte PE-04."),
    ("Fichas_Ultimo",
     "VAR p = [Periodo_PE04]\nRETURN CALCULATE ( [Fichas_Atendidas], Fact_PE04_Fichas[ID_PERIODO] = p )",
     "#,##0", "05 Último corte", "Fichas del último corte PE-04."),
    ("Tasa_Activos_Ultimo", "DIVIDE ( [Activos_Ultimo], [Matriculados_Ultimo] )", "0.0%", "05 Último corte", "Tasa de activos del último corte."),
    ("PE14_Ultimo",
     "VAR p = [Periodo_PE14]\nRETURN CALCULATE ( [Total_Aprendices_PE14], Fact_PE14_Aprendices[ID_PERIODO] = p )",
     "#,##0", "05 Último corte", "Aprendices caracterizados en el último corte PE-14."),
    ("Vulnerable_Ultimo",
     "VAR p = [Periodo_PE14]\nRETURN CALCULATE ( [Total_Poblacion_Vulnerable], Fact_PE14_Aprendices[ID_PERIODO] = p )",
     "#,##0", "05 Último corte", "Población vulnerable en el último corte PE-14."),
    ("Desplazados_Ultimo",
     "VAR p = [Periodo_PE14]\nRETURN CALCULATE ( [Total_Desplazados_Violencia], Fact_PE14_Aprendices[ID_PERIODO] = p )",
     "#,##0", "05 Último corte", "Desplazados por violencia en el último corte PE-14."),
    ("Fichas_Caracterizadas_Ultimo",
     "VAR p = [Periodo_PE14]\nRETURN CALCULATE ( DISTINCTCOUNT ( Fact_PE14_Aprendices[CODIGO_FICHA] ), Fact_PE14_Aprendices[ID_PERIODO] = p )",
     "#,##0", "05 Último corte", "Fichas con PE-14 en el último corte."),
    ("Cobertura_Ultimo", "DIVIDE ( [Fichas_Caracterizadas_Ultimo], [Fichas_Ultimo] )", "0.0%", "05 Último corte", "Cobertura PE-14 / PE-04 del último corte."),
]


def esc_tmdl(texto: str) -> str:
    return texto.replace("\t", "    ")


def _utils_bindings() -> str:
    lines = (PQ / "ASTIN_Utils.m").read_text(encoding="utf-8-sig").splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == "let") + 1
    end = max(i for i, l in enumerate(lines) if l.strip() == "in" and not l.startswith((" ", "\t")))
    bindings = lines[start:end]
    while bindings and not bindings[-1].strip():
        bindings.pop()
    if bindings and not bindings[-1].rstrip().endswith(","):
        bindings[-1] = bindings[-1].rstrip() + ","
    return "\n".join(bindings)


_UTILS = _utils_bindings()


def inline_utils(code: str) -> str:
    """Reemplaza la expresión compartida ASTIN_Utils por sus funciones inline.

    Power BI Desktop no puede previsualizar una expresión que devuelve un record
    de funciones; al inlinearla el modelo carga sin errores de Mashup.Preview.
    """
    if "U = ASTIN_Utils" not in code:
        return code
    code = code.replace("    U = ASTIN_Utils,\n", _UTILS + "\n", 1)
    code = re.sub(r"U\[([A-Za-z0-9_]+)\]", r"\1", code)
    return code


def leer_m(nombre: str) -> str:
    return inline_utils((PQ / nombre).read_text(encoding="utf-8-sig").replace("\r\n", "\n").rstrip())


def m_escape_text(texto: str) -> str:
    return "".join(f"#({ord(c):04X})" if ord(c) > 127 else c for c in texto)


def escribir_modelo() -> None:
    definition = MODEL_DIR / "definition"
    tables = definition / "tables"
    tables.mkdir(parents=True, exist_ok=True)

    # database.tmdl
    (definition / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1604\n", encoding="utf-8")

    refs = "\n".join(f"ref table {t}" for t in TABLAS) + "\nref table '_Medidas_ASTIN'\n"
    model = (
        "model Model\n"
        "\tculture: es-CO\n"
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
        "\tsourceQueryCulture: en-US\n"
        "\tannotation PBI_IgnorePrivacyLevels = true\n"
        "\n"
        f"{refs}"
    )
    (definition / "model.tmdl").write_text(model, encoding="utf-8")

    # Expresiones compartidas
    expresiones = []
    for nombre, valor in RUTAS_BASE.items():
        expresiones.append(f'expression {nombre} = "{m_escape_text(valor)}"')
    for nombre, expr in RUTAS_DERIVADAS.items():
        expresiones.append(f"expression {nombre} = {expr}")
    expresiones.append("expression AnioPorDefecto = Date.Year(DateTime.LocalNow())")
    (definition / "expressions.tmdl").write_text("\n\n".join(expresiones) + "\n", encoding="utf-8")

    # Tablas
    for tabla, meta in TABLAS.items():
        lineas = [f"table {tabla}", ""]
        for col, tipo, fmt, summarize, sort_by, hidden in meta["columnas"]:
            lineas.append(f"\tcolumn {col}")
            lineas.append(f"\t\tdataType: {tipo}")
            if fmt:
                lineas.append(f"\t\tformatString: {fmt}")
            if sort_by:
                lineas.append(f"\t\tsortByColumn: {sort_by}")
            if hidden:
                lineas.append("\t\tisHidden")
            lineas.append(f"\t\tsummarizeBy: {summarize}")
            lineas.append(f"\t\tsourceColumn: {col}")
            lineas.append("")
        m = leer_m(meta["archivo"])
        lineas.append(f"\tpartition {tabla} = m")
        lineas.append("\t\tmode: import")
        lineas.append("\t\tsource =")
        for l in m.split("\n"):
            lineas.append("\t\t\t" + l if l else "")
        (tables / f"{tabla}.tmdl").write_text("\n".join(lineas).rstrip() + "\n", encoding="utf-8")

    # Tabla de medidas
    lineas = ["table '_Medidas_ASTIN'", "", "\tcolumn _", "\t\tdataType: int64", "\t\tisHidden", "\t\tsummarizeBy: none", "\t\tsourceColumn: _", ""]
    for nombre, expr, fmt, carpeta, desc in MEDIDAS:
        lineas.append(f"\tmeasure {nombre} =")
        for l in expr.split("\n"):
            lineas.append("\t\t\t" + l if l else "")
        if fmt:
            lineas.append(f"\t\tformatString: {fmt}")
        lineas.append(f"\t\tdisplayFolder: {carpeta}")
        lineas.append("")
    lineas.append("\tpartition '_Medidas_ASTIN' = calculated")
    lineas.append("\t\tmode: import")
    lineas.append('\t\tsource = ROW ( "_", 0 )')
    (tables / "_Medidas_ASTIN.tmdl").write_text("\n".join(lineas).rstrip() + "\n", encoding="utf-8")

    # Relaciones
    rel_lineas = []
    for i, (desde_t, desde_c, hacia_t, hacia_c) in enumerate(RELACIONES, 1):
        rid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"astin-rel-{i}"))
        rel_lineas += [
            f"relationship {rid}",
            f"\tfromColumn: {desde_t}.{desde_c}",
            f"\ttoColumn: {hacia_t}.{hacia_c}",
            "",
        ]
    (definition / "relationships.tmdl").write_text("\n".join(rel_lineas).rstrip() + "\n", encoding="utf-8")

    # Archivos de proyecto
    (MODEL_DIR / "definition.pbism").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0",
        "settings": {},
    }, indent=2), encoding="utf-8")
    (MODEL_DIR / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": MODEL_NAME},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid5(uuid.NAMESPACE_URL, "astin-semantic-model"))},
    }, indent=2), encoding="utf-8")


def escribir_pbip() -> None:
    pbip = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [
            {
                "report": {"path": f"{MODEL_NAME}.Report"},
            }
        ],
        "settings": {"enableAutoRecovery": True},
    }
    (BASE / f"{MODEL_NAME}.pbip").write_text(json.dumps(pbip, indent=2), encoding="utf-8")


def escribir_dax_doc() -> None:
    lineas = ["// Catálogo de medidas DAX - Sistema de control e información ASTIN", ""]
    actual = None
    for nombre, expr, fmt, carpeta, desc in MEDIDAS:
        if carpeta != actual:
            lineas += [f"// ===== {carpeta} =====", ""]
            actual = carpeta
        lineas.append(f"// {desc}")
        lineas.append(f"{nombre} =")
        for l in expr.split("\n"):
            lineas.append("    " + l)
        if fmt:
            lineas.append(f"    // formatString: {fmt}")
        lineas.append("")
    (PQ / "_Medidas_ASTIN.dax").write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    escribir_modelo()
    escribir_pbip()
    escribir_dax_doc()
    print("Modelo TMDL generado en", MODEL_DIR)
