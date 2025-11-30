@echo off
chcp 65001 >nul
echo ========================================
echo   DIAGNOSTICO SIRIUS V4
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/5] Verificando Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python no encontrado
    pause
    exit /b 1
)
echo [OK] Python encontrado
echo.

echo [2/5] Verificando archivo .env...
if not exist ".env" (
    echo [ERROR] Archivo .env no encontrado
    echo Copia env.example a .env y configura las variables
    pause
    exit /b 1
)
echo [OK] Archivo .env encontrado
echo.

echo [3/5] Verificando dependencias...
python -c "import fastapi; import uvicorn; print('[OK] Dependencias instaladas')" 2>nul
if errorlevel 1 (
    echo [ADVERTENCIA] Algunas dependencias pueden faltar
    echo Ejecuta: pip install -r requirements.txt
)
echo.

echo [4/5] Verificando que la aplicacion se puede cargar...
python -c "import sys; sys.path.insert(0, '.'); from main import app; print('[OK] Aplicacion se puede cargar')" 2>&1
if errorlevel 1 (
    echo [ERROR] No se puede cargar la aplicacion
    echo Revisa los errores arriba
    pause
    exit /b 1
)
echo.

echo [5/5] Verificando puerto 8000...
netstat -ano | findstr ":8000" >nul
if not errorlevel 1 (
    echo [ADVERTENCIA] El puerto 8000 esta en uso
    echo Cierra otros programas que usen el puerto 8000
) else (
    echo [OK] Puerto 8000 disponible
)
echo.

echo ========================================
echo   DIAGNOSTICO COMPLETADO
echo ========================================
echo.
echo Si todo esta [OK], puedes iniciar SIRIUS con:
echo   python -m uvicorn main:app --reload
echo.
pause

