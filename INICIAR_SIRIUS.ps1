# Script para iniciar SIRIUS V4
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "     ACTIVANDO SIRIUS V4" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio backend
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend"

if (-not (Test-Path $backendPath)) {
    Write-Host "[ERROR] No se encuentra la carpeta backend" -ForegroundColor Red
    exit 1
}

Set-Location $backendPath
Write-Host "[1/4] Directorio cambiado a: $backendPath" -ForegroundColor Gray
Write-Host ""

# Verificar Python
Write-Host "[2/4] Verificando Python..." -ForegroundColor Gray
try {
    $pythonVersion = python --version 2>&1
    Write-Host "       $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python no encontrado. Por favor instala Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verificar .env
Write-Host "[3/4] Verificando configuracion..." -ForegroundColor Gray
if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] Archivo .env no encontrado en la carpeta backend" -ForegroundColor Red
    Write-Host "       Copia env.example a .env y configura las variables" -ForegroundColor Yellow
    exit 1
}
Write-Host "       Archivo .env encontrado" -ForegroundColor Green
Write-Host ""

# Iniciar servidor
Write-Host "[4/4] Iniciando servidor SIRIUS..." -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SIRIUS V4 SE ESTA INICIANDO..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs disponibles:" -ForegroundColor Cyan
Write-Host "  - Interfaz web: http://localhost:8000" -ForegroundColor Yellow
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Iniciar uvicorn
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

