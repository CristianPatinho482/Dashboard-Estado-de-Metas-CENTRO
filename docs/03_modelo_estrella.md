# Modelo estrella

## Diagrama lógico

```text
                         ┌───────────────┐
                         │  DimPeriodo   │
                         │  IdPeriodo    │
                         └──────┬────────┘
        ┌───────────────────────┼────────────────────────┐
        ▼                       ▼                        ▼
┌───────────────┐      ┌──────────────────┐     ┌────────────────────┐
│   FactMetas   │      │ Fact_PE04_Fichas │     │ Fact_PE14_Aprendices│
│ IdPeriodo     │      │ ID_PERIODO       │     │ ID_PERIODO         │
│ IdCategoria   │      │ CODIGO_FICHA     │     │ CODIGO_FICHA       │
│ IdNivelFormac.│      │ IdCentro         │     │ IdCentro           │
│ IdEstrategia  │      └──────┬───────────┘     │ IdPoblacion        │
│ IdCentro      │             │                 └─────────┬──────────┘
└───┬───┬───┬───┘             ▼                           ▼
    │   │   │          ┌────────────────┐        ┌────────────────┐
    │   │   └─────────▶│Dim_Ficha_Prog. │◀───────│  DimPoblacion  │
    │   │              └────────────────┘        └────────────────┘
    │   └──────────────────▶ DimEstrategia
    └──────────────────────▶ DimNivelFormacion / DimCategoria
```

## Relaciones (todas 1:* y filtro simple)

| Desde (1) | Hacia (*) | Columna |
|---|---|---|
| DimPeriodo | FactMetas | IdPeriodo |
| DimPeriodo | Fact_PE04_Fichas | ID_PERIODO |
| DimPeriodo | Fact_PE14_Aprendices | ID_PERIODO |
| DimPeriodo | _Control_Metas | IdPeriodo |
| Dim_Ficha_Programa | Fact_PE04_Fichas | CODIGO_FICHA |
| Dim_Ficha_Programa | Fact_PE14_Aprendices | CODIGO_FICHA |
| DimPoblacion | Fact_PE14_Aprendices | IdPoblacion |
| DimCategoria | FactMetas | IdCategoria |
| DimNivelFormacion | FactMetas | IdNivelFormacion |
| DimEstrategia | FactMetas | IdEstrategia |
| DimCentro | FactMetas | IdCentro |
| DimCentro | Fact_PE04_Fichas | IdCentro |
| DimCentro | Fact_PE14_Aprendices | IdCentro |

**Dirección de filtro:** única (dimensión → hecho). No hay relaciones bidireccionales ni rutas ambiguas.

## Granos

- `FactMetas`: un registro por periodo e indicador de formación. La ejecución es acumulada (YTD) al corte.
- `Fact_PE04_Fichas`: un registro por periodo y ficha. Los valores son del corte mensual, no acumulados.
- `Fact_PE14_Aprendices`: un registro por periodo, ficha y población. Es una tabla desdinamizada; una ficha puede aparecer en varias poblaciones.

## Reglas de integridad

- `DimPeriodo` cubre todos los meses del año (12 filas) para que los ejes temporales no pierdan continuidad.
- `Dim_Ficha_Programa` se alimenta de `Fact_PE04_Fichas` (la ficha más reciente). Las fichas de PE-14 son subconjunto de PE-04 en los cortes validados.
- `DimPoblacion` se alimenta de `data/curated/dim_poblacion.csv`; si aparece una población nueva, el ETL la agrega y el modelo la reclasifica con 9999 hasta actualizar el catálogo.
- `_Control_Metas` se relaciona con `DimPeriodo` solo para la página de calidad; no interviene en los KPI.
