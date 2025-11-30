@echo off
chcp 65001 >nul
echo ========================================
echo   REINICIANDO SIRIUS V4
echo ========================================
echo.

echo [1/3] Deteniendo procesos en puerto 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo   Cerrando proceso PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [2/3] Esperando 2 segundos...
timeout /t 2 /nobreak >nul

echo.
echo [3/3] Iniciando SIRIUS...
cd backend
start "SIRIUS Server" cmd /k "python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

echo.
echo ========================================
echo   SIRIUS reiniciado exitosamente
echo ========================================
echo.
echo   El servidor se abrio en una nueva ventana.
echo   Espera unos segundos y luego abre:
echo.
echo   http://localhost:8000
echo.
echo   IMPORTANTE: No cierres la ventana del servidor
echo.
pause

