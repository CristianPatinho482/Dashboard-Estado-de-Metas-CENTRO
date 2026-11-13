# Sistema de control e información — Estado de las metas Centro ASTIN

Proyecto de datos y tablero de Power BI para consolidar, de forma multitemporal y automática, la información de las metas de formación, los reportes PE-04 y la caracterización PE-14 del Centro Nacional de Asistencia Técnica a la Industria — ASTIN.

## Entregables

| Componente | Ubicación | Descripción |
|---|---|---|
| Proyecto Power BI (PBIP) | `ASTIN_Metas.pbip` | Modelo semántico TMDL + reporte PBIR de 6 páginas. Es el formato nativo versionable de Power BI. |
| Modelo semántico | `ASTIN_Metas.SemanticModel/` | Tablas de hechos, dimensiones, relaciones 1:* y 31 medidas DAX. |
| Reporte | `ASTIN_Metas.Report/` | Páginas y visuales en formato PBIR. |
| ETL | `scripts/astin_etl.py` | Lee las tres carpetas, normaliza, valida y genera los CSV curados. |
| Power Query (M) | `powerquery/` | Consultas de ingesta, dimensiones y utilidades. |
| Datos curados | `data/curated/` | Hechos, dimensiones y cortes mensuales listos para el modelo. |
| Calidad | `data/qa/` | Auditoría de archivos e informe de conciliación. |
| Documentación | `docs/` | Arquitectura, diccionario, modelo estrella, DAX, manual e informe de ejecución. |

## Inicio rápido

1. Ejecute el ETL:

   ```powershell
   python scripts\astin_etl.py
   ```

2. Abra `ASTIN_Metas.pbip` con Power BI Desktop (doble clic).
3. Actualice el modelo (`Inicio > Actualizar`).
4. Para generar el `.pbix`, use `Archivo > Guardar como` y elija el formato PBIX, o ejecute:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\generar_pbix.ps1
   ```

## Actualización transparente al agregar un mes

Coloque el nuevo archivo en la carpeta correspondiente:

- `01_Metas`: archivo `.xlsx` con la tabla de metas del mes.
- `02_Reportes_PE04`: archivo `.xlsx` o `.csv` del reporte PE-04.
- `03_Reportes_PE14`: archivo `.xlsx` o `.csv` del reporte PE-14.

Luego:

```powershell
python scripts\astin_etl.py
```

El ETL detecta el periodo por el nombre/contenido del archivo, lo normaliza, excluye subtotales y escribe un nuevo corte mensual en `data/curated/`. El modelo toma todos los cortes disponibles; no hay que editar consultas ni medidas.

Para que la actualización sea totalmente desatendida mientras el tablero está abierto, ejecute una vez:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\vigilar_y_actualizar.ps1
```

El vigilante detecta archivos nuevos/modificados, ejecuta el ETL y refresca el modelo abierto en Power BI mediante AMO/XMLA. El log queda en `data/qa/vigilante.log`.

## Rutas de origen configuradas

Las rutas están en las expresiones del modelo (`RutaMetas`, `RutaPE04`, `RutaPE14`, `RutaCurados`) y en `scripts/astin_etl.py`:

```text
C:\Users\capatino\OneDrive - Servicio Nacional de Aprendizaje\BACKUP DISCO\Mis proyectos\AREA LABORAL\SENA\POWER BI\Sistema de control e información - Estado de las metas centro ASTIN\
├── 01_Metas
├── 02_Reportes_PE04
└── 03_Reportes_PE14
```

Para mover el proyecto o las fuentes, actualice esas cuatro expresiones en Power Query (`Inicio > Transformar datos > fx`) y las constantes del ETL.

## Notas de diseño

- **Modelo en estrella** con tres hechos (`FactMetas`, `Fact_PE04_Fichas`, `Fact_PE14_Aprendices`) y dimensiones conformes (`DimPeriodo`, `Dim_Ficha_Programa`, `DimCategoria`, `DimNivelFormacion`, `DimEstrategia`, `DimCentro`, `DimPoblacion`).
- **Ingesta por carpeta**: el ETL recorre las tres carpetas y consolida todos los cortes; el modelo lee los curados mensuales con `Folder.Files` y `Csv.Document`, lo que mantiene el refresco rápido y determinista.
- **Sin subtotales**: el ETL excluye filas `TOTAL`, `(A)`, `(H)` y encabezados repetidos para evitar dobles conteos.
- **Trazabilidad**: cada hecho conserva `OrigenArchivo` y la página *Calidad y auditoría* muestra la conciliación contra el total oficial y los archivos monitoreados.
- **Caveats**: consulte `docs/06_informe_ejecucion.md` (cancelados derivados, horas de intensidad, diferencias de metas oficiales y cobertura PE-14).
