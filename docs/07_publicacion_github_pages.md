# Publicación en GitHub Pages

## 1. Aclaración importante

GitHub Pages **solo publica archivos estáticos** (HTML, CSS, JavaScript, JSON, imágenes). No puede ejecutar Power BI ni abrir un `.pbix`/`.pbip` directamente.

Por eso el proyecto incluye dos caminos:

| Camino | Qué se publica | Cuándo usarlo |
|---|---|---|
| **A. Tablero web estático** (recomendado para GitHub Pages) | `web/index.html` + `web/datos.js` + Chart.js | Difusión pública o institucional sin licencias de Power BI. |
| **B. Power BI Service embebido** | Un iframe de un informe publicado en Power BI | Cuando se requiere el reporte interactivo original y se cuenta con licencia/capacidad. |

El tablero web se genera desde los mismos CSV curados del modelo, por lo que las cifras coinciden con el reporte de Power BI.

---

## 2. Opción A — Tablero web estático

### 2.1 Archivos

```text
web/
├── index.html          # tablero (6 secciones)
├── datos.js            # datos agregados (window.ASTIN_DATA)
├── datos.json          # misma data para consumo externo
└── chart.umd.min.js    # Chart.js local, sin CDN
```

### 2.2 Generar/actualizar los datos

Cada vez que cambien los CSV curados:

```powershell
python scripts\exportar_web.py
```

Esto reescribe `web/datos.js` y `web/datos.json` con los agregados de metas, PE-04, PE-14, control y auditoría. No incluye nombres, documentos ni datos personales.

### 2.3 Probar localmente

Abra `web/index.html` con doble clic. Como los datos están en `datos.js` (no en un `fetch`), funciona sin servidor local.

Si prefiere servidor:

```powershell
cd web
python -m http.server 8000
```

Visite `http://localhost:8000`.

### 2.4 Publicar con GitHub Actions

El workflow ya está en `.github/workflows/pages.yml`. Hace:

1. Checkout del repositorio.
2. Instala Python y dependencias.
3. Ejecuta `scripts/exportar_web.py`.
4. Sube la carpeta `web` como artefacto de Pages.
5. Despliega en GitHub Pages.

Pasos en GitHub:

1. Suba el proyecto al repositorio:

   ```powershell
   cd "C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN"
   git add .
   git commit -m "Tablero web y despliegue GitHub Pages"
   git push origin main
   ```

2. En GitHub, entre a **Settings → Pages**.
3. En **Build and deployment → Source**, seleccione **GitHub Actions**.
4. Espere el workflow **Deploy GitHub Pages** en la pestaña **Actions**.
5. La URL será:

   ```text
   https://<usuario>.github.io/<repositorio>/
   ```

   Para este repositorio:

   ```text
   https://cristianpatinho482.github.io/Dashboard-Estado-de-Metas-CENTRO/
   ```

### 2.5 Actualización automática

Cada `push` a `main` que modifique `web/`, `data/curated/`, `scripts/exportar_web.py` o el workflow vuelve a generar y desplegar el sitio. También puede ejecutarlo manualmente desde **Actions → Deploy GitHub Pages → Run workflow**.

Flujo mensual recomendado:

```text
Nuevo archivo en 01/02/03
        ↓
python scripts/astin_etl.py
        ↓
python scripts/exportar_web.py
        ↓
git add data/curated web/datos.js web/datos.json
git commit -m "Nuevo corte YYYY-MM"
git push
        ↓
GitHub Actions publica
```

### 2.6 Dominio personalizado (opcional)

1. Cree un archivo `web/CNAME` con el dominio, por ejemplo:

   ```text
   metas-astin.sena.edu.co
   ```

2. Configure el DNS del dominio:
   - `CNAME` para `www` apuntando a `<usuario>.github.io`.
   - Registros `A` para el dominio raíz a las IP de GitHub Pages.
3. En **Settings → Pages → Custom domain**, escriba el dominio y active HTTPS.

---

## 3. Opción B — Informe de Power BI embebido

Si necesita el reporte interactivo original:

1. Publique el PBIX en un espacio de trabajo de Power BI Service.
2. Use **Archivo → Insertar informe → Publicar en la web** (genera un enlace público) o **Insertar** (requiere autenticación).
3. Copie el iframe y insértelo en una página de GitHub Pages:

```html
<iframe title="Estado de las metas ASTIN"
        width="100%" height="720"
        src="https://app.powerbi.com/view?r=XXXXXXXX"
        frameborder="0" allowFullScreen="true"></iframe>
```

Advertencias:

- **Publicar en la web** hace el informe accesible a cualquier persona con el enlace. No lo use con datos sensibles.
- **Insertar** requiere que el visitante inicie sesión en Power BI y tenga permisos sobre el espacio de trabajo.
- GitHub Pages no puede autenticar usuarios de Power BI; la seguridad depende del enlace/embed de Power BI.

---

## 4. Seguridad y visibilidad

- El tablero web publica **conteos agregados** por periodo, nivel, programa y población; no incluye nombres, documentos, correos ni datos individuales.
- Aun así, revise la política de publicación de información del SENA antes de hacer público el repositorio.
- Si el repositorio es privado, GitHub Pages puede requerir un plan de pago (Pro/Team/Enterprise) y la configuración de visibilidad del sitio. Verifique la disponibilidad en su organización.
- Para uso interno, considere GitHub Enterprise Cloud con Pages privadas o un servidor institucional.

---

## 5. Solución de problemas

| Síntoma | Causa | Acción |
|---|---|---|
| El workflow falla en `exportar_web.py` | Faltan CSV curados | Ejecute `python scripts/astin_etl.py` y haga commit de `data/curated`. |
| La página queda en blanco | `datos.js` no se generó o hay error JS | Abra la consola del navegador; ejecute `python scripts/exportar_web.py`. |
| 404 en GitHub Pages | Pages no está en “GitHub Actions” o el workflow no terminó | Revise **Settings → Pages** y **Actions**. |
| Los datos no cambian | El push no incluyó `data/curated` o `web/datos.js` | Haga commit de ambos o deje que el workflow los regenere. |
| El sitio no carga Chart.js | Falta `web/chart.umd.min.js` | Copie el archivo o cámbielo por un CDN. |
