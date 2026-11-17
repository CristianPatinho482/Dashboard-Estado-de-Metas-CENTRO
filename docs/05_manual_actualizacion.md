# Manual de actualización

> **Paquete entregable (uso operativo):** para la actualización mensual use
> `Actualizar.bat` en la raíz del proyecto. No requiere Python. Consulte
> `LEEME.txt` o `Manual_Actualizacion.md`. Esta guía describe el detalle
> técnico del ETL y del modelo.

## 1. Agregar un mes nuevo

### Metas (01_Metas)

Copie el archivo del mes en `01_Metas`. El nombre debe contener el mes y el año (por ejemplo `METAS FORMACION NOVIEMBRE 30 - 2026.xlsx`). El ETL reconoce los layouts:

- vertical con columnas `INDICADOR | Meta 2026 | Ejecución | % Ejecución | Estado`;
- vertical antiguo con `Metas Formación Profesional Integral | Meta | Ejecución | % Ejecución`;
- archivos con dos cortes (p. ej. 20 y 30 de abril): se conserva el corte de mayor día.

Si el archivo no tiene mes/año, se omite y queda registrado en `data/qa/auditoria_ingesta.csv`.

### PE-04 (02_Reportes_PE04)

Copie el `.xlsx` mensual. El ETL lee la hoja `Reporte`, detecta el periodo en la fila 3 (`YYYYMM`) y toma las columnas de ficha, matrícula, activos y horas. También acepta `.csv` curados con el contrato de `data/curated/pe04/`.

### PE-14 (03_Reportes_PE14)

Copie el `.xlsx` mensual. El ETL lee la hoja `Hoja1`, detecta las 52 columnas `*_Total_Aprendices` y desdinamiza. Las columnas de género no se suman para evitar duplicar personas.

## 2. Ejecutar el ETL

Opción empaquetada (recomendada, sin Python):

```powershell
.\Actualizar.exe
```

Opción con Python (desarrollo):

```powershell
cd "C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN"
python scripts\astin_etl.py
```

Ambas leen las rutas desde `config.json` (`ruta_fuentes`, `ruta_proyecto`) y el
año por defecto del sistema (`anio_por_defecto: null`).

Salidas:

- `data/curated/fact_metas.csv`, `fact_pe04_fichas.csv`, `fact_pe14_aprendices.csv`.
- `data/curated/metas/metas_curated_YYYY_MM.csv`, `pe04/pe04_curated_YYYY_MM.csv`, `pe14/pe14_curated_YYYY_MM.csv`.
- `data/curated/dim_*.csv`, `control_metas.csv`.
- `data/qa/auditoria_ingesta.csv`, `data/qa/informe_calidad.json`.

Revise el informe de calidad: diferencias entre suma de indicadores y total oficial, fichas PE-14 sin dimensión, cancelados negativos y horas.

## 3. Actualizar Power BI

Abra `ASTIN_Metas.pbip` y use `Inicio > Actualizar`. El modelo lee todos los CSV de `data/curated/metas`, `pe04` y `pe14`; no hay que agregar consultas.

Si el tablero ya está abierto, puede refrescar por XMLA/AMO con:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\vigilar_y_actualizar.ps1
```

o dejar el vigilante activo; detectará cambios en las tres carpetas y refrescará solo.

## 4. Generar el PBIX

Con el PBIP abierto en Power BI Desktop:

1. `Archivo > Guardar como`.
2. Elija la carpeta del proyecto.
3. En el nombre escriba `ASTIN_Metas.pbix`.
4. Guarde.

O ejecute:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generar_pbix.ps1
```

> El PBIP es el formato nativo versionable; el PBIX es la copia binaria para distribuir. Ambos contienen el mismo modelo y reporte.

## 5. Programar la actualización

### Opción A — Vigilante en tiempo real

```powershell
powershell -ExecutionPolicy Bypass -File scripts\vigilar_y_actualizar.ps1
```

Mantenga la ventana abierta (o ejecútela al iniciar sesión). El log está en `data/qa/vigilante.log`.

### Opción B — Programador de tareas

Cree una tarea que ejecute cada 30 minutos:

```powershell
python "C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN\scripts\astin_etl.py"
```

Power BI Desktop no se puede refrescar de forma desatendida sin el archivo abierto; para publicación, use un modelo en el servicio con credenciales de puerta de enlace y programe la actualización en el espacio de trabajo.

## 6. Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| Un mes no aparece | Nombre sin mes/año o layout no reconocido | Revise `data/qa/auditoria_ingesta.csv`; renombre el archivo con el mes. |
| Meta total no coincide con el archivo | Filas de estrategia (CampeSENA/FEP) reportadas por separado | Use la página *Calidad y auditoría*; la diferencia está documentada. |
| PE-14 no cuadra con PE-04 | PE-14 es mensual y puede faltar un mes | Revise la cobertura en la página de calidad. |
| Error de privacidad al refrescar | Fuentes locales con niveles de privacidad | El modelo incluye `PBI_IgnorePrivacyLevels = true`; si persiste, `Archivo > Opciones > Privacidad > Ignorar`. |
| El PBIX no se generó | Sesión de escritorio bloqueada o diálogo cancelado | Desbloquee Windows y ejecute `scripts\generar_pbix.ps1` o guarde como desde Power BI. |
