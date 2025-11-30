@echo off
chcp 65001 >nul
echo ========================================
echo   VERIFICACION COMPLETA DE SIRIUS V4
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/7] Verificando Python...
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python no encontrado
    echo        Instala Python desde python.org
    goto :end
)
echo [OK] Python encontrado
echo.

echo [2/7] Verificando archivo .env...
if not exist ".env" (
    echo [ERROR] Archivo .env no encontrado
    echo        Copia env.example a .env y configura las variables necesarias
    goto :end
)
echo [OK] Archivo .env encontrado
echo.

echo [3/7] Verificando OPENAI_API_KEY...
findstr /C:"OPENAI_API_KEY=" .env | findstr /V "^#" | findstr /V "tu_openai" >nul
if errorlevel 1 (
    echo [ERROR] OPENAI_API_KEY no configurada o es un placeholder
    echo        Edita el archivo .env y configura tu OPENAI_API_KEY
    goto :end
)
echo [OK] OPENAI_API_KEY configurada
echo.

echo [4/7] Verificando dependencias...
python -c "import fastapi, uvicorn, sqlalchemy; print('[OK] Dependencias principales instaladas')" 2>nul
if errorlevel 1 (
    echo [ERROR] Faltan dependencias
    echo        Ejecuta: pip install -r requirements.txt
    goto :end
)
echo [OK] Dependencias instaladas
echo.

echo [5/7] Verificando que la aplicacion se puede cargar...
python -c "import sys; sys.path.insert(0, '.'); from main import app; print('[OK] Aplicacion se puede cargar')" 2>nul
if errorlevel 1 (
    echo [ERROR] No se puede cargar la aplicacion
    echo        Revisa los errores arriba
    goto :end
)
echo [OK] Aplicacion se puede cargar
echo.

echo [6/7] Verificando puerto 8000...
netstat -ano | findstr ":8000" >nul
if not errorlevel 1 (
    echo [ADVERTENCIA] El puerto 8000 esta en uso
    echo               Esto puede impedir que SIRIUS inicie
    echo               Usa este comando para ver que proceso lo usa:
    echo               netstat -ano ^| findstr ":8000"
) else (
    echo [OK] Puerto 8000 disponible
)
echo.

echo [7/7] Verificando archivos estaticos y templates...
if not exist "static\css\style.css" (
    echo [ERROR] Archivo static\css\style.css no encontrado
    goto :end
)
if not exist "templates\base.html" (
    echo [ERROR] Archivo templates\base.html no encontrado
    goto :end
)
echo [OK] Archivos estaticos y templates encontrados
echo.

echo ========================================
echo   VERIFICACION COMPLETADA
echo ========================================
echo.
echo Si todo esta [OK], puedes iniciar SIRIUS con:
echo   INICIAR_SIRIUS_SIMPLE.bat
echo.
echo O manualmente desde PowerShell:
echo   cd backend
echo   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Luego abre tu navegador en: http://localhost:8000
echo.

:end
pause

