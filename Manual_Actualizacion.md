# Manual de actualización — Reporte de Metas ASTIN

**Centro Nacional de Asistencia Técnica a la Industria — ASTIN**
Paquete entregable de corto plazo · vigente para 2026 y años siguientes

---

## 1. Qué contiene el paquete

| Archivo | Función |
|---|---|
| `Reporte_Metas_ASTIN.pbix` | Reporte listo para abrir y compartir (6 páginas, modelo incluido). |
| `Actualizar.exe` | Motor ETL empaquetado. No requiere Python ni internet. |
| `Actualizar.bat` | Lanzador de doble clic: ejecuta el ETL, abre el PBIX y refresca. |
| `Actualizar.ps1` | Orquestador (ETL + apertura + refresco vía AMO + registro en log). |
| `config.json` | Rutas de fuentes, carpeta del proyecto, nombre del PBIX y del ejecutable. |
| `LEEME.txt` | Resumen de uso en una página. |
| `Manual_Actualizacion.md` / `.docx` | Este manual. |
| `ASTIN_Metas.pbip` + carpetas `.Report` / `.SemanticModel` | Proyecto fuente versionable (respaldo y mantenimiento). |
| `actualizar_reporte.bat`/`Generar_PBIX.ps1` | Utilidad para regenerar el `.pbix` desde el proyecto (ver sección 8). |

> El paquete **no** necesita Access, ni SQL Server, ni conexión a internet. Todo el
> procesamiento es local.

---

## 2. Requisitos

- Windows 10 u 11, 64 bits.
- **Power BI Desktop** instalado (Microsoft Store o instalador `.exe`).
- Permisos de escritura sobre la carpeta del proyecto.
- Los archivos de origen en las carpetas indicadas en `config.json`.

No se requiere:

- Python (el ETL va dentro de `Actualizar.exe`).
- Excel instalado (la lectura de `.xlsx` es directa).
- Power BI Service ni licencia Pro para actualizar el archivo local.

---

## 3. Actualización mensual (3 pasos)

### Paso 1 — Copiar los archivos del mes

| Carpeta de origen | Contenido esperado |
|---|---|
| `01_Metas` | Archivo `.xlsx` de metas del mes (hoja por estrategia/indicador). |
| `02_Reportes_PE04` | Reporte PE-04 del mes (`.xlsx` o `.csv`). |
| `03_Reportes_PE14` | Reporte PE-14 del mes (`.xlsx` o `.csv`). |

La ruta base de estas carpetas está en `config.json` → `ruta_fuentes`.
Los nombres de archivo pueden variar: el ETL los reconoce por contenido y por
periodo, no por nombre exacto.

### Paso 2 — Doble clic en `Actualizar.bat`

El proceso:

1. Ejecuta `Actualizar.exe`, que:
   - lee las tres carpetas de origen;
   - normaliza y valida la información;
   - regenera los CSV curados en `data\curated\`;
   - escribe el informe de calidad en `data\qa\informe_calidad.json`.
2. Abre `Reporte_Metas_ASTIN.pbix` si no está abierto.
3. Refresca el modelo del PBIX abierto (AMO/XMLA contra la instancia local).
4. Muestra en pantalla el resumen: periodos, filas de Metas, PE-04, PE-14, fichas.
5. Registra todo en `data\qa\actualizacion.log`.

### Paso 3 — Guardar el PBIX

En Power BI Desktop presione **Ctrl+S**.

> **Por qué es manual:** Power BI Desktop no expone una API para escribir el
> archivo `.pbix` en disco. El refresco sí es automático (vía AMO), pero la
> persistencia del archivo la hace Desktop cuando se guarda. Es un solo atajo
> de teclado.

---

## 4. Qué hace exactamente cada pieza

```
Actualizar.bat
   └─ Actualizar.ps1
        ├─ lee config.json
        ├─ ejecuta Actualizar.exe            (ETL → data\curated, data\qa)
        ├─ abre Reporte_Metas_ASTIN.pbix     (si no está abierto)
        ├─ refresco AMO (Full)               (modelo en memoria)
        └─ imprime resumen + escribe log
