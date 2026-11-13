# Catálogo de medidas DAX

Todas las medidas viven en la tabla `_Medidas_ASTIN`, organizadas en carpetas de presentación. El archivo `powerquery/_Medidas_ASTIN.dax` contiene la versión texto generada por el constructor.

## 01 Metas

| Medida | Fórmula / propósito |
|---|---|
| `Meta_Total` | `SUM(FactMetas[Meta])`. Meta de los indicadores en el contexto. |
| `Ejecucion_Total` | `SUM(FactMetas[Ejecucion])`. Ejecución acumulada del corte. |
| `Porc_Cumplimiento_Metas` | `DIVIDE([Ejecucion_Total],[Meta_Total],0)`. |
| `Brecha_Metas` | `[Meta_Total]-[Ejecucion_Total]`. |
| `Estado_Meta` | Semáforo: Sobre ejecución / En ruta / Vulnerable / Bajo. |
| `Ejecucion_Mes_Anterior` | Ejecución del periodo inmediatamente anterior. |
| `Variacion_Ejecucion_MoM` | Variación % contra el mes anterior. |
| `Ejecucion_Incremental` | Diferencia contra el mes anterior (útil si la ejecución es acumulada). |

## 02 PE-04

| Medida | Fórmula / propósito |
|---|---|
| `Total_Matriculados` | `SUM(Fact_PE04_Fichas[APRENDICES_MATRICULADOS])`. |
| `Total_Activos` | `SUM(Fact_PE04_Fichas[APRENDICES_ACTIVOS])`. |
| `Total_Cancelados` | `SUM(Fact_PE04_Fichas[APRENDICES_CANCELADOS])` (derivado). |
| `Total_Horas_Ejecutadas` | `SUM(Fact_PE04_Fichas[TOTAL_HORAS])`. |
| `Tasa_Activos` | Activos / matriculados. |
| `Tasa_Cancelacion` | No activos / matriculados. |
| `Fichas_Atendidas` | `DISTINCTCOUNT(Fact_PE04_Fichas[CODIGO_FICHA])`. |
| `Promedio_Aprendices_Ficha` | Matriculados / fichas. |
| `Promedio_Horas_Ficha` | Horas / fichas. |

## 03 PE-14

| Medida | Fórmula / propósito |
|---|---|
| `Total_Aprendices_PE14` | `SUM(Fact_PE14_Aprendices[Cantidad_Aprendices])`. |
| `Total_Poblacion_Vulnerable` | Total PE-14 con `EsVulnerable = 1` (excluye NINGUNA). |
| `Total_Desplazados_Violencia` | Total PE-14 para el conjunto de poblaciones de desplazamiento/violencia de la especificación. |
| `Fichas_Con_Caracterizacion` | Fichas con registro PE-14. |
| `Cobertura_Caracterizacion` | Fichas PE-14 / fichas PE-04. |
| `Participacion_Vulnerable` | Población vulnerable / total PE-14. |
| `Poblaciones_Con_Registro` | Poblaciones con al menos un aprendiz marcado. |

`Total_Desplazados_Violencia` usa la lista:

```text
DESPLAZADOS_DISCAPACITADOS
DESPLAZADOS_POR_FENOMENOS_NATURALES
DESPLAZADOS_POR_FENOMENOS_NATURALES_CABEZA_DE_FAMILIA
DESPLAZADOS_POR_LA_VIOLENCIA
AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA
AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA
INDIGENAS
INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA_CABEZA_DE_FAMILIA
```

La especificación original traía `NDIGENAS`; se corrigió a `INDIGENAS`.

## 04 Comparativo

| Medida | Fórmula / propósito |
|---|---|
| `Brecha_PE04_PE14` | Matriculados − caracterizados. |
| `Cumplimiento_PE04_vs_Meta` | Matriculados / meta. |
| `Horas_Por_Aprendiz` | Horas / matriculados. |

## 05 Último corte

Estas medidas permiten que tarjetas y desgloses muestren el último dato disponible sin obligar a seleccionar un periodo.

| Medida | Fórmula / propósito |
|---|---|
| `Periodo_Actual` | `FORMAT(MAX(DimPeriodo[IdPeriodo]),"000000")`. |
| `Meta_Actual` | Meta del último periodo con archivo de metas (`LASTNONBLANK`). |
| `Ejecucion_Actual` | Ejecución del último periodo con archivo de metas. |
| `Cumplimiento_Actual` | Cumplimiento del último corte. |
| `Brecha_Actual` | Brecha del último corte. |
| `Matriculados_Actual`, `Activos_Actual`, `PE14_Actual`, `Desplazados_Actual` | Último dato disponible por fuente. |
| `Periodo_PE04`, `Periodo_PE14` | Último periodo con datos PE-04/PE-14 dentro del filtro. |
| `Matriculados_Ultimo`, `Activos_Ultimo`, `Cancelados_Ultimo`, `Horas_Ultimo`, `Fichas_Ultimo`, `Tasa_Activos_Ultimo` | Valores del último corte PE-04 respetando la categoría del visual. |
| `PE14_Ultimo`, `Vulnerable_Ultimo`, `Desplazados_Ultimo`, `Fichas_Caracterizadas_Ultimo` | Valores del último corte PE-14 respetando la población del visual. |
| `Cobertura_Ultimo` | Cobertura PE-14/PE-04 del último corte. |

## 06 Control

| Medida | Fórmula / propósito |
|---|---|
| `Meta_Oficial_Total` | Suma del total oficial del encabezado de metas. |
| `Ejecucion_Oficial_Total` | Suma de la ejecución oficial del encabezado. |
| `Diferencia_Meta_Oficial` | Suma de indicadores − meta oficial. |
| `Diferencia_Ejecucion_Oficial` | Suma de indicadores − ejecución oficial. |
