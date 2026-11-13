# -*- coding: utf-8 -*-
"""
ETL maestro del Sistema de Control e Informacion - Estado de las metas Centro ASTIN.

Lee las tres carpetas de origen (Metas, PE-04 y PE-14), normaliza la informacion
a un modelo en estrella y genera:
  - Archivos curados mensuales (CSV) listos para Power BI.
  - Tablas consolidadas de hechos y dimensiones.
  - Un informe de calidad/auditoria en JSON.

El script es idempotente: puede ejecutarse tantas veces como sea necesario.
No modifica los archivos de origen.
"""
from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable

import openpyxl

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
BASE_PROYECTO = Path(r"C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN")
BASE_FUENTES = Path(
    r"C:\Users\capatino\OneDrive - Servicio Nacional de Aprendizaje\BACKUP DISCO\Mis proyectos\AREA LABORAL\SENA\POWER BI\Sistema de control e información - Estado de las metas centro ASTIN"
)
RUTA_METAS = BASE_FUENTES / "01_Metas"
RUTA_PE04 = BASE_FUENTES / "02_Reportes_PE04"
RUTA_PE14 = BASE_FUENTES / "03_Reportes_PE14"

DATA = BASE_PROYECTO / "data"
CURADOS = DATA / "curated"
QA = DATA / "qa"

ANIO_POR_DEFECTO = 2026

MESES = {
    "ENERO": 1, "ENE": 1,
    "FEBRERO": 2, "FEB": 2,
    "MARZO": 3, "MAR": 3,
    "ABRIL": 4, "ABR": 4,
    "MAYO": 5, "MAY": 5,
    "JUNIO": 6, "JUN": 6,
    "JULIO": 7, "JUL": 7,
    "AGOSTO": 8, "AGO": 8,
    "SEPTIEMBRE": 9, "SEP": 9, "SET": 9,
    "OCTUBRE": 10, "OCT": 10,
    "NOVIEMBRE": 11, "NOV": 11,
    "DICIEMBRE": 12, "DIC": 12,
}

NOMBRE_MES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# ---------------------------------------------------------------------------
# Utilidades de texto y numeros
# ---------------------------------------------------------------------------

def sin_acentos(texto: Any) -> str:
    if texto is None:
        return ""
    s = str(texto).replace("\n", " ").replace("\r", " ")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def norm(texto: Any) -> str:
    """Normaliza a MAYUSCULAS_CON_GUION_BAJO, sin acentos ni signos."""
    s = sin_acentos(texto).upper()
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    return s.strip("_")


