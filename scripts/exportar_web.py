# -*- coding: utf-8 -*-
"""Genera los datos agregados para el tablero web estático (GitHub Pages).

Lee los CSV curados y escribe web/datos.js (window.ASTIN_DATA) y web/datos.json.
No incluye información personal: solo conteos agregados por periodo, nivel,
programa y población.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CUR = BASE / "data" / "curated"
WEB = BASE / "web"

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

POBLACIONES_DESPLAZADOS = {
    # Definición estricta: solo violencia y sus variantes de cabeza de familia.
    # Excluye fenómenos naturales, discapacidad e indígenas generales.
    "DESPLAZADOS_POR_LA_VIOLENCIA",
    "DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA",
    "AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA",
    "AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA",
    "INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA",
    "INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA",
}


def leer(nombre: str) -> list[dict]:
    ruta = CUR / nombre
    if not ruta.exists():
        return []
    with ruta.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(valor, defecto=0):
    try:
        if valor is None or valor == "":
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def etiqueta(p: int) -> str:
    return f"{MESES.get(p % 100, '')} {p // 100}"


def main() -> None:
    WEB.mkdir(parents=True, exist_ok=True)

    metas = leer("fact_metas.csv")
    pe04 = leer("fact_pe04_fichas.csv")
    pe14 = leer("fact_pe14_aprendices.csv")
    dim_nivel = {int(r["IdNivelFormacion"]): r for r in leer("dim_nivel_formacion.csv")}
    dim_estr = {int(r["IdEstrategia"]): r for r in leer("dim_estrategia.csv")}
    dim_pob = {int(r["IdPoblacion"]): r for r in leer("dim_poblacion.csv")}
    control = leer("control_metas.csv")
    auditoria = leer("../qa/auditoria_ingesta.csv")

    # ---------------- Metas ----------------
    p_metas = max((int(r["IdPeriodo"]) for r in metas), default=None)
    metas_periodo = defaultdict(lambda: {"meta": 0, "ejecucion": 0})
    metas_nivel = defaultdict(lambda: {"meta": 0, "ejecucion": 0})
    metas_estrategia = defaultdict(lambda: {"meta": 0, "ejecucion": 0})
    for r in metas:
        p = int(r["IdPeriodo"])
        m = num(r["Meta"])
        e = num(r["Ejecucion"])
        metas_periodo[p]["meta"] += m
        metas_periodo[p]["ejecucion"] += e
        if p == p_metas:
            n = int(r["IdNivelFormacion"])
            metas_nivel[n]["meta"] += m
            metas_nivel[n]["ejecucion"] += e
            s = int(r["IdEstrategia"])
            metas_estrategia[s]["meta"] += m
            metas_estrategia[s]["ejecucion"] += e
    metas_por_periodo = [
        {"id": p, "label": etiqueta(p), "meta": v["meta"], "ejecucion": v["ejecucion"],
         "cumplimiento": (v["ejecucion"] / v["meta"]) if v["meta"] else None}
        for p, v in sorted(metas_periodo.items())
    ]
    metas_por_nivel = [
        {"nivel": dim_nivel.get(n, {}).get("NombreNivelFormacion", str(n)),
         "meta": v["meta"], "ejecucion": v["ejecucion"],
         "cumplimiento": (v["ejecucion"] / v["meta"]) if v["meta"] else None}
        for n, v in sorted(metas_nivel.items(), key=lambda kv: dim_nivel.get(kv[0], {}).get("Orden", 99))
    ]
    metas_por_estrategia = [
        {"estrategia": dim_estr.get(s, {}).get("NombreEstrategia", str(s)),
         "meta": v["meta"], "ejecucion": v["ejecucion"]}
        for s, v in sorted(metas_estrategia.items())
    ]

    # ---------------- PE-04 ----------------
    pe04_periodo = defaultdict(lambda: {"matriculados": 0, "activos": 0, "cancelados": 0, "horas": 0.0, "fichas": set()})
    for r in pe04:
        p = int(r["ID_PERIODO"])
        v = pe04_periodo[p]
        v["matriculados"] += int(num(r["APRENDICES_MATRICULADOS"]))
        v["activos"] += int(num(r["APRENDICES_ACTIVOS"]))
        v["cancelados"] += int(num(r["APRENDICES_CANCELADOS"]))
        v["horas"] += num(r["TOTAL_HORAS"])
        v["fichas"].add(r["CODIGO_FICHA"])
    p_pe04 = max(pe04_periodo) if pe04_periodo else None
    pe04_por_periodo = [
        {"id": p, "label": etiqueta(p), "matriculados": v["matriculados"], "activos": v["activos"],
         "cancelados": v["cancelados"], "horas": round(v["horas"], 1), "fichas": len(v["fichas"])}
        for p, v in sorted(pe04_periodo.items())
    ]

    latest_pe04 = [r for r in pe04 if p_pe04 is not None and int(r["ID_PERIODO"]) == p_pe04]
    prog = defaultdict(lambda: {"matriculados": 0, "activos": 0, "fichas": set()})
    jornada = defaultdict(int)
    modalidad = defaultdict(int)
    for r in latest_pe04:
        nombre = (r["NOMBRE_PROGRAMA"] or "Sin programa").strip()
        prog[nombre]["matriculados"] += int(num(r["APRENDICES_MATRICULADOS"]))
        prog[nombre]["activos"] += int(num(r["APRENDICES_ACTIVOS"]))
        prog[nombre]["fichas"].add(r["CODIGO_FICHA"])
        jornada[(r["NOMBRE_JORNADA"] or "Sin jornada").strip()] += int(num(r["APRENDICES_MATRICULADOS"]))
        modalidad[(r["MODALIDAD_FORMACION"] or "Sin modalidad").strip()] += int(num(r["APRENDICES_MATRICULADOS"]))
    pe04_programas = sorted(
        [{"programa": k, "matriculados": v["matriculados"], "activos": v["activos"], "fichas": len(v["fichas"])}
         for k, v in prog.items()], key=lambda x: x["matriculados"], reverse=True)[:15]
    pe04_jornada = sorted([{"jornada": k, "matriculados": v} for k, v in jornada.items()], key=lambda x: x["matriculados"], reverse=True)
    pe04_modalidad = sorted([{"modalidad": k, "matriculados": v} for k, v in modalidad.items()], key=lambda x: x["matriculados"], reverse=True)

    # ---------------- PE-14 ----------------
    p_pe14 = max((int(r["ID_PERIODO"]) for r in pe14), default=None)
    pe14_periodo = defaultdict(lambda: {"total": 0, "vulnerable": 0, "desplazados": 0})
    pe14_pob = defaultdict(int)
    pe14_grupo = defaultdict(int)
    pe14_fichas_latest = set()
    for r in pe14:
        p = int(r["ID_PERIODO"])
        cant = int(num(r["Cantidad_Aprendices"]))
        meta = dim_pob.get(int(r["IdPoblacion"]), {})
        vulnerable = str(meta.get("EsVulnerable", "0")) == "1"
        desplazado = r["NombrePoblacion"] in POBLACIONES_DESPLAZADOS
        pe14_periodo[p]["total"] += cant
        if vulnerable:
            pe14_periodo[p]["vulnerable"] += cant
        if desplazado:
            pe14_periodo[p]["desplazados"] += cant
        if p == p_pe14:
            pe14_fichas_latest.add(r["CODIGO_FICHA"])
            if vulnerable:
                nombre = meta.get("NombreAmigable", r["NombrePoblacion"])
                pe14_pob[nombre] += cant
                pe14_grupo[meta.get("GrupoPoblacional", "Otras poblaciones")] += cant
    pe14_por_periodo = [
        {"id": p, "label": etiqueta(p), "total": v["total"], "vulnerable": v["vulnerable"], "desplazados": v["desplazados"]}
        for p, v in sorted(pe14_periodo.items())
    ]
    pe14_poblaciones = sorted([{"poblacion": k, "cantidad": v} for k, v in pe14_pob.items()], key=lambda x: x["cantidad"], reverse=True)[:15]
    pe14_grupos = sorted([{"grupo": k, "cantidad": v} for k, v in pe14_grupo.items()], key=lambda x: x["cantidad"], reverse=True)

    # ---------------- Control ----------------
    control_por_periodo = defaultdict(lambda: {"metaOficial": 0, "ejecucionOficial": 0})
    for r in control:
        p = int(r["IdPeriodo"])
        control_por_periodo[p]["metaOficial"] += num(r["Meta_Oficial"])
        control_por_periodo[p]["ejecucionOficial"] += num(r["Ejecucion_Oficial"])
    control_data = []
    for p in sorted(set(metas_periodo) | set(control_por_periodo)):
        m = metas_periodo.get(p, {"meta": 0, "ejecucion": 0})
        c = control_por_periodo.get(p, {"metaOficial": 0, "ejecucionOficial": 0})
        control_data.append({
            "id": p, "label": etiqueta(p),
            "meta": m["meta"], "metaOficial": c["metaOficial"], "difMeta": m["meta"] - c["metaOficial"],
            "ejecucion": m["ejecucion"], "ejecucionOficial": c["ejecucionOficial"], "difEjecucion": m["ejecucion"] - c["ejecucionOficial"],
        })

    # ---------------- KPIs ----------------
    latest_pe04_tot = pe04_periodo.get(p_pe04, {"matriculados": 0, "activos": 0, "cancelados": 0, "horas": 0.0, "fichas": set()})
    latest_pe14_tot = pe14_periodo.get(p_pe14, {"total": 0, "vulnerable": 0, "desplazados": 0})
    latest_metas = metas_periodo.get(p_metas, {"meta": 0, "ejecucion": 0})
    cobertura = (len(pe14_fichas_latest) / max(len(latest_pe04), 1))
    kpis = {
        "meta": latest_metas["meta"],
        "ejecucion": latest_metas["ejecucion"],
        "cumplimiento": (latest_metas["ejecucion"] / latest_metas["meta"]) if latest_metas["meta"] else None,
        "matriculados": latest_pe04_tot["matriculados"],
        "activos": latest_pe04_tot["activos"],
        "cancelados": latest_pe04_tot["cancelados"],
        "horas": round(latest_pe04_tot["horas"], 1),
        "pe14": latest_pe14_tot["total"],
        "vulnerable": latest_pe14_tot["vulnerable"],
        "desplazados": latest_pe14_tot["desplazados"],
        "cobertura": round(cobertura, 4),
        "periodoMetas": etiqueta(p_metas) if p_metas else "",
        "periodoPE04": etiqueta(p_pe04) if p_pe04 else "",
        "periodoPE14": etiqueta(p_pe14) if p_pe14 else "",
    }

    datos = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "periodos": [{"id": p, "label": etiqueta(p)} for p in sorted(set(metas_periodo) | set(pe04_periodo) | set(pe14_periodo))],
        "kpis": kpis,
        "metasPorPeriodo": metas_por_periodo,
        "metasNivel": metas_por_nivel,
        "metasEstrategia": metas_por_estrategia,
        "pe04PorPeriodo": pe04_por_periodo,
        "pe04Programas": pe04_programas,
        "pe04Jornada": pe04_jornada,
        "pe04Modalidad": pe04_modalidad,
        "pe14PorPeriodo": pe14_por_periodo,
        "pe14Poblaciones": pe14_poblaciones,
        "pe14Grupos": pe14_grupos,
        "control": control_data,
        "auditoria": [{"origen": r.get("Origen", ""), "archivo": r.get("Archivo", ""), "periodo": r.get("Periodo", ""), "estado": r.get("Estado", "")} for r in auditoria[-60:]],
    }

    (WEB / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    (WEB / "datos.js").write_text("window.ASTIN_DATA = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print("Datos web generados:", WEB / "datos.js", f"({len(json.dumps(datos)) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
