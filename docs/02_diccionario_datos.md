# Diccionario de datos

## Tablas de hechos

### FactMetas (grano: periodo × indicador)

| Columna | Tipo | Descripción |
|---|---|---|
| IdPeriodo | Int64 | Periodo YYYYMM. Clave foránea a DimPeriodo. |
| IdCentro | Int64 | Centro de formación (9230 ASTIN). |
| IdCategoria | Int64 | 1 Formación Titulada / 2 Formación Complementaria. |
| IdNivelFormacion | Int64 | Tecnólogo, Técnico, Operario, Auxiliar, Complementaria, Bilingüismo, FEC. |
| IdEstrategia | Int64 | Regular, Presencial, Virtual, A Distancia, CampeSENA, Full Popular, FIC, Articulación, Especial. |
| Indicador | Texto | Etiqueta original del indicador. |
| Indicador_Normalizado | Texto | Etiqueta normalizada (auditoría/deduplicación). |
| Meta | Int64 | Meta del indicador. |
| Ejecucion | Int64 | Ejecución acumulada reportada en el archivo de metas. |
| OrigenArchivo | Texto | Archivo fuente. |
| Hoja | Texto | Hoja fuente. |
| DiaCorte | Int64 | Día de corte cuando el archivo trae varias hojas (p. ej. 20 y 30 de abril). |

### Fact_PE04_Fichas (grano: periodo × ficha)

| Columna | Tipo | Descripción |
|---|---|---|
| ID_REGISTRO_UUID | Texto | Llave única `periodo-ficha`. |
| ID_PERIODO | Int64 | Periodo YYYYMM. |
| CODIGO_FICHA | Int64 | Identificador de ficha. |
| NOMBRE_PROGRAMA | Texto | Programa de formación. |
| CODIGO_JORNADA | Int64 | Código de jornada. |
| NOMBRE_JORNADA | Texto | Diurna, Mixta, Nocturna, etc. |
| MODALIDAD_FORMACION | Texto | Presencial, Virtual, etc. |
| ESTADO_CURSO | Texto | Estado reportado. |
| NIVEL_FORMACION | Texto | Nivel reportado por PE-04. |
| APRENDICES_MATRICULADOS | Int64 | Total de aprendices de la ficha. |
| APRENDICES_ACTIVOS | Int64 | Aprendices activos. |
| APRENDICES_CANCELADOS | Int64 | Derivado: matriculados − activos (no activos). |
| TOTAL_HORAS | Double | Intensidad horaria de la ficha en horas decimales. |
| IdCentro | Int64 | Centro. |
| ORIGEN_ARCHIVO | Texto | Archivo fuente. |

### Fact_PE14_Aprendices (grano: periodo × ficha × población)

| Columna | Tipo | Descripción |
|---|---|---|
| ID_REGISTRO_UUID | Texto | Llave única `periodo-ficha-población`. |
| ID_PERIODO | Int64 | Periodo YYYYMM. |
| IdCentro | Int64 | Centro. |
| CODIGO_FICHA | Int64 | Ficha. |
| IdPoblacion | Int64 | Población (1–52; 9999 sin clasificar). |
| NombrePoblacion | Texto | Nombre normalizado de la población. |
| Cantidad_Aprendices | Int64 | Aprendices marcados en esa población. |

## Dimensiones

### DimPeriodo
`IdPeriodo`, `Anio`, `Mes`, `NombreMes`, `Trimestre`, `FechaInicio`, `FechaFin`, `PeriodoTexto`, `OrdenAnual`.

### Dim_Ficha_Programa
`CODIGO_FICHA`, `NOMBRE_PROGRAMA`, `CODIGO_JORNADA`, `NOMBRE_JORNADA`, `MODALIDAD_FORMACION`, `NIVEL_FORMACION`, `IdCentro`, `UltimoPeriodo`. Se construye con la última versión de cada ficha.

### DimCategoria
`IdCategoria`, `NombreCategoria`.

### DimNivelFormacion
`IdNivelFormacion`, `NombreNivelFormacion`, `IdCategoria`, `Orden`.

### DimEstrategia
`IdEstrategia`, `NombreEstrategia`, `Orden`.

### DimCentro
`IdCentro`, `NombreCentro`, `NombreRegional`, `CodigoRegional`.

### DimPoblacion
`IdPoblacion`, `NombrePoblacion` (técnico), `NombreAmigable`, `GrupoPoblacional`, `EsVulnerable` (1/0), `EsDesplazamientoViolencia` (1/0), `Orden`.
Incluye 52 poblaciones y la fila 9999 `SIN_CLASIFICAR` para nuevos valores no catalogados.

## Tablas de control

### _Control_Metas
`IdPeriodo`, `Meta_Oficial`, `Ejecucion_Oficial`, `Fuente`, `OrigenArchivo`, `Hoja`, `DiaCorte`.

### _Auditoria_Ingesta
`Origen`, `Archivo`, `Extension`, `IdPeriodo`, `FechaModificacion`, `TamanoKB`.

### _Medidas_ASTIN
Tabla contenedora de las 31 medidas DAX. No tiene relación con los hechos.