def limpiar_texto(texto: Any) -> str:
    if texto is None:
        return ""
    s = str(texto).replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def a_numero(valor: Any) -> float | None:
    """Convierte valores de Excel/CSV a numero. Devuelve None para vacios y '-'."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return float(valor)
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, timedelta):
        return valor.total_seconds() / 3600.0
    if isinstance(valor, time):
        return valor.hour + valor.minute / 60 + valor.second / 3600
    s = limpiar_texto(valor)
    if s == "" or s in {"-", "--", "N/A", "NA", "N.D.", "ND"}:
        return None
    s = s.replace("%", "")
    # Formato colombiano: 1.234,56 -> 1234.56 ; 1,234.56 -> 1234.56
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def a_entero(valor: Any) -> int | None:
    n = a_numero(valor)
    if n is None:
        return None
    return int(round(n))


def a_horas(valor: Any) -> float:
    """Normaliza horas. Excel guarda [h]:mm como fraccion de dia."""
    if valor is None:
        return 0.0
    if isinstance(valor, timedelta):
        return round(valor.total_seconds() / 3600.0, 4)
    if isinstance(valor, time):
        return round(valor.hour + valor.minute / 60 + valor.second / 3600, 4)
    if isinstance(valor, (int, float)):
        # Fraccion de dia (una celda con formato [h]:mm puede superar 1)
        return round(float(valor) * 24.0, 4)
    s = limpiar_texto(valor)
    if not s or s == "-":
        return 0.0
    # Formato "1 day, 15:52:00" o "4 days, 3:57:00"
    m = re.match(r"(?:(\d+)\s*days?,\s*)?(\d{1,3}):(\d{2})(?::(\d{2}))?", s)
    if m:
        dias = int(m.group(1) or 0)
        horas = int(m.group(2))
        minutos = int(m.group(3))
        segundos = int(m.group(4) or 0)
        return round(dias * 24 + horas + minutos / 60 + segundos / 3600, 4)
    n = a_numero(valor)
    return round(n * 24.0, 4) if n is not None else 0.0


def periodo_desde_texto(*textos: Any, anio_defecto: int = ANIO_POR_DEFECTO) -> int | None:
    """Extrae YYYYMM de un texto. Acepta '202604' o 'ABRIL 2026'."""
    for texto in textos:
        if texto is None:
            continue
        if isinstance(texto, (datetime, date)):
            return texto.year * 100 + texto.month
        s = sin_acentos(texto).upper()
        m = re.search(r"(20\d{2})\s*[-/ ]?\s*(0[1-9]|1[0-2])(?![0-9])", s)
        if m:
            return int(m.group(1)) * 100 + int(m.group(2))
        m = re.search(r"\b(20\d{2})(0[1-9]|1[0-2])\b", s)
        if m:
            return int(m.group(1)) * 100 + int(m.group(2))
        m = re.search(r"(20\d{2})", s)
        anio = int(m.group(1)) if m else anio_defecto
        for token in re.findall(r"[A-Z]+", s):
            if token in MESES:
                return anio * 100 + MESES[token]
    return None


def periodo_desde_archivo(nombre: str) -> int | None:
    return periodo_desde_texto(nombre)


def periodo_valido(p: int | None) -> bool:
    return bool(p) and 200001 <= int(p) <= 209912 and 1 <= int(p) % 100 <= 12


def escribir_csv(ruta: Path, filas: Iterable[dict], columnas: list[str]) -> int:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    filas = list(filas)
    with ruta.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow({k: fila.get(k) for k in columnas})
    return len(filas)


# ---------------------------------------------------------------------------
# Dimensiones estaticas
# ---------------------------------------------------------------------------
DIM_CATEGORIA = [
    {"IdCategoria": 1, "NombreCategoria": "Formación Titulada", "Orden": 1},
    {"IdCategoria": 2, "NombreCategoria": "Formación Complementaria", "Orden": 2},
]

DIM_NIVEL = [
    {"IdNivelFormacion": 1, "NombreNivelFormacion": "Tecnólogo", "IdCategoria": 1, "Orden": 1},
    {"IdNivelFormacion": 2, "NombreNivelFormacion": "Técnico", "IdCategoria": 1, "Orden": 2},
    {"IdNivelFormacion": 3, "NombreNivelFormacion": "Operario", "IdCategoria": 1, "Orden": 3},
    {"IdNivelFormacion": 4, "NombreNivelFormacion": "Auxiliar", "IdCategoria": 1, "Orden": 4},
    {"IdNivelFormacion": 5, "NombreNivelFormacion": "Formación Complementaria", "IdCategoria": 2, "Orden": 5},
    {"IdNivelFormacion": 6, "NombreNivelFormacion": "Bilingüismo", "IdCategoria": 2, "Orden": 6},
    {"IdNivelFormacion": 7, "NombreNivelFormacion": "Formación Especial Campesina", "IdCategoria": 2, "Orden": 7},
]

DIM_ESTRATEGIA = [
    {"IdEstrategia": 1, "NombreEstrategia": "Regular", "Orden": 1},
    {"IdEstrategia": 2, "NombreEstrategia": "Presencial", "Orden": 2},
    {"IdEstrategia": 3, "NombreEstrategia": "Virtual", "Orden": 3},
    {"IdEstrategia": 4, "NombreEstrategia": "A Distancia", "Orden": 4},
    {"IdEstrategia": 5, "NombreEstrategia": "CampeSENA", "Orden": 5},
    {"IdEstrategia": 6, "NombreEstrategia": "Full Popular", "Orden": 6},
    {"IdEstrategia": 7, "NombreEstrategia": "FIC", "Orden": 7},
    {"IdEstrategia": 8, "NombreEstrategia": "Articulación con la Media", "Orden": 8},
    {"IdEstrategia": 9, "NombreEstrategia": "Especial", "Orden": 9},
]

DIM_CENTRO = [
    {
        "IdCentro": 9230,
        "NombreCentro": "Centro Nacional de Asistencia Técnica a la Industria - ASTIN",
        "NombreRegional": "Regional Valle",
        "CodigoRegional": 76,
    }
]

# Nombre normalizado -> (nombre amigable, grupo, es_vulnerable, es_desplazamiento_violencia)
POBLACIONES_INFO: dict[str, tuple[str, str, bool, bool]] = {
    "INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA": ("Indígenas desplazados por la violencia", "Víctimas del conflicto", True, True),
    "INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA": ("Indígenas desplazados por la violencia - Cabeza de familia", "Víctimas del conflicto", True, True),
    "AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA": ("Afrocolombianos desplazados por la violencia", "Víctimas del conflicto", True, True),
    "AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA": ("Afrocolombianos desplazados por la violencia - Cabeza de familia", "Víctimas del conflicto", True, True),
    "DESPLAZADOS_POR_LA_VIOLENCIA": ("Desplazados por la violencia", "Víctimas del conflicto", True, True),
    "DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA": ("Desplazados por la violencia - Cabeza de familia", "Víctimas del conflicto", True, True),
    "DESPLAZADOS_DISCAPACITADOS": ("Desplazados discapacitados", "Discapacidad", True, True),
    "DESPOJO": ("Despojo", "Víctimas del conflicto", True, False),
    "ACTOS_DE_GRUPOS_ARMADOS": ("Actos de grupos armados", "Víctimas del conflicto", True, False),
    "AMENAZA": ("Amenaza", "Víctimas del conflicto", True, False),
    "DELITOS_SEXUALES": ("Delitos sexuales", "Víctimas del conflicto", True, False),
    "DESAPARICION_FORZADA": ("Desaparición forzada", "Víctimas del conflicto", True, False),
    "HOMICIDIO_MASACRE": ("Homicidio / masacre", "Víctimas del conflicto", True, False),
    "MINAS_ANTIPERSONALES_Y_EXPLOSIVOS": ("Minas antipersonales y explosivos", "Víctimas del conflicto", True, False),
    "SECUESTRO": ("Secuestro", "Víctimas del conflicto", True, False),
    "TORTURA": ("Tortura", "Víctimas del conflicto", True, False),
    "USO_DE_MENORES_POR_GRUPOS_ARMADOS": ("Uso de menores por grupos armados", "Víctimas del conflicto", True, False),
    "HERIDO": ("Herido", "Víctimas del conflicto", True, False),
    "RECLUTAMIENTO_FORZADO": ("Reclutamiento forzado", "Víctimas del conflicto", True, False),
    "NEGRO": ("Negro", "Étnicas", True, False),
    "AFROCOLOMBIANOS": ("Afrocolombianos", "Étnicas", True, False),
    "PALENQUEROS": ("Palenqueros", "Étnicas", True, False),
    "RAIZALES": ("Raizales", "Étnicas", True, False),
    "DISCAPACIDAD": ("Discapacidad", "Discapacidad", True, False),
    "DISCAPACIDAD_AUDITIVA": ("Discapacidad auditiva", "Discapacidad", True, False),
    "DISCAPACIDAD_VISUAL": ("Discapacidad visual", "Discapacidad", True, False),
    "DISCAPACIDAD_FISICA": ("Discapacidad física", "Discapacidad", True, False),
    "DISCAPACIDAD_INTELECTUAL": ("Discapacidad intelectual", "Discapacidad", True, False),
    "DISCAPACIDAD_PSICOSOCIAL": ("Discapacidad psicosocial", "Discapacidad", True, False),
    "DISCAPACIDAD_MULTIPLE": ("Discapacidad múltiple", "Discapacidad", True, False),
    "SORDOCEGUERA": ("Sordoceguera", "Discapacidad", True, False),
    "DESPLAZADOS_POR_FENOMENOS_NATURALES": ("Desplazados por fenómenos naturales", "Víctimas del conflicto", True, True),
    "DESPLAZADOS_POR_FENOMENOS_NATURALES_CABEZA_DE_FAMILIA": ("Desplazados por fenómenos naturales - Cabeza de familia", "Víctimas del conflicto", True, True),
    "ADOLESCENTE_EN_CONFLICTO_CON_LA_LEY_PENAL": ("Adolescente en conflicto con la ley penal", "Víctimas del conflicto", True, False),
    "ADOLESCENTE_TRABAJADOR": ("Adolescente trabajador", "Otras poblaciones", True, False),
    "INDIGENAS": ("Indígenas", "Étnicas", True, True),
    "INPEC": ("INPEC", "Víctimas del conflicto", True, False),
    "JOVENES_VULNERABLES": ("Jóvenes vulnerables", "Otras poblaciones", True, False),
    "MUJER_CABEZA_DE_FAMILIA": ("Mujer cabeza de familia", "Otras poblaciones", True, False),
    "PROC_REINTEGRACION": ("Proceso de reintegración", "Víctimas del conflicto", True, False),
    "ADOLESCENTE_DESVINCULADO_DE_GRUPOS_ARMADOS_ORGANIZADOS_AL_MARGEN_DE_LA_LEY": ("Adolescente desvinculado de grupos armados al margen de la ley", "Víctimas del conflicto", True, False),
    "REMITIDOS_POR_EL_PAL": ("Remitidos por el PAL", "Víctimas del conflicto", True, False),
    "SOBREVIVIENTES_MINAS_ANTIPERSONALES": ("Sobrevivientes de minas antipersonales", "Víctimas del conflicto", True, False),
    "SOLDADOS_CAMPESINOS": ("Soldados campesinos", "Víctimas del conflicto", True, False),
    "TERCERA_EDAD": ("Tercera edad", "Otras poblaciones", True, False),
    "ROM": ("ROM", "Étnicas", True, False),
    "CAMPESINOS": ("Campesinos", "Étnicas", True, False),
    "NINGUNA": ("Ninguna", "Sin vulnerabilidad", False, False),
    "ARTESANOS": ("Artesanos", "Otras poblaciones", True, False),
    "EMPRENDEDORES": ("Emprendedores", "Otras poblaciones", True, False),
    "MICROEMPRESAS": ("Microempresas", "Otras poblaciones", True, False),
    "REMITIDOS_POR_EL_CIE": ("Remitidos por el CIE", "Víctimas del conflicto", True, False),
}

# Orden estable de poblaciones (el que aparece en el reporte PE-14)
ORDEN_POBLACIONES = list(POBLACIONES_INFO.keys())

POBLACION_ID = {nombre: i + 1 for i, nombre in enumerate(ORDEN_POBLACIONES)}

# Lista exacta solicitada en la especificacion para el measure de desplazados.
POBLACIONES_DESPLAZADOS_VIOLENCIA = [
    "DESPLAZADOS_DISCAPACITADOS",
    "DESPLAZADOS_POR_FENOMENOS_NATURALES",
    "DESPLAZADOS_POR_FENOMENOS_NATURALES_CABEZA_DE_FAMILIA",
    "DESPLAZADOS_POR_LA_VIOLENCIA",
    "AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA",
    "AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA",
    "INDIGENAS",
    "INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA",
]


# ---------------------------------------------------------------------------
# 01_Metas: parser de layouts heterogeneos
# ---------------------------------------------------------------------------

def _etiqueta_es_agregado(label: str) -> bool:
    n = norm(label)
    if not n:
        return True
    if n.startswith("TOTAL"):
        return True
    if " = (" in label or re.search(r"\)\s*=\s*\(", label):
        return True
    if n.startswith("FORMACION_TECNOLOGICA"):
        return True
    if n.startswith("FORMACION_TITULADA"):
        return True
    if n.startswith("FORMACION_OCUPACIONAL"):
        return True
    if n.startswith("FORMACION_PROFESIONAL"):
        return True
    if n.startswith("FORMACION_COMPLEMENTARIA_ESTRATEGIA"):
        return True
    if n.startswith("FORMACION_COMPLEMENTARIA_TOTAL"):
        return True
    if n.startswith("FORMACION_ESPECIAL_CAMPESINA"):
        return True
    if n.startswith("EDUCACION_SUPERIOR"):
        return True
    if n.startswith("CERTIFICACION"):
        return True
    if n.startswith("RETENCION"):
        return True
    if n.startswith("APRENDICES_DE_PRIMER_CURSO"):
        return True
    if n.startswith("METAS_PROGRAMAS"):
        return True
    if n in {"FORMACION_COMPLEMENTARIA", "PROGRAMA_DE_BILINGUISMO", "FORMACION_OCUPACIONAL"}:
        return True
    return False


def _nivel_desde_etiqueta(label: str) -> int | None:
    n = norm(label)
    if "TECNOLOG" in n:
        return 1
    if "TECNICO" in n:
        return 2
    if "OPERARIO" in n:
        return 3
    if "AUXILIAR" in n:
        return 4
    if "BILINGU" in n and "SIN_BILINGUISMO" not in n:
        return 6
    if "PLACA_HUELLA" in n or "OTROS_PROGRAMAS_FEC" in n:
        return 7
    if "COMPLEMENTARIA" in n or "FORMACION_ESPECIAL_POPULAR" in n or n.startswith("FEP"):
        return 5
    return None


def _estrategia_desde_etiqueta(label: str) -> int:
    n = norm(label)
    if "ARTICULACION" in n:
        return 8
    if "CAMPESENA" in n:
        return 5
    if "FULL_POPULAR" in n or n.startswith("FEP") or "FORMACION_ESPECIAL_POPULAR" in n:
        return 6
    if re.search(r"\bFIC\b", n) or n.endswith("_FIC"):
        return 7
    if "A_DISTANCIA" in n and "PRESENCIAL" not in n:
        return 4
    if "VIRTUAL" in n:
        return 3
    if "PRESENCIAL" in n:
        return 2
    return 1


def _buscar_fila_encabezado(filas: list[tuple], max_filas: int = 40) -> int | None:
    """Encuentra la fila de encabezado de la tabla principal de metas."""
    for i, fila in enumerate(filas[:max_filas]):
        c1 = norm(fila[0] if len(fila) > 0 else "")
        c2 = norm(fila[1] if len(fila) > 1 else "")
        c3 = norm(fila[2] if len(fila) > 2 else "")
        if c1 == "INDICADOR" and c2.startswith("META") and c3.startswith("EJECUCION"):
            return i
        if c1.startswith("METAS_FORMACION_PROFESIONAL") and c2 == "META" and c3.startswith("EJECUCION"):
            return i
    return None


def _fin_bloque_principal(filas: list[tuple], inicio: int) -> int:
    for i in range(inicio + 1, len(filas)):
        c1 = norm(filas[i][0] if len(filas[i]) > 0 else "")
        if c1.startswith("RETENCION") or c1.startswith("METAS_PROGRAMAS_RELEVANTES"):
            return i
    return len(filas)


def _control_oficial(filas: list[tuple], es_moderno: bool) -> tuple[float | None, float | None, str]:
    """Obtiene la meta/ejecucion oficial total del archivo (solo control)."""
    if not es_moderno:
        for fila in filas:
            c1 = norm(fila[0] if len(fila) > 0 else "")
            if c1.startswith("TOTAL_FORMACION_PROFESIONAL_INTEGRAL"):
                return a_numero(fila[1] if len(fila) > 1 else None), a_numero(fila[2] if len(fila) > 2 else None), "Fila TOTAL FORMACIÓN PROFESIONAL INTEGRAL"
    # Layout moderno: resumen superior "Meta | 31733" y "Ejecución | 25281"
    meta = ejec = None
    for fila in filas[:10]:
        etiqueta = limpiar_texto(fila[0] if len(fila) > 0 else "")
        c1 = norm(etiqueta)
        if etiqueta.replace(" ", "").startswith("%"):
            continue
        if c1 == "META":
            meta = a_numero(fila[1] if len(fila) > 1 else None)
        elif c1 == "EJECUCION":
            ejec = a_numero(fila[1] if len(fila) > 1 else None)
    if meta is not None or ejec is not None:
        return meta, ejec, "Resumen superior del archivo"
    # Ultimo recurso: sumar total titulada + total complementaria
    for fila in filas:
        c1 = norm(fila[0] if len(fila) > 0 else "")
        if c1 == "TOTAL_TECNOLOGICA_Y_OCUPACIONAL":
            meta_t = a_numero(fila[1] if len(fila) > 1 else None)
            ejec_t = a_numero(fila[2] if len(fila) > 2 else None)
            for f2 in filas:
                c2 = norm(f2[0] if len(f2) > 0 else "")
                if c2.startswith("TOTAL_FORMACION_COMPLEMENTARIA"):
                    meta_c = a_numero(f2[1] if len(f2) > 1 else None)
                    ejec_c = a_numero(f2[2] if len(f2) > 2 else None)
                    if meta_t is not None and meta_c is not None:
                        return meta_t + meta_c, (ejec_t or 0) + (ejec_c or 0), "Suma titulada + complementaria"
    return None, None, ""


def _leer_hoja_metas(ws, ruta: Path, periodo: int, dia_corte: int) -> tuple[list[dict], dict | None, list[str]]:
    filas = [list(r) + [None] * 8 for r in ws.iter_rows(values_only=True)]
    incidencias: list[str] = []
    idx = _buscar_fila_encabezado(filas)
    if idx is None:
        return [], None, ["Sin encabezado de tabla principal"]

    encabezado = [norm(x) for x in filas[idx][:5]]
    es_moderno = encabezado[0] == "INDICADOR"
    fin = _fin_bloque_principal(filas, idx)
    meta_of, ejec_of, fuente_of = _control_oficial(filas, es_moderno)
    control = None
    if meta_of is not None or ejec_of is not None:
        control = {
            "IdPeriodo": periodo,
            "Meta_Oficial": meta_of,
            "Ejecucion_Oficial": ejec_of,
            "Fuente": fuente_of,
            "OrigenArchivo": ruta.name,
            "Hoja": ws.title,
            "DiaCorte": dia_corte,
        }

    hechos: list[dict] = []
    vistos: set[str] = set()
    for fila in filas[idx + 1:fin]:
        label = limpiar_texto(fila[0] if len(fila) > 0 else "")
        if not label:
            continue
        meta = a_numero(fila[1] if len(fila) > 1 else None)
        ejec = a_numero(fila[2] if len(fila) > 2 else None)
        if meta is None and ejec is None:
            continue
        # Encabezados repetidos dentro del archivo (p. ej. "Formación Regular sin Bilingüismo")
        if norm(fila[1] if len(fila) > 1 else "").startswith("META") and norm(fila[2] if len(fila) > 2 else "").startswith("EJECUCION"):
            continue
        if _etiqueta_es_agregado(label):
            continue
        nivel = _nivel_desde_etiqueta(label)
        if nivel is None:
            incidencias.append(f"Etiqueta no clasificada: {label}")
            continue
        clave = norm(label)
        if clave in vistos:
            continue
        vistos.add(clave)
        hechos.append({
            "IdPeriodo": periodo,
            "IdCentro": 9230,
            "IdCategoria": 1 if nivel <= 4 else 2,
            "IdNivelFormacion": nivel,
            "IdEstrategia": _estrategia_desde_etiqueta(label),
            "Indicador": label,
            "Indicador_Normalizado": clave,
            "Meta": int(round(meta)) if meta is not None else 0,
            "Ejecucion": int(round(ejec)) if ejec is not None else 0,
            "OrigenArchivo": ruta.name,
            "Hoja": ws.title,
            "DiaCorte": dia_corte,
        })
    return hechos, control, incidencias


def leer_metas() -> tuple[list[dict], list[dict], list[dict]]:
    hechos: list[dict] = []
    controles: list[dict] = []
    auditoria: list[dict] = []
    archivos = sorted([p for p in RUTA_METAS.iterdir() if p.is_file() and p.suffix.lower() in {".xlsx", ".xlsm", ".xls", ".csv"} and not p.name.startswith("~$")])
    for ruta in archivos:
        periodo = periodo_desde_archivo(ruta.name)
        incidencias: list[str] = []
        if ruta.suffix.lower() == ".csv":
            # Los CSV de metas deben venir curados; se leen con el mismo contrato.
            incidencias.append("CSV de metas: se espera esquema curado (ver powerquery/FactMetas.m)")
            auditoria.append({
                "Origen": "01_Metas", "Archivo": ruta.name, "Periodo": periodo, "Hoja": "",
                "Filas": 0, "Estado": "OMITIDO", "Detalle": "CSV crudo no soportado en el ETL Python; use la consulta M o un archivo curado.",
            })
            continue
        try:
            wb = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
        except Exception as e:  # pragma: no cover
            auditoria.append({"Origen": "01_Metas", "Archivo": ruta.name, "Periodo": periodo, "Hoja": "", "Filas": 0, "Estado": "ERROR", "Detalle": str(e)})
            continue

        # Un archivo puede tener varios cortes (p. ej. 20 y 30 de abril).
        # Se conserva el corte mas reciente de cada periodo.
        candidatos: list[tuple[int, Any, list[dict], dict | None, list[str]]] = []
        for ws in wb.worksheets:
            dias = [int(x) for x in re.findall(r"\b(\d{1,2})\b", ws.title)]
            dia = max(dias) if dias else 0
            filas, control, inc = _leer_hoja_metas(ws, ruta, periodo or 0, dia)
            if filas or control:
                candidatos.append((dia, ws, filas, control, inc))
        wb.close()

        if not candidatos:
            auditoria.append({
                "Origen": "01_Metas", "Archivo": ruta.name, "Periodo": periodo, "Hoja": "",
                "Filas": 0, "Estado": "OMITIDO",
                "Detalle": "Layout no reconocido o archivo sin periodo (p. ej. matriz anual de metas).",
            })
            continue
        dia, ws, filas, control, inc = max(candidatos, key=lambda x: x[0])
        incidencias.extend(inc)
        if not periodo:
            auditoria.append({"Origen": "01_Metas", "Archivo": ruta.name, "Periodo": None, "Hoja": ws.title, "Filas": len(filas), "Estado": "OMITIDO", "Detalle": "No se pudo determinar el periodo."})
            continue
        for h in filas:
            h["IdPeriodo"] = periodo
        if control:
            control["IdPeriodo"] = periodo
            controles.append(control)
        hechos.extend(filas)
        auditoria.append({
            "Origen": "01_Metas", "Archivo": ruta.name, "Periodo": periodo, "Hoja": ws.title,
            "Filas": len(filas), "Estado": "OK" if filas else "SIN HECHOS",
            "Detalle": f"Corte día {dia}. " + ("; ".join(incidencias[:4]) if incidencias else "Layout reconocido."),
        })

    # Deduplicar por periodo + indicador normalizado, conservando el corte mas reciente.
    unicos: dict[tuple, dict] = {}
    for h in hechos:
        k = (h["IdPeriodo"], h["Indicador_Normalizado"])
        prev = unicos.get(k)
        if prev is None or h.get("DiaCorte", 0) >= prev.get("DiaCorte", 0):
            unicos[k] = h
    hechos = sorted(unicos.values(), key=lambda x: (x["IdPeriodo"], x["IdNivelFormacion"], x["IdEstrategia"], x["Indicador"]))
    return hechos, controles, auditoria


# ---------------------------------------------------------------------------
# 02_Reportes_PE04: xlsx y SpreadsheetML (.xml)
# ---------------------------------------------------------------------------

def _fila_pe04_desde_dict(d: dict, periodo: int, archivo: str) -> dict | None:
    ficha = a_entero(d.get("IDENTIFICADOR_FICHA"))
    if ficha is None:
        return None
    mat = a_entero(d.get("TOTAL_APRENDICES")) or 0
    act = a_entero(d.get("TOTAL_APRENDICES_ACTIVOS"))
    act = mat if act is None else act
    cancelados = max(mat - act, 0)
    return {
        "ID_REGISTRO_UUID": f"{periodo}-{ficha}",
        "ID_PERIODO": periodo,
        "CODIGO_FICHA": ficha,
        "NOMBRE_PROGRAMA": limpiar_texto(d.get("NOMBRE_PROGRAMA_FORMACION")),
        "CODIGO_JORNADA": a_entero(d.get("CODIGO_JORNADA")) or 0,
        "NOMBRE_JORNADA": limpiar_texto(d.get("NOMBRE_JORNADA")),
        "MODALIDAD_FORMACION": limpiar_texto(d.get("MODALIDAD_FORMACION")),
        "ESTADO_CURSO": limpiar_texto(d.get("ESTADO_CURSO")),
        "NIVEL_FORMACION": limpiar_texto(d.get("NIVEL_FORMACION")),
        "APRENDICES_MATRICULADOS": mat,
        "APRENDICES_ACTIVOS": act,
        "APRENDICES_CANCELADOS": cancelados,
        "TOTAL_HORAS": round(a_horas(d.get("TOTAL_HORAS")), 4),
        "IdCentro": a_entero(d.get("CODIGO_CENTRO")) or 9230,
        "ORIGEN_ARCHIVO": archivo,
    }


def _leer_pe04_xlsx(ruta: Path) -> tuple[int | None, list[dict], str]:
    wb = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    filas = list(ws.iter_rows(values_only=True))
    wb.close()
    periodo = None
    for fila in filas[:6]:
        for valor in fila[:3]:
            p = periodo_desde_texto(valor)
            if p and 1 <= p % 100 <= 12:
                periodo = p
                break
        if periodo:
            break
    periodo = periodo or periodo_desde_archivo(ruta.name)

    idx = None
    for i, fila in enumerate(filas[:20]):
        valores = [norm(v) for v in fila]
        if "CODIGO_REGIONAL" in valores and "IDENTIFICADOR_FICHA" in valores:
            idx = i
            break
    if idx is None or periodo is None:
        return periodo, [], "No se encontró encabezado o periodo."

    encabezado = [limpiar_texto(v) for v in filas[idx]]
    hechos = []
    for fila in filas[idx + 1:]:
        d = {encabezado[j]: fila[j] for j in range(min(len(encabezado), len(fila))) if encabezado[j]}
        h = _fila_pe04_desde_dict(d, periodo, ruta.name)
        if h:
            hechos.append(h)
    return periodo, hechos, ""


def _leer_pe04_xml(ruta: Path) -> tuple[int | None, list[dict], str]:
    """Lee SpreadsheetML 2003 (exportaciones SSRS/Excel XML)."""
    import xml.etree.ElementTree as ET

    NS = "urn:schemas-microsoft-com:office:spreadsheet"
    ns = {"ss": NS}
    root = ET.parse(ruta).getroot()
    ws = root.find("ss:Worksheet", ns)
    if ws is None:
        return None, [], "XML sin Worksheet."
    table = ws.find("ss:Table", ns)
    if table is None:
        return None, [], "XML sin Table."
    rows = table.findall("ss:Row", ns)

    def celdas(row) -> list[str]:
        out: list[str] = []
        for c in row.findall("ss:Cell", ns):
            idx = c.get(f"{{{NS}}}Index")
            if idx:
                objetivo = int(idx) - 1
                while len(out) < objetivo:
                    out.append("")
            d = c.find("ss:Data", ns)
            out.append("".join(d.itertext()) if d is not None else "")
        return out

    matriz = [celdas(r) for r in rows]
    periodo = None
    for fila in matriz[:6]:
        for v in fila[:3]:
            p = periodo_desde_texto(v)
            if p and 1 <= p % 100 <= 12:
                periodo = p
                break
        if periodo:
            break
    periodo = periodo or periodo_desde_archivo(ruta.name)

    idx = None
    for i, fila in enumerate(matriz[:20]):
        valores = {norm(v) for v in fila}
        if "CODIGO_REGIONAL" in valores and "IDENTIFICADOR_FICHA" in valores:
            idx = i
            break
    if idx is None or periodo is None:
        return periodo, [], "No se encontró encabezado o periodo."

    encabezado = [limpiar_texto(v) for v in matriz[idx]]
    hechos = []
    for fila in matriz[idx + 1:]:
        d = {encabezado[j]: fila[j] for j in range(min(len(encabezado), len(fila))) if encabezado[j]}
        # En SpreadsheetML las horas vienen como fecha ISO; se convierten aparte.
        horas_txt = d.get("TOTAL_HORAS")
        h = _fila_pe04_desde_dict(d, periodo, ruta.name)
        if h and isinstance(horas_txt, str) and "T" in horas_txt:
            try:
                dt = datetime.fromisoformat(horas_txt)
                h["TOTAL_HORAS"] = round((dt - datetime(1899, 12, 31)).total_seconds() / 3600, 4)
            except ValueError:
                pass
        if h:
            hechos.append(h)
    return periodo, hechos, ""


def leer_pe04() -> tuple[list[dict], list[dict]]:
    hechos: list[dict] = []
    auditoria: list[dict] = []
    archivos = sorted([p for p in RUTA_PE04.iterdir() if p.is_file() and p.suffix.lower() in {".xlsx", ".xlsm", ".xls", ".xml"} and not p.name.startswith("~$")])
    for ruta in archivos:
        try:
            if ruta.suffix.lower() == ".xml":
                periodo, filas, detalle = _leer_pe04_xml(ruta)
            else:
                periodo, filas, detalle = _leer_pe04_xlsx(ruta)
        except Exception as e:  # pragma: no cover
            auditoria.append({"Origen": "02_Reportes_PE04", "Archivo": ruta.name, "Periodo": None, "Filas": 0, "Estado": "ERROR", "Detalle": str(e)})
            continue
        if periodo and filas:
            # Eliminar duplicados exactos de ficha dentro del mismo archivo.
            unicos = {f["CODIGO_FICHA"]: f for f in filas}
            filas = list(unicos.values())
            hechos.extend(filas)
            auditoria.append({"Origen": "02_Reportes_PE04", "Archivo": ruta.name, "Periodo": periodo, "Filas": len(filas), "Estado": "OK", "Detalle": detalle or "Procesado."})
        else:
            auditoria.append({"Origen": "02_Reportes_PE04", "Archivo": ruta.name, "Periodo": periodo, "Filas": 0, "Estado": "OMITIDO", "Detalle": detalle or "Sin datos."})
    unicos = {h["ID_REGISTRO_UUID"]: h for h in hechos}
    hechos = list(unicos.values())
    hechos.sort(key=lambda x: (x["ID_PERIODO"], x["CODIGO_FICHA"]))
    return hechos, auditoria


# ---------------------------------------------------------------------------
# 03_Reportes_PE14: unpivot de poblaciones
# ---------------------------------------------------------------------------

def _poblacion_desde_encabezado(header: Any) -> str | None:
    n = norm(header)
    if not n.endswith("_TOTAL_APRENDICES") or n == "GRAN_TOTAL_APRENDICES":
        return None
    n = n[: -len("_TOTAL_APRENDICES")]
    n = re.sub(r"_+", "_", n).strip("_")
    return n or None


def leer_pe14() -> tuple[list[dict], list[dict], dict[str, int]]:
    hechos: list[dict] = []
    auditoria: list[dict] = []
    poblaciones_nuevas: dict[str, int] = {}
    archivos = sorted([p for p in RUTA_PE14.iterdir() if p.is_file() and p.suffix.lower() in {".xlsx", ".xlsm", ".xls", ".csv"} and not p.name.startswith("~$")])
    for ruta in archivos:
        if ruta.suffix.lower() == ".csv":
            auditoria.append({"Origen": "03_Reportes_PE14", "Archivo": ruta.name, "Periodo": periodo_desde_archivo(ruta.name), "Filas": 0, "Estado": "OMITIDO", "Detalle": "CSV crudo: use el esquema curado pe14_curated_YYYY_MM.csv."})
            continue
        try:
            wb = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
        except Exception as e:  # pragma: no cover
            auditoria.append({"Origen": "03_Reportes_PE14", "Archivo": ruta.name, "Periodo": None, "Filas": 0, "Estado": "ERROR", "Detalle": str(e)})
            continue
        ws = wb.worksheets[0]
        filas = list(ws.iter_rows(values_only=True))
        wb.close()
        periodo = None
        for fila in filas[:6]:
            for v in fila[:3]:
                p = periodo_desde_texto(v)
                if p and 1 <= p % 100 <= 12:
                    periodo = p
                    break
            if periodo:
                break
        periodo = periodo or periodo_desde_archivo(ruta.name)
        idx = None
        for i, fila in enumerate(filas[:20]):
            valores = {norm(v) for v in fila}
            if "IDENTIFICADOR_FICHA" in valores and "CODIGO_REGIONAL" in valores:
                idx = i
                break
        if idx is None or periodo is None:
            auditoria.append({"Origen": "03_Reportes_PE14", "Archivo": ruta.name, "Periodo": periodo, "Filas": 0, "Estado": "OMITIDO", "Detalle": "Sin encabezado o periodo."})
            continue
        encabezado = [limpiar_texto(v) for v in filas[idx]]
        indice = {norm(h): j for j, h in enumerate(encabezado) if h}
        col_poblaciones = []
        mapa_nombres = {}
        for j, h in enumerate(encabezado):
            pob = _poblacion_desde_encabezado(h)
            if pob:
                col_poblaciones.append((j, pob))
                mapa_nombres[pob] = h
        if not col_poblaciones:
            auditoria.append({"Origen": "03_Reportes_PE14", "Archivo": ruta.name, "Periodo": periodo, "Filas": 0, "Estado": "OMITIDO", "Detalle": "No se encontraron columnas Total_Aprendices."})
            continue

        j_ficha = indice.get("IDENTIFICADOR_FICHA")
        j_centro = indice.get("CODIGO_CENTRO")
        j_programa = indice.get("NOMBRE_PROGRAMA_FORMACION")
        j_nivel = indice.get("NIVEL_FORMACION")
        j_jornada = indice.get("NOMBRE_JORNADA")
        n_antes = len(hechos)
        for fila in filas[idx + 1:]:
            if j_ficha is None or j_ficha >= len(fila):
                continue
            ficha = a_entero(fila[j_ficha])
            if ficha is None:
                continue
            centro = a_entero(fila[j_centro]) if j_centro is not None and j_centro < len(fila) else 9230
            for j, pob in col_poblaciones:
                cant = a_entero(fila[j]) if j < len(fila) else 0
                cant = cant or 0
                if pob not in POBLACION_ID:
                    nuevo_id = max(POBLACION_ID.values(), default=0) + 1
                    POBLACION_ID[pob] = nuevo_id
                    POBLACIONES_INFO[pob] = (pob.replace("_", " ").title(), "Otras poblaciones", True, False)
                    ORDEN_POBLACIONES.append(pob)
                    poblaciones_nuevas[pob] = nuevo_id
                hechos.append({
                    "ID_REGISTRO_UUID": f"{periodo}-{ficha}-{POBLACION_ID[pob]}",
                    "ID_PERIODO": periodo,
                    "IdCentro": centro or 9230,
                    "CODIGO_FICHA": ficha,
                    "IdPoblacion": POBLACION_ID[pob],
                    "NombrePoblacion": pob,
                    "Cantidad_Aprendices": cant,
                    "NOMBRE_PROGRAMA": limpiar_texto(fila[j_programa]) if j_programa is not None and j_programa < len(fila) else "",
                    "NIVEL_FORMACION": limpiar_texto(fila[j_nivel]) if j_nivel is not None and j_nivel < len(fila) else "",
                    "NOMBRE_JORNADA": limpiar_texto(fila[j_jornada]) if j_jornada is not None and j_jornada < len(fila) else "",
                    "ORIGEN_ARCHIVO": ruta.name,
                })
        auditoria.append({"Origen": "03_Reportes_PE14", "Archivo": ruta.name, "Periodo": periodo, "Filas": len(hechos) - n_antes, "Estado": "OK", "Detalle": f"{len(col_poblaciones)} poblaciones desdinamizadas."})
    unicos = {h["ID_REGISTRO_UUID"]: h for h in hechos}
    hechos = list(unicos.values())
    hechos.sort(key=lambda x: (x["ID_PERIODO"], x["CODIGO_FICHA"], x["IdPoblacion"]))
    return hechos, auditoria, poblaciones_nuevas


# ---------------------------------------------------------------------------
# Dimensiones derivadas y control de calidad
# ---------------------------------------------------------------------------

def construir_dim_periodo(periodos: Iterable[int]) -> list[dict]:
    import calendar

    periodos = sorted({int(p) for p in periodos if periodo_valido(p)})
    anios = {p // 100 for p in periodos} or {ANIO_POR_DEFECTO}
    if ANIO_POR_DEFECTO not in anios:
        anios.add(ANIO_POR_DEFECTO)
    filas = []
    for anio in sorted(anios):
        for mes in range(1, 13):
            ultimo = calendar.monthrange(anio, mes)[1]
            filas.append({
                "IdPeriodo": anio * 100 + mes,
                "Anio": anio,
                "Mes": mes,
                "NombreMes": NOMBRE_MES[mes],
                "Trimestre": (mes - 1) // 3 + 1,
                "FechaInicio": date(anio, mes, 1).isoformat(),
                "FechaFin": date(anio, mes, ultimo).isoformat(),
                "PeriodoTexto": f"{NOMBRE_MES[mes]} {anio}",
                "OrdenAnual": mes,
            })
    return filas


def construir_dim_ficha(pe04: list[dict], pe14: list[dict]) -> list[dict]:
    fichas: dict[int, dict] = {}
    for h in sorted(pe04, key=lambda x: x["ID_PERIODO"]):
        fichas[h["CODIGO_FICHA"]] = {
            "CODIGO_FICHA": h["CODIGO_FICHA"],
            "NOMBRE_PROGRAMA": h["NOMBRE_PROGRAMA"],
            "CODIGO_JORNADA": h["CODIGO_JORNADA"],
            "NOMBRE_JORNADA": h["NOMBRE_JORNADA"],
            "MODALIDAD_FORMACION": h["MODALIDAD_FORMACION"],
            "NIVEL_FORMACION": h.get("NIVEL_FORMACION", ""),
            "IdCentro": h["IdCentro"],
            "UltimoPeriodo": h["ID_PERIODO"],
        }
    for h in sorted(pe14, key=lambda x: x["ID_PERIODO"]):
        if h["CODIGO_FICHA"] not in fichas and h.get("NOMBRE_PROGRAMA"):
            fichas[h["CODIGO_FICHA"]] = {
                "CODIGO_FICHA": h["CODIGO_FICHA"],
                "NOMBRE_PROGRAMA": h.get("NOMBRE_PROGRAMA", ""),
                "CODIGO_JORNADA": 0,
                "NOMBRE_JORNADA": h.get("NOMBRE_JORNADA", ""),
                "MODALIDAD_FORMACION": "",
                "NIVEL_FORMACION": h.get("NIVEL_FORMACION", ""),
                "IdCentro": h.get("IdCentro", 9230),
                "UltimoPeriodo": h["ID_PERIODO"],
            }
    return sorted(fichas.values(), key=lambda x: x["CODIGO_FICHA"])


def construir_dim_poblacion() -> list[dict]:
    filas = []
    for i, nombre in enumerate(ORDEN_POBLACIONES, 1):
        amigable, grupo, vulnerable, desplazado = POBLACIONES_INFO[nombre]
        filas.append({
            "IdPoblacion": POBLACION_ID[nombre],
            "NombrePoblacion": nombre,
            "NombreAmigable": amigable,
            "GrupoPoblacional": grupo,
            "EsVulnerable": 1 if vulnerable else 0,
            "EsDesplazamientoViolencia": 1 if desplazado else 0,
            "Orden": i,
        })
    return filas


def calcular_qa(metas: list[dict], controles: list[dict], pe04: list[dict], pe14: list[dict], dim_ficha: list[dict], auditoria: list[dict]) -> dict:
    metas_por_periodo = defaultdict(lambda: {"Meta": 0, "Ejecucion": 0, "Indicadores": 0})
    for h in metas:
        m = metas_por_periodo[h["IdPeriodo"]]
        m["Meta"] += h["Meta"]
        m["Ejecucion"] += h["Ejecucion"]
        m["Indicadores"] += 1
    control_por_periodo = {c["IdPeriodo"]: c for c in controles}
    pe04_por_periodo = defaultdict(lambda: {"Fichas": 0, "Matriculados": 0, "Activos": 0, "Cancelados": 0, "Horas": 0.0})
    for h in pe04:
        p = pe04_por_periodo[h["ID_PERIODO"]]
        p["Fichas"] += 1
        p["Matriculados"] += h["APRENDICES_MATRICULADOS"]
        p["Activos"] += h["APRENDICES_ACTIVOS"]
        p["Cancelados"] += h["APRENDICES_CANCELADOS"]
        p["Horas"] += h["TOTAL_HORAS"]
    pe14_por_periodo = defaultdict(lambda: {"Marcaciones": 0, "AprendicesMarcados": 0, "Fichas": set()})
    for h in pe14:
        p = pe14_por_periodo[h["ID_PERIODO"]]
        p["Marcaciones"] += h["Cantidad_Aprendices"]
        p["Fichas"].add(h["CODIGO_FICHA"])
    for p in pe14_por_periodo.values():
        p["AprendicesMarcados"] = p["Marcaciones"]
        p["Fichas"] = len(p["Fichas"])

    periodos = sorted(set(metas_por_periodo) | set(pe04_por_periodo) | set(pe14_por_periodo))
    detalle = []
    for periodo in periodos:
        m = metas_por_periodo.get(periodo, {"Meta": 0, "Ejecucion": 0, "Indicadores": 0})
        c = control_por_periodo.get(periodo)
        p4 = pe04_por_periodo.get(periodo, {"Fichas": 0, "Matriculados": 0, "Activos": 0, "Cancelados": 0, "Horas": 0.0})
        p14 = pe14_por_periodo.get(periodo, {"Marcaciones": 0, "Fichas": 0})
        detalle.append({
            "IdPeriodo": periodo,
            "Meta_Suma_Indicadores": m["Meta"],
            "Ejecucion_Suma_Indicadores": m["Ejecucion"],
            "Indicadores": m["Indicadores"],
            "Meta_Oficial": (c or {}).get("Meta_Oficial"),
            "Ejecucion_Oficial": (c or {}).get("Ejecucion_Oficial"),
            "Diferencia_Meta_vs_Oficial": (m["Meta"] - (c or {}).get("Meta_Oficial", 0)) if c and c.get("Meta_Oficial") is not None else None,
            "PE04_Fichas": p4["Fichas"],
            "PE04_Matriculados": p4["Matriculados"],
            "PE04_Activos": p4["Activos"],
            "PE04_Cancelados": p4["Cancelados"],
            "PE04_Horas": round(p4["Horas"], 2),
            "PE14_Marcaciones": p14["Marcaciones"],
            "PE14_Fichas": p14["Fichas"],
            "Cobertura_PE14_vs_PE04": round(p14["Fichas"] / p4["Fichas"], 4) if p4["Fichas"] else None,
        })

    claves_pe04 = [(h["ID_PERIODO"], h["CODIGO_FICHA"]) for h in pe04]
    fichas_dim = {f["CODIGO_FICHA"] for f in dim_ficha}
    huerfanas_pe14 = sorted({h["CODIGO_FICHA"] for h in pe14 if h["CODIGO_FICHA"] not in fichas_dim})
    return {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "resumen": {
            "periodos": len(periodos),
            "rango_periodos": [min(periodos), max(periodos)] if periodos else [],
            "filas_fact_metas": len(metas),
            "filas_fact_pe04": len(pe04),
            "filas_fact_pe14": len(pe14),
            "fichas_dim": len(dim_ficha),
            "poblaciones": len(ORDEN_POBLACIONES),
            "duplicados_pe04": len(claves_pe04) - len(set(claves_pe04)),
            "fichas_pe14_sin_dim": len(huerfanas_pe14),
            "cancelados_negativos": sum(1 for h in pe04 if h["APRENDICES_CANCELADOS"] < 0),
            "activos_mayores_matriculados": sum(1 for h in pe04 if h["APRENDICES_ACTIVOS"] > h["APRENDICES_MATRICULADOS"]),
            "horas_totales": round(sum(h["TOTAL_HORAS"] for h in pe04), 2),
        },
        "detalle_periodos": detalle,
        "huerfanas_pe14": huerfanas_pe14[:50],
        "auditoria_ingesta": auditoria,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 78)
    print("ETL ASTIN - Estado de las metas Centro ASTIN")
    print("=" * 78)

    print("[1/6] Leyendo 01_Metas ...")
    metas, controles, aud_metas = leer_metas()
    print(f"      {len(metas)} filas de hechos, {len(controles)} controles oficiales.")

    print("[2/6] Leyendo 02_Reportes_PE04 ...")
    pe04, aud_pe04 = leer_pe04()
    print(f"      {len(pe04)} fichas.")

    print("[3/6] Leyendo 03_Reportes_PE14 ...")
    pe14, aud_pe14, nuevas = leer_pe14()
    print(f"      {len(pe14)} marcaciones de población.")
    if nuevas:
        print(f"      Poblaciones nuevas detectadas: {nuevas}")

    print("[4/6] Construyendo dimensiones ...")
    dim_periodo = construir_dim_periodo([h["IdPeriodo"] for h in metas] + [h["ID_PERIODO"] for h in pe04] + [h["ID_PERIODO"] for h in pe14])
    dim_ficha = construir_dim_ficha(pe04, pe14)
    dim_poblacion = construir_dim_poblacion()
    print(f"      DimPeriodo: {len(dim_periodo)}; DimFicha: {len(dim_ficha)}; DimPoblacion: {len(dim_poblacion)}.")

    print("[5/6] Escribiendo archivos curados ...")
    columnas_metas = ["IdPeriodo", "IdCentro", "IdCategoria", "IdNivelFormacion", "IdEstrategia", "Indicador", "Indicador_Normalizado", "Meta", "Ejecucion", "OrigenArchivo", "Hoja", "DiaCorte"]
    columnas_pe04 = ["ID_REGISTRO_UUID", "ID_PERIODO", "CODIGO_FICHA", "NOMBRE_PROGRAMA", "CODIGO_JORNADA", "NOMBRE_JORNADA", "MODALIDAD_FORMACION", "ESTADO_CURSO", "NIVEL_FORMACION", "APRENDICES_MATRICULADOS", "APRENDICES_ACTIVOS", "APRENDICES_CANCELADOS", "TOTAL_HORAS", "IdCentro", "ORIGEN_ARCHIVO"]
    columnas_pe14 = ["ID_REGISTRO_UUID", "ID_PERIODO", "IdCentro", "CODIGO_FICHA", "IdPoblacion", "NombrePoblacion", "Cantidad_Aprendices", "NOMBRE_PROGRAMA", "NIVEL_FORMACION", "NOMBRE_JORNADA", "ORIGEN_ARCHIVO"]

    n1 = escribir_csv(CURADOS / "fact_metas.csv", metas, columnas_metas)
    n2 = escribir_csv(CURADOS / "fact_pe04_fichas.csv", pe04, columnas_pe04)
    n3 = escribir_csv(CURADOS / "fact_pe14_aprendices.csv", pe14, columnas_pe14)
    escribir_csv(CURADOS / "dim_periodo.csv", dim_periodo, list(dim_periodo[0].keys()) if dim_periodo else [])
    escribir_csv(CURADOS / "dim_ficha_programa.csv", dim_ficha, list(dim_ficha[0].keys()) if dim_ficha else [])
    escribir_csv(CURADOS / "dim_poblacion.csv", dim_poblacion, list(dim_poblacion[0].keys()))
    escribir_csv(CURADOS / "dim_categoria.csv", DIM_CATEGORIA, list(DIM_CATEGORIA[0].keys()))
    escribir_csv(CURADOS / "dim_nivel_formacion.csv", DIM_NIVEL, list(DIM_NIVEL[0].keys()))
    escribir_csv(CURADOS / "dim_estrategia.csv", DIM_ESTRATEGIA, list(DIM_ESTRATEGIA[0].keys()))
    escribir_csv(CURADOS / "dim_centro.csv", DIM_CENTRO, list(DIM_CENTRO[0].keys()))
    escribir_csv(CURADOS / "control_metas.csv", controles, ["IdPeriodo", "Meta_Oficial", "Ejecucion_Oficial", "Fuente", "OrigenArchivo", "Hoja", "DiaCorte"])

    por_periodo_metas = defaultdict(list)
    for h in metas:
        por_periodo_metas[h["IdPeriodo"]].append(h)
    for periodo, filas in sorted(por_periodo_metas.items()):
        escribir_csv(CURADOS / "metas" / f"metas_curated_{periodo // 100}_{periodo % 100:02d}.csv", filas, columnas_metas)
    por_periodo_pe04 = defaultdict(list)
    for h in pe04:
        por_periodo_pe04[h["ID_PERIODO"]].append(h)
    for periodo, filas in sorted(por_periodo_pe04.items()):
        escribir_csv(CURADOS / "pe04" / f"pe04_curated_{periodo // 100}_{periodo % 100:02d}.csv", filas, columnas_pe04)
    por_periodo_pe14 = defaultdict(list)
    for h in pe14:
        por_periodo_pe14[h["ID_PERIODO"]].append(h)
    for periodo, filas in sorted(por_periodo_pe14.items()):
        escribir_csv(CURADOS / "pe14" / f"pe14_curated_{periodo // 100}_{periodo % 100:02d}.csv", filas, columnas_pe14)
    print(f"      Hechos: {n1} metas / {n2} PE04 / {n3} PE14.")

    print("[6/6] Calculando control de calidad ...")
    auditoria = aud_metas + aud_pe04 + aud_pe14
    escribir_csv(QA / "auditoria_ingesta.csv", auditoria, ["Origen", "Archivo", "Periodo", "Hoja", "Filas", "Estado", "Detalle"])
    qa = calcular_qa(metas, controles, pe04, pe14, dim_ficha, auditoria)
    with (QA / "informe_calidad.json").open("w", encoding="utf-8") as f:
        json.dump(qa, f, ensure_ascii=False, indent=2)

    print("-" * 78)
    for d in qa["detalle_periodos"]:
        print(f"  {d['IdPeriodo']} | metas {d['Meta_Suma_Indicadores']:>7,} vs oficial {str(d['Meta_Oficial']):>7} | PE04 {d['PE04_Fichas']:>4} fichas / {d['PE04_Matriculados']:>6,} apr. | PE14 {d['PE14_Marcaciones']:>6,} marcaciones")
    print("-" * 78)
    print(f"Informe de calidad: {QA / 'informe_calidad.json'}")
    print("ETL finalizado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
