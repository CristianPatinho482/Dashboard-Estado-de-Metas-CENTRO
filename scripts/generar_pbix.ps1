param(
    [string]$Pbip = "C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN\ASTIN_Metas.pbip",
    [string]$Pbix = "C:\Users\capatino\Documents\Sistema de control e información - Estado de las metas centro ASTIN\ASTIN_Metas.pbix"
)

# Genera una copia .pbix a partir del proyecto PBIP abierto en Power BI Desktop.
# Requiere una sesión de escritorio desbloqueada. Si la automatización falla,
# guarde manualmente con Archivo > Guardar como.

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Pbip)) {
    throw "No se encontró el PBIP: $Pbip"
}

function Get-PbiProcess {
    Get-Process PBIDesktop -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
}

$pbi = Get-PbiProcess
if (-not $pbi) {
    Start-Process -FilePath $Pbip
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 2
        $pbi = Get-PbiProcess
        if ($pbi) { break }
    }
}
if (-not $pbi) {
    throw "No se pudo iniciar Power BI Desktop."
}

Start-Sleep -Seconds 25
$ws = New-Object -ComObject WScript.Shell
$ws.AppActivate($pbi.Id) | Out-Null
Start-Sleep -Seconds 1

# Alt+F abre Archivo; A selecciona Guardar como en la cinta en español.
$ws.SendKeys("%f")
Start-Sleep -Seconds 2
$ws.SendKeys("a")
Start-Sleep -Seconds 3

# Si apareció el diálogo clásico, escribir la ruta completa.
Set-Clipboard -Value $Pbix
$ws.SendKeys("^v")
Start-Sleep -Seconds 1
$ws.SendKeys("{ENTER}")
Start-Sleep -Seconds 10

if (Test-Path -LiteralPath $Pbix) {
    Write-Host "PBIX generado: $Pbix" -ForegroundColor Green
    exit 0
}

Write-Warning "No se pudo confirmar la creación automática del PBIX."
Write-Host "Abra el PBIP y use Archivo > Guardar como, seleccionando el formato PBIX." -ForegroundColor Yellow
Write-Host "Ruta sugerida: $Pbix"
exit 1