```

El ETL (`scripts/astin_etl.py`, empaquetado como `Actualizar.exe`):

1. Detecta los archivos de cada carpeta de origen.
2. Normaliza encabezados, tildes, tipos y periodos (`AAAAMM`).
3. Genera el modelo en estrella en `data\curated\`:
   `FactMetas`, `Fact_PE04_Fichas`, `Fact_PE14_Aprendices`, `DimPeriodo`,
   `DimCentro`, `DimCategoria`, `DimNivelFormacion`, `DimEstrategia`,
   `DimPoblacion`, `Dim_Ficha_Programa` y tablas de control/auditoría.
4. Concilia contra los totales oficiales de los encabezados y deja las
   diferencias documentadas.
5. Es **idempotente**: puede ejecutarse cuantas veces sea necesario.

---

## 5. Configuración (`config.json`)

```json
{
  "ruta_fuentes": "C:\\...\\Sistema de control e información - Estado de las metas centro ASTIN",
  "ruta_proyecto": "C:\\Users\\capatino\\Documents\\Sistema de control e información - Estado de las metas centro ASTIN",
  "anio_por_defecto": null,
  "pbix": "Reporte_Metas_ASTIN.pbix",
  "ejecutable": "Actualizar.exe"
}
```

| Campo | Uso |
|---|---|
| `ruta_fuentes` | Carpeta que contiene `01_Metas`, `02_Reportes_PE04` y `03_Reportes_PE14`. |
| `ruta_proyecto` | Carpeta del proyecto, donde se escriben `data\curated` y `data\qa`. |
| `anio_por_defecto` | `null` = usar el año del sistema. Se puede fijar, por ejemplo, `2027`. |
| `pbix` | Nombre del archivo que abre y refresca `Actualizar.ps1`. |
| `ejecutable` | Nombre del ETL empaquetado. |

Si cambia de equipo o mueve las carpetas, **solo** debe editar `config.json`.
No es necesario recompilar nada.

---

## 6. Agregar un año nuevo (2027, 2028, …)

El paquete ya está preparado para años futuros:

- El ETL calcula el periodo a partir de las fechas de los archivos; no hay
  listas de meses ni años fijas.
- En el modelo, `AnioPorDefecto` se calcula con
  `Date.Year(DateTime.LocalNow())`, por lo que el año por defecto cambia solo.
- Las rutas del modelo se derivan de dos expresiones base
  (`RutaFuentes` y `RutaProyecto`), editables sin tocar cada consulta.

Procedimiento:

1. Copie los archivos de enero 2027 en las carpetas de origen.
2. Doble clic en `Actualizar.bat`.
3. Ctrl+S en Power BI Desktop.

No hay que renombrar carpetas, ni editar el ETL, ni volver a generar el PBIX.

---

## 7. Verificación de resultados

### 7.1 Informe de calidad

Abra `data\qa\informe_calidad.json` y revise:

- `resumen.rango_periodos`: primer y último periodo cargado.
- `resumen.filas_fact_metas`, `filas_fact_pe04`, `filas_fact_pe14`, `fichas_dim`.
- Bloque de conciliación: diferencia entre la suma de indicadores y el total
  oficial del encabezado.

### 7.2 Cortes de referencia (octubre 2026)

| Indicador | Valor |
|---|---|
| Filas `FactMetas` | 88 |
| Filas `Fact_PE04_Fichas` | 3.811 |
| Filas `Fact_PE14_Aprendices` | 116.844 |
| Fichas (`Dim_Ficha_Programa`) | 3.811 |
| Desplazados por violencia (KPI, definición estricta) | 3.667 |

Si los valores cambian de forma razonable al agregar un mes, la actualización
fue correcta. Si un valor cae a cero, revise el paso 1 (archivo faltante o en la
carpeta equivocada).

### 7.3 Definición estricta de «desplazados por violencia»

La medida `Total_Desplazados_Violencia` cuenta únicamente:

- `DESPLAZADOS_POR_LA_VIOLENCIA` y `..._CABEZA_DE_FAMILIA`
- `AFROCOLOMBIANOS_DESPLAZADOS_POR_LA_VIOLENCIA` y `..._CABEZA_DE_FAMILIA`
- `INDIGENAS_DESPLAZADOS_POR_LA_VIOLENCIA` y `..._CABEZA_DE_FAMILIA`

No incluye fenómenos naturales, discapacidad ni la categoría general
`INDIGENAS`. La tarjeta muestra el total estricto (3.667 en agosto 2026) y el
gráfico de barras muestra cada categoría por separado; la barra
`DESPLAZADOS_POR_LA_VIOLENCIA` vale 2.285 por sí sola.

---

## 8. Regenerar el `.pbix` desde el proyecto

Power BI Desktop **no permite guardar un proyecto PBIP directamente como
`.pbix`**. Si necesita reconstruir el archivo:

1. Abra `ASTIN_Metas.pbip`.
2. `Archivo > Guardar como…` y elija el formato de proyecto si Desktop lo pide.
3. Alternativa recomendada: `Archivo > Exportar > Plantilla de Power BI`
   (`.pbit`), abra la plantilla y use `Archivo > Guardar como` → `.pbix`.

También puede ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File Generar_PBIX.ps1
```

El script abre el PBIP, intenta la exportación y avisa si debe completarla a
mano. El `.pbix` resultante debe llamarse `Reporte_Metas_ASTIN.pbix` y quedar en
la raíz del proyecto.

---

## 9. Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| «No se encontró config.json» | Se ejecutó el script desde otra carpeta | Ejecute `Actualizar.bat` desde la raíz del proyecto. |
| `Actualizar.exe` termina con código distinto de 0 | Archivo de origen bloqueado o corrupto | Cierre el archivo en Excel y repita. Revise el mensaje en pantalla. |
| Filas en cero para un periodo | Falta el archivo del mes o está en otra carpeta | Verifique `ruta_fuentes` y los nombres de carpeta. |
| «No se encontró el puerto local de Power BI» | El PBIX no terminó de abrir | Abra el PBIX manualmente y vuelva a ejecutar. |
| «No se encontró Power BI Desktop» | Instalación no estándar | Instale Power BI Desktop o ajuste `Actualizar.ps1`. |
| El refresco falla por rutas | Se movió la carpeta de datos curados | Actualice `RutaProyecto` en el modelo o edite `config.json` y regenere. |
| El PBIX no refleja los cambios | No se guardó | Ctrl+S en Power BI Desktop. |
| Windows bloquea el `.ps1` | Política de ejecución | Use `Actualizar.bat`, que ya invoca con `-ExecutionPolicy Bypass`. |

Registro detallado: `data\qa\actualizacion.log`.

---

## 10. Mantenimiento del paquete

### Recompilar `Actualizar.exe`

```powershell
python -m pip install pyinstaller openpyxl
python -m PyInstaller --onefile --noconfirm --clean --name Actualizar `
    --distpath build\dist --workpath build\pyinstaller --specpath build `
    scripts\astin_etl.py
copy build\dist\Actualizar.exe Actualizar.exe
```

### Regenerar el modelo/reporte desde los datos curados

```powershell
python scripts\astin_etl.py
python scripts\build_pbip.py
```

### Volver a desplegar el tablero web (opcional)

```powershell
python scripts\exportar_web.py
git add web && git commit -m "Actualiza tablero web" && git push
```
