# Informe de ejecución

**Proyecto:** Sistema de control e información — Estado de las metas Centro ASTIN  
**Fecha:** 13 de noviembre de 2026  
**Entregable:** proyecto PBIP `ASTIN_Metas.pbip` + ETL + modelo + reporte de 6 páginas

## 1. Resumen

Se construyó desde cero un proyecto de datos y un tablero multitemporal que reemplaza las tablas estáticas del archivo antiguo. El modelo se alimenta de las tres carpetas de origen y consolida todos los cortes disponibles sin intervención manual sobre el modelo.

| Indicador | Resultado |
|---|---|
| Periodos detectados | 2026-02 a 2026-10 (9 periodos con algún dato) |
| Filas FactMetas | 88 (4 cortes de metas: abril, agosto, septiembre y octubre) |
| Filas Fact_PE04_Fichas | 3.811 |
| Filas Fact_PE14_Aprendices | 116.844 |
| Fichas en Dim_Ficha_Programa | 753 |
| Poblaciones PE-14 | 52 + fila 9999 de contingencia |
| Medidas DAX | 31 |
| Páginas del reporte | 6 |
| Horas de fichas (suma de cortes) | 447.396,96 |

## 2. Validación técnica

- El modelo TMDL se deserializó correctamente con `TmdlSerializer` (14 tablas, 13 de datos + tabla de medidas).
- El PBIP abrió en Power BI Desktop 2.159 y el modelo se refrescó vía AMO/XMLA sin errores.
- Se ejecutaron consultas DAX de control: `COUNTROWS` de hechos y dimensiones, totales por periodo y medidas de último corte.
- El reporte PBIR cargó con las 6 páginas y los visuales; se validaron capturas de las páginas 1 a 6.
- Se corrigieron problemas de codificación (BOM/acentos), colisiones de columnas (`IdPeriodo`, `Hoja`), `Text.PositionOfAny` con cadenas de varios caracteres y el rendimiento de la ingesta.

## 3. Resultados por periodo

| Periodo | Meta indicadores | Ejecución | PE-04 matriculados | PE-14 marcaciones | Horas |
|---|---:|---:|---:|---:|---:|
| 2026-02 | — | — | 5.460 | — | 5.915,2 |
| 2026-03 | — | — | 10.215 | — | 22.480,0 |
| 2026-04 | 31.733 | 13.974 | 13.974 | — | 34.992,5 |
| 2026-05 | — | — | 16.926 | 16.926 | 50.151,3 |
| 2026-06 | — | — | 19.948 | 19.948 | 63.871,8 |
| 2026-07 | — | — | 22.544 | 22.544 | 76.426,8 |
| 2026-08 | 31.823 | 25.379 | 25.431 | 25.431 | 89.585,7 |
| 2026-09 | 31.823 | 28.695 | 28.917 | — | 103.973,7 |
| 2026-10 | 31.823 | 30.103 | — | — | — |

> No existen archivos de Metas para febrero, marzo, mayo, junio y julio en la carpeta original. El tablero muestra el periodo sin dato en lugar de inventar una meta.

## 4. Conciliación y hallazgos

1. **Metas oficiales vs suma de indicadores**
   - Abril: 31.733 = 31.733 (0).
   - Agosto, septiembre y octubre: 31.823 vs 31.733 oficial (+90). La diferencia corresponde a filas de estrategia (CampeSENA/FEP) que el archivo reporta por separado y que el total oficial no incorpora. Se expone en la página *Calidad y auditoría*, no se oculta.
2. **Ejecución oficial vs suma de indicadores**
   - Abril: 13.974 = 13.974.
   - Agosto: 25.379 vs 25.281 (+98).
   - Septiembre: 28.695 vs 28.597 (+98).
   - Octubre: 30.103 vs 30.046 (+57).
   - Son diferencias de redondeo/reporteo del archivo; el tablero muestra ambas columnas.
3. **PE-04 vs PE-14**
   - En mayo, junio, julio y agosto los totales coinciden exactamente (16.926; 19.948; 22.544; 25.431). En septiembre no hay PE-14; en abril no hay PE-14.
   - La cobertura PE-14/PE-04 del último corte es 89,3%.
4. **Cancelados**
   - PE-04 no trae una columna de cancelados. Se calcula `matriculados − activos`; en abril asciende a 4.636 (33,2%) y en septiembre a 14.059 (48,6%). Debe leerse como **no activos**, no necesariamente cancelaciones formales.
5. **Horas**
   - `TOTAL_HORAS` es la intensidad horaria de la ficha. La suma de cortes no representa horas-cronómetro ni horas efectivamente impartidas.
6. **PE-14**
   - La suma de todas las poblaciones coincide con el total de aprendices porque la categoría `NINGUNA` completa el 100%. La población vulnerable del último corte es 9.490 y los desplazados por violencia 3.465.
   - `Total_Desplazados_Violencia` usa la lista de la especificación, corregida (`INDIGENAS`, no `NDIGENAS`).

## 5. Entregables y estado del PBIX

| Entregable | Estado |
|---|---|
| PBIP con modelo TMDL y reporte PBIR | ✅ Generado, abierto y refrescado en Power BI Desktop |
| ETL Python + CSV curados | ✅ Generado y validado |
| Consultas M por carpeta | ✅ Implementadas sobre los curados; versiones de lectura directa en `powerquery/raw/` |
| Medidas DAX | ✅ 31 medidas, probadas con consultas DAX |
| Documentación | ✅ Arquitectura, diccionario, modelo, DAX, manual e informe |
| PBIX binario | ⚠️ No se pudo escribir de forma desatendida: la sesión de Windows se bloqueó durante la automatización del diálogo “Guardar como”. El PBIP está listo; para producir el PBIX abra el PBIP y use `Archivo > Guardar como`, o ejecute `scripts/generar_pbix.ps1` con la sesión desbloqueada. |

## 6. Cómo comprobar la actualización automática

1. Copie un archivo nuevo en cualquiera de las tres carpetas.
2. Ejecute `python scripts\astin_etl.py`.
3. Abra/actualice el PBIP.
4. Verifique el nuevo periodo en el slicer `Periodo`, en la tabla de calidad y en la evolución.

Si usa `scripts\vigilar_y_actualizar.ps1`, los pasos 2 y 3 ocurren solos al detectar el archivo, siempre que el PBIP esté abierto en Power BI Desktop.

## 7. Recomendaciones

- Programar el ETL cada 30 minutos y el vigilante al iniciar sesión.
- Revisar mensualmente la página de calidad antes de publicar.
- Mantener el catálogo `data/curated/dim_poblacion.csv` cuando PE-14 agregue una población nueva (el ETL la detecta y la marca como 9999 hasta catalogarla).
- Para distribución, publicar el PBIX en el servicio con actualización programada y credenciales de la puerta de enlace.
