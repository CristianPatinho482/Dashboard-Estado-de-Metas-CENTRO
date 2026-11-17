param(
    [switch]$Auto
)

# Genera Reporte_Metas_ASTIN.pbix a partir del proyecto PBIP.
#
# Power BI Desktop no permite guardar un proyecto PBIP directamente como .pbix.
# Este script abre el proyecto y guía la exportación (3 clics).
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File Generar_PBIX.ps1
#
# Requiere una sesión de escritorio desbloqueada.

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pbip = Join-Path $Root 'ASTIN_Metas.pbip'
$Pbix = Join-Path $Root 'Reporte_Metas_ASTIN.pbix'

if (-not (Test-Path -LiteralPath $Pbip)) {
    throw "No se encontró el proyecto: $Pbip"
}

if (Test-Path -LiteralPath $Pbix) {
    $info = Get-Item -LiteralPath $Pbix
    Write-Host "Ya existe: $($info.FullName)" -ForegroundColor Green
    Write-Host "  Tamaño: $($info.Length) bytes | Modificado: $($info.LastWriteTime)"
    $resp = Read-Host '¿Desea regenerarlo igualmente? (s/N)'
    if ($resp -notmatch '^[sS]') { exit 0 }
    Rename-Item -LiteralPath $Pbix -NewName ("Reporte_Metas_ASTIN_{0}.bak" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
}

Write-Host ''
Write-Host 'Abriendo el proyecto en Power BI Desktop...' -ForegroundColor Cyan
Start-Process -FilePath $Pbip
Start-Sleep -Seconds 30

Write-Host ''
Write-Host 'Complete la exportación en Power BI Desktop:' -ForegroundColor Yellow
Write-Host '  1) Archivo > Exportar > Plantilla de Power BI'
Write-Host '  2) Guarde la plantilla como  Reporte_Metas_ASTIN.pbit  (en esta carpeta)'
Write-Host '  3) Abra ese .pbit (doble clic)'
Write-Host '  4) Archivo > Guardar como > elija el formato PBIX'
Write-Host "  5) Guarde como  $Pbix"
Write-Host ''
Write-Host 'Cuando termine, presione ENTER para verificar...' -ForegroundColor Yellow
Read-Host | Out-Null

if (Test-Path -LiteralPath $Pbix) {
    $info = Get-Item -LiteralPath $Pbix
    Write-Host ''
    Write-Host "PBIX generado correctamente: $($info.FullName)" -ForegroundColor Green
    Write-Host "  Tamaño: $($info.Length) bytes"
    exit 0
}

Write-Host ''
Write-Warning "No se encontró $Pbix"
Write-Host 'Verifique que guardó con el nombre y en la carpeta indicados.' -ForegroundColor Yellow
exit 1
