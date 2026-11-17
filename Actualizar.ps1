param(
    [string]$Pbix = ""
)

# Actualiza el reporte completo:
#   1. Ejecuta el ETL empaquetado (Actualizar.exe) o el script Python.
#   2. Abre el PBIX si no está abierto.
#   3. Refresca el modelo por AMO/XMLA.
#   4. Intenta guardar el PBIX.
#
# Requiere Power BI Desktop instalado y una sesión de Windows desbloqueada.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root "data\qa"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir "actualizacion.log"

function Write-Log([string]$Message) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $Message"
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}

function Read-Config {
    $path = Join-Path $Root "config.json"
    if (-not (Test-Path -LiteralPath $path)) {
        throw "No se encontró config.json en $Root"
    }
    return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Get-PbiBin {
    $pkg = Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop -ErrorAction SilentlyContinue
    if ($pkg) { return (Join-Path $pkg.InstallLocation "bin") }
    $alt = "C:\Program Files\Microsoft Power BI Desktop\bin"
    if (Test-Path -LiteralPath $alt) { return $alt }
    throw "No se encontró Power BI Desktop."
}

function Get-PbiPort {
    $bases = @(
        (Join-Path $env:USERPROFILE "Microsoft\Power BI Desktop Store App\AnalysisServicesWorkspaces"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\Power BI Desktop\AnalysisServicesWorkspaces")
    )
    foreach ($base in $bases) {
        if (-not (Test-Path -LiteralPath $base)) { continue }
        $pf = Get-ChildItem $base -Recurse -Filter "msmdsrv.port.txt" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($pf) {
            return ((Get-Content $pf.FullName) -replace "`0", "").Trim()
        }
    }
    return $null
}

function Invoke-Refresh {
    $port = Get-PbiPort
    if (-not $port) { throw "No se encontró el puerto local de Power BI. Abra el PBIX y reintente." }

    $bin = Get-PbiBin
    [System.Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Amo.Core.dll")) | Out-Null
    [System.Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Amo.dll")) | Out-Null
    [System.Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Tabular.dll")) | Out-Null

    $server = New-Object Microsoft.AnalysisServices.Server
    try {
        $server.Connect("localhost:$port")
        if ($server.Databases.Count -eq 0) { throw "No hay una base de datos abierta en Power BI." }
        $db = $server.Databases[0]
        Write-Log "Refrescando modelo '$($db.Name)' en el puerto $port..."
        $db.Model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
        $db.Model.SaveChanges()
        Write-Log "Modelo refrescado correctamente."
    } finally {
        if ($server.Connected) { $server.Disconnect() }
    }
}

function Save-Pbix {
    # Guarda el PBIX invocando el botón "Guardar" por UI Automation, sin robar
    # el foco del usuario. Si no es posible, solicita el guardado manual.
    $proc = Get-Process PBIDesktop -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if (-not $proc) { return }
    try {
        Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
        $w = [System.Windows.Automation.AutomationElement]::FromHandle($proc.MainWindowHandle)
        $cond = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::AutomationIdProperty, 'save')
        $btn = $w.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
        if ($btn) {
            $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
            Start-Sleep -Seconds 8
            Write-Log "PBIX guardado automáticamente."
        } else {
            Write-Log "No se encontró el botón Guardar. Guarde con Ctrl+S en Power BI Desktop."
        }
    } catch {
        Write-Log "No se pudo guardar automáticamente el PBIX: $($_.Exception.Message). Use Ctrl+S."
    }
}

try {
    Write-Log "===== Inicio de actualización ====="
    $config = Read-Config
    $exe = Join-Path $Root "Actualizar.exe"
    if (Test-Path -LiteralPath $exe) {
        Write-Log "Ejecutando ETL empaquetado..."
        & $exe
        if ($LASTEXITCODE -ne 0) { throw "Actualizar.exe terminó con código $LASTEXITCODE." }
    } else {
        Write-Log "Actualizar.exe no encontrado; usando Python..."
        & python (Join-Path $Root "scripts\astin_etl.py")
        if ($LASTEXITCODE -ne 0) { throw "El ETL terminó con código $LASTEXITCODE." }
    }

    $pbixName = if ($Pbix) { $Pbix } elseif ($config.pbix) { $config.pbix } else { "Reporte_Metas_ASTIN.pbix" }
    if (-not [System.IO.Path]::IsPathRooted($pbixName)) { $pbixName = Join-Path $Root $pbixName }
    if (-not (Test-Path -LiteralPath $pbixName)) {
        throw "No se encontró el PBIX: $pbixName"
    }

    $pbi = Get-Process PBIDesktop -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if (-not $pbi) {
        Write-Log "Abriendo PBIX..."
        Start-Process -FilePath $pbixName
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 2
            $pbi = Get-Process PBIDesktop -ErrorAction SilentlyContinue |
                Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
            if ($pbi) { break }
        }
        Start-Sleep -Seconds 20
    }

    Invoke-Refresh
    Save-Pbix

    $qa = Join-Path $Root "data\qa\informe_calidad.json"
    if (Test-Path -LiteralPath $qa) {
        $info = Get-Content -LiteralPath $qa -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host ""
        Write-Host "Resumen de la actualización:" -ForegroundColor Green
        Write-Host "  Periodos: $($info.resumen.rango_periodos -join ' a ')"
        Write-Host "  Filas Metas: $($info.resumen.filas_fact_metas)"
        Write-Host "  Filas PE-04: $($info.resumen.filas_fact_pe04)"
        Write-Host "  Filas PE-14: $($info.resumen.filas_fact_pe14)"
        Write-Host "  Fichas: $($info.resumen.fichas_dim)"
        Write-Host "  Informe completo: data\qa\informe_calidad.json"
    }
    Write-Log "===== Actualización finalizada ====="
    exit 0
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
