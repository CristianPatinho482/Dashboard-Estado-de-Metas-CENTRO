# Arquitectura de la solución

## 1. Flujo de datos

```text
01_Metas (xlsx)           02_Reportes_PE04 (xlsx/xml)      03_Reportes_PE14 (xlsx)
      │                            │                                │
      └──────────────┬─────────────┴────────────────┬───────────────┘
                     ▼                              ▼
            scripts/astin_etl.py  (Python + openpyxl)
                     │
      ┌──────────────┼───────────────────────────────┐
      ▼              ▼                               ▼
 data/curated/    data/curated/pe04/            data/curated/pe14/
 metas_*.csv      pe04_curated_*.csv             pe14_curated_*.csv
      │              │                               │
      └──────────────┴───────────────┬───────────────┘
                                     ▼
                     Power Query (M) — Folder.Files + Csv.Document
                                     ▼
             Modelo semántico TMDL (estrella, 3 hechos, 7 dimensiones)
                                     ▼
                     Reporte PBIR (6 páginas, 31 medidas DAX)
```

## 2. Capas

| Capa | Responsable | Función |
|---|---|---|
| Fuente | Carpetas 01/02/03 | Archivos mensuales originales. No se modifican. |
| Normalización | `scripts/astin_etl.py` | Detecta periodo, layout, encabezados, tipos, subtotales y duplicados. Genera curados. |
| Curados | `data/curated/` | Contrato estable para Power BI: hechos, dimensiones y control. |
| Ingesta | `powerquery/*.m` | `Folder.Files` sobre los curados, tipado estricto y deduplicación. |
| Modelo | TMDL | Star schema, relaciones 1:* y medidas DAX. |
| Reporte | PBIR | Visuales, filtros, tema y navegación. |
| Calidad | `data/qa/` | Auditoría, conciliación y log del vigilante. |

## 3. Decisiones de ingesta

- **Periodo**: se obtiene del contenido (`202604` en PE-04/PE-14) o del nombre del archivo (meses en español + año). `Metas` sin mes (matriz anual) se omite y se reporta en auditoría.
- **Subtotales**: se excluyen etiquetas que empiezan por `TOTAL`, contienen ` = (` o son encabezados repetidos. También se excluyen las filas de retención, certificación y poblaciones dentro de `01_Metas` para que el hecho solo contenga indicadores de formación.
- **Duplicados**: los hechos se deduplican por llave de negocio (`IdPeriodo + indicador`, `periodo + ficha`, `periodo + ficha + población`).
- **Cancelados**: PE-04 no reporta cancelados; se calcula `matriculados - activos` y se documenta como “no activos”.
- **Horas**: `TOTAL_HORAS` de PE-04 es intensidad horaria de la ficha (formato `[h]:mm`), no horas-cronómetro. El ETL la convierte a horas decimales.
- **PE-14**: se desdinamizan únicamente las columnas `*_Total_Aprendices` (52 poblaciones) y se conserva el total por ficha en la auditoría. No se suman las columnas de género para evitar duplicar personas.
- **Metas oficiales**: se captura el total del encabezado del archivo en `_Control_Metas` para conciliar contra la suma de indicadores. No se usa para calcular los KPI; se muestra en la página de calidad.

## 4. Por qué el modelo lee curados y no los Excel directamente

La lectura directa de 17 libros con `Excel.Workbook` y 234 columnas en PE-14 es costosa y sensible a cambios de formato. El ETL concentra esa complejidad una vez y deja un contrato CSV estable. El modelo queda rápido, reproducible y fácil de auditar; el vigilante ejecuta el ETL y refresca automáticamente al detectar un archivo nuevo.

Las consultas M de lectura directa se conservan en `powerquery/raw/` como referencia y para escenarios de contingencia.

## 5. Automatización

- `scripts/astin_etl.py`: ejecución manual o programada.
- `scripts/vigilar_y_actualizar.ps1`: `FileSystemWatcher` + ETL + refresco AMO del modelo abierto.
- `scripts/generar_pbix.ps1`: guarda una copia `.pbix` desde el PBIP abierto (requiere sesión de escritorio desbloqueada).
- Programador de tareas sugerido: ejecutar el ETL cada 30 minutos y el vigilante al iniciar sesión.
