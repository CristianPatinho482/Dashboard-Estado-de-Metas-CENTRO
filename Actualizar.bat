@echo off
chcp 65001 >nul
title Actualizar Reporte de Metas ASTIN
echo.
echo ============================================================
echo   ACTUALIZACION DEL REPORTE DE METAS - CENTRO ASTIN
echo ============================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Actualizar.ps1" %*
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (
  echo Proceso terminado. Recuerde guardar en Power BI Desktop con Ctrl+S.
) else (
  echo El proceso termino con errores. Revise data\qa\actualizacion.log
)
echo.
pause
exit /b %RC%
