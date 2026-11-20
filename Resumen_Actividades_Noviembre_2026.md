# Resumen de actividades de desarrollo — Noviembre 2026

**Proyecto:** Sistema de control e información — Estado de las metas Centro ASTIN
**Repositorio:** `CristianPatinho482/Dashboard-Estado-de-Metas-CENTRO`
**Rama de trabajo:** `feature/paquete-entregable`
**Periodo:** 13 al 20 de noviembre de 2026

---

## 1. Objetivo del mes

Empaquetar el Sistema de Control e Información (metas, PE-04, PE-14) en un
**paquete entregable de corto plazo** que cualquier analista pueda usar para
refrescar el reporte con los archivos nuevos de 2026 y años siguientes, sin
conocimientos técnicos. El paquete quedó integrado en una rama propia de Git
y publicado en GitHub.

---

## 2. Actividades realizadas

### 2.1 Rama y control de versiones

- Creación de la rama `feature/paquete-entregable` a partir de `b28b179`.
- Publicación de la rama en `origin` (GitHub).
- Dos commits con el paquete completo (`6f3c180`, `fa4efc2`), verificando
  `HEAD == origin/feature/paquete-entregable`.
- Exclusión en `.gitignore` de archivos locales de Power BI (`*.pbix`,
  `*.pbit`, `**/.pbi/localSettings.json`) con excepción para el entregable
  `Reporte_Metas_ASTIN.pbix`, e inclusión de `build/` y `actualizacion.log`.

### 2.2 Parametrización del ETL

- `scripts/astin_etl.py` lee ahora `config.json` (rutas de fuentes y de
  proyecto, año por defecto, nombres de PBIX y EXE).
- Soporte para ejecución congelada (`sys.frozen`) y paths relativos al
  ejecutable, para el uso dentro de `Actualizar.exe`.
- Año por defecto dinámico: `datetime.now().year`.
- Prueba end-to-end del ETL con configuración: 88 Metas · 3.811 PE-04 ·
  116.844 PE-14 · 753 fichas.

### 2.3 Parametrización del modelo (Power Query / M)

- `scripts/build_pbip.py` y `expressions.tmdl` migrados a dos expresiones
  base (`RutaFuentes`, `RutaProyecto`) y cinco expresiones derivadas
  (`RutaMetas`, `RutaPE04`, `RutaPE14`, `RutaCurados`, `AnioPorDefecto`).
- `AnioPorDefecto` se calcula con `Date.Year(DateTime.LocalNow())` (no
  requiere edición manual en 2027 ni siguientes).
- Revalidación del PBIP (apertura + refresco AMO): Metas 88, PE-04 3.811,
  PE-14 116.844, Desplazados 3.667.

### 2.4 ETL empaquetado

- Instalación de PyInstaller 6.22.3.
- Generación de `Actualizar.exe` (31,7 MB, `--onefile`), copiado a la raíz.
- Prueba exitosa ejecutando el EXE desde la carpeta del proyecto.

### 2.5 Lanzador y orquestación

- `Actualizar.ps1`: lee `config.json`, ejecuta el ETL (EXE o Python como
  respaldo), abre el PBIX si no está abierto, refresca el modelo por
  AMO/XMLA y registra el resultado en `data/qa/actualizacion.log`.
- Guardado del PBIX mediante UI Automation (botón Guardar) para no robar el
  foco del usuario.
- `Actualizar.bat`: invoca el script con `-ExecutionPolicy Bypass` y pausa
  al final.
- `Generar_PBIX.ps1`: guía la regeneración del `.pbix` desde el PBIP.

### 2.6 Reporte y modelo

- Preservación de la definición estricta de **desplazados por violencia**
  (commit `b28b179`): `Total_Desplazados_Violencia` cuenta únicamente
  violencia y variantes de cabeza de familia, incluidos afrocolombianos e
  indígenas desplazados. KPI = 3.667; barra por categoría =
  2.285.
- `Reporte_Metas_ASTIN.pbix` generado a partir del proyecto, con el modelo
  ajustado (medida + rutas), refrescado y guardado (88 / 3.811 / 116.844 /
  3.667). Archivo verificado reabriéndolo y consultando el modelo por AMO.

### 2.7 Documentación

- `LEEME.txt`: resumen de una página.
- `Manual_Actualizacion.md` (9.6 KB) y `Manual_Actualizacion.docx` (40,5 KB):
  uso mensual, configuración, años futuros, verificación de resultados,
  regeneración del PBIX y solución de problemas.
- Actualización de `docs/05_manual_actualizacion.md` para enlazar el paquete
  entregable y `Actualizar.exe`.
- Actualización de `README.md` con la sección del paquete de corto plazo.
- `Resumen_Actividades_Noviembre_2026.md` (este archivo).

### 2.8 Pruebas end-to-end

- `Actualizar.bat` ejecutado completo: ETL (EXE) + refresco AMO (6 s) +
  guardado automático del PBIX + resumen en pantalla y log.
- Verificación del PBIX reabierto: 7 expresiones, medida estricta y datos
  88 / 3.811 / 116.844 / 3.667.

---

## 3. Resultados clave

| Indicador | Valor (corte octubre 2026) |
|---|---|
| Filas `FactMetas` | 88 |
| Filas `Fact_PE04_Fichas` | 3.811 |
| Filas `Fact_PE14_Aprendices` | 116.844 |
| Fichas distintas (`fichas_dim`) | 753 |
| Desplazados por violencia (KPI, definición estricta) | 3.667 |
| Barra `DESPLAZADOS_POR_LA_VIOLENCIA` | 2.285 |

---

## 4. Limitaciones conocidas y decisiones

- **Power BI Desktop no permite guardar un proyecto PBIP directamente como
  `.pbix` por API.** El `.pbix` del paquete fue generado y verificado, pero
  para regenerarlo con cambios en el reporte (por ejemplo, el texto de
  “Notas de calidad” actualizado) se debe usar `Generar_PBIX.ps1` (3 clics).
  El `.pbix` actual conserva la redacción previa en esa caja de texto; la
  definición estricta queda documentada en el manual §7.3.
- **`config.json`** apunta a las rutas del equipo actual. Al cambiar de PC o
  mover las carpetas, solo se edita ese archivo; no hay que recompilar.
- **Año por defecto dinámico** (`Date.Year(DateTime.LocalNow())`), soportado
  hasta 2099 en el ETL.
- **Guardado manual**: el refresco es automático (AMO), pero la
  persistencia del `.pbix` la hace Power BI Desktop con `Ctrl+S`; el
  actualizador ya invoca el botón Guardar automáticamente.

---

## 5. Archivos del paquete (en la rama)

```
Actualizar.bat            Actualizar.exe            Actualizar.ps1
Generar_PBIX.ps1          LEEME.txt                Manual_Actualizacion.md
Manual_Actualizacion.docx Reporte_Metas_ASTIN.pbix config.json
```

---

## 6. Próximos pasos sugeridos

1. (Opcional) Ejecutar `Generar_PBIX.ps1` para regenerar el `.pbix` desde el
   PBIP y así incorporar la nota actualizada en el reporte.
2. Abrir una Pull Request de `feature/paquete-entregable` hacia `main` para
   fusionar el paquete.
3. Al iniciar 2027, copiar los archivos del mes en las carpetas de origen y
   ejecutar `Actualizar.bat`; no se requiere modificar código ni el PBIX.
