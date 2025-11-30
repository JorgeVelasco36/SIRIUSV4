@echo off
echo ========================================
echo     ACTIVANDO SIRIUS V4
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/3] Verificando entorno...
python --version
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Por favor instala Python 3.10+
    pause
    exit /b 1
)

echo.
echo [2/3] Verificando configuracion...
if not exist ".env" (
    echo [ERROR] Archivo .env no encontrado en la carpeta backend
    echo Por favor copia env.example a .env y configura las variables
    pause
    exit /b 1
)

echo.
echo [3/3] Iniciando servidor SIRIUS...
echo.
echo ========================================
echo   SIRIUS V4 se esta iniciando...
echo ========================================
echo.
echo URLs disponibles:
echo   - Interfaz web: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Health: http://localhost:8000/health
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

