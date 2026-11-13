param(
    [string]$Proyecto = "C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN",
    [string]$Fuente = "C:\Users\capatino\OneDrive - Servicio Nacional de Aprendizaje\BACKUP DISCO\Mis proyectos\AREA LABORAL\SENA\POWER BI\Sistema de control e información - Estado de las metas centro ASTIN"
)

# Vigila las tres carpetas de origen, ejecuta el ETL y refresca el modelo abierto
# en Power BI Desktop mediante AMO/XMLA. No requiere interacción del usuario.

$ErrorActionPreference = "Stop"
$log = Join-Path $Proyecto "data\qa\vigilante.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

function Write-Log([string]$mensaje) {
    $linea = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $mensaje"
    Add-Content -Path $log -Value $linea -Encoding UTF8
    Write-Host $linea
}

function Invoke-Etl {
    Write-Log "Ejecutando ETL..."
    $salida = & python (Join-Path $Proyecto "scripts\astin_etl.py") 2>&1
    $codigo = $LASTEXITCODE
    Add-Content -Path $log -Value $salida -Encoding UTF8
    if ($codigo -ne 0) {
        Write-Log "ETL falló con código $codigo"
        return $false
    }
    Write-Log "ETL completado."
    return $true
}

function Get-PbiPort {
    $base = Join-Path $env:USERPROFILE "Microsoft\Power BI Desktop Store App\AnalysisServicesWorkspaces"
    if (-not (Test-Path $base)) { return $null }
    $pf = Get-ChildItem $base -Recurse -Filter "msmdsrv.port.txt" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $pf) { return $null }
    return ((Get-Content $pf.FullName) -replace "`0", "").Trim()
}

function Invoke-RefreshPbi {
    $port = Get-PbiPort
    if (-not $port) {
        Write-Log "Power BI Desktop no está abierto o no se encontró el puerto local. Se omite el refresco."
        return
    }
    $pkg = Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop -ErrorAction SilentlyContinue
    if (-not $pkg) {
        Write-Log "No se encontró la instalación de Power BI Desktop."
        return
    }
    $bin = Join-Path $pkg.InstallLocation "bin"
    [System.Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Amo.Core.dll")) | Out-Null
    [System.Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Amo.dll")) | Out-Null
    [System.Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Tabular.dll")) | Out-Null
    $server = New-Object Microsoft.AnalysisServices.Server
    try {
        $server.Connect("localhost:$port")
        $db = $server.Databases[0]
        $db.Model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
        $db.Model.SaveChanges()
        Write-Log "Modelo refrescado correctamente (puerto $port)."
    } catch {
        Write-Log "Error al refrescar: $($_.Exception.Message)"
    } finally {
        if ($server.Connected) { $server.Disconnect() }
    }
}

$pendiente = $false
$ultimo = Get-Date

$watchers = @()
foreach ($sub in @("01_Metas", "02_Reportes_PE04", "03_Reportes_PE14")) {
    $ruta = Join-Path $Fuente $sub
    if (-not (Test-Path $ruta)) {
        Write-Log "Carpeta no encontrada: $ruta"
        continue
    }
    $w = New-Object System.IO.FileSystemWatcher $ruta
    $w.IncludeSubdirectories = $false
    $w.EnableRaisingEvents = $true
    $w.NotifyFilter = [System.IO.NotifyFilters]'FileName, LastWrite, Size'
    $accion = {
        $global:pendiente = $true
        $global:ultimo = Get-Date
    }
    Register-ObjectEvent $w Changed -Action $accion | Out-Null
    Register-ObjectEvent $w Created -Action $accion | Out-Null
    Register-ObjectEvent $w Renamed -Action $accion | Out-Null
    $watchers += $w
}

Write-Log "Vigilante iniciado. Carpetas: 01_Metas, 02_Reportes_PE04, 03_Reportes_PE14."
Write-Log "Presione Ctrl+C para detener."

try {
    while ($true) {
        Start-Sleep -Seconds 3
        if ($global:pendiente -and ((Get-Date) - $global:ultimo).TotalSeconds -ge 10) {
            $global:pendiente = $false
            Write-Log "Cambio detectado en las fuentes."
            if (Invoke-Etl) {
                Invoke-RefreshPbi
            }
        }
    }
} finally {
    foreach ($w in $watchers) {
        $w.EnableRaisingEvents = $false
        $w.Dispose()
    }
    Get-EventSubscriber | Unregister-Event -ErrorAction SilentlyContinue
    Write-Log "Vigilante detenido."
}
