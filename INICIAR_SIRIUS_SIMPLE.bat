@echo off
chcp 65001 >nul
echo ========================================
echo     ACTIVANDO SIRIUS V4
echo ========================================
echo.

cd /d "%~dp0backend"

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.
echo ========================================
echo   Iniciando servidor...
echo ========================================
echo.
echo URLs disponibles:
echo   - Interfaz web: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo IMPORTANTE: Mantén esta ventana abierta
echo Para detener el servidor, presiona Ctrl+C
echo.
echo ========================================
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

