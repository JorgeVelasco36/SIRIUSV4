# 🔧 Solución: No puedo ver SIRIUS en el navegador

## 🎯 Pasos para resolver el problema

### Paso 1: Detener procesos anteriores

Abre PowerShell y ejecuta:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Paso 2: Iniciar SIRIUS correctamente

**Opción A - Usando el script PowerShell (Recomendado):**

```powershell
cd "C:\Users\JEVD4139\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4"
.\INICIAR_SIRIUS.ps1
```

**Opción B - Manualmente:**

```powershell
cd "C:\Users\JEVD4139\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4\backend"
python -m uvicorn main:app --reload
```

### Paso 3: Esperar a que aparezca este mensaje

Deberías ver en la terminal algo como:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Paso 4: Abrir el navegador

Una vez que veas el mensaje "Application startup complete", abre tu navegador en:

**http://localhost:8000**

---

## ✅ Verificar que está funcionando

Abre una **nueva** ventana de PowerShell y ejecuta:

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

Si responde con `{"status":"healthy"}`, ¡está funcionando!

---

## 🔍 Solución de problemas comunes

### Problema 1: "El puerto 8000 está en uso"

**Solución:**

```powershell
# Encontrar qué proceso está usando el puerto
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# Detener el proceso (reemplaza PID con el número que veas)
Stop-Process -Id PID -Force
```

### Problema 2: "No module named 'main'"

**Solución:**

Asegúrate de estar en la carpeta `backend` antes de ejecutar:

```powershell
cd backend
python -m uvicorn main:app --reload
```

### Problema 3: "ModuleNotFoundError"

**Solución:**

Instala las dependencias:

```powershell
cd backend
pip install -r requirements.txt
```

### Problema 4: La página carga pero está en blanco

**Solución:**

1. Abre la consola del navegador (F12)
2. Revisa si hay errores en la consola
3. Verifica que los archivos estáticos carguen:
   - http://localhost:8000/static/css/style.css
   - http://localhost:8000/static/js/app.js

---

## 📝 Notas importantes

- **No cierres la ventana de PowerShell** donde está corriendo el servidor
- Si cierras la ventana, el servidor se detendrá
- Para detener el servidor, presiona `Ctrl+C` en la ventana donde está corriendo

---

## 🆘 Si nada funciona

1. Verifica que Python esté instalado:
   ```powershell
   python --version
   ```

2. Verifica la configuración:
   ```powershell
   python scripts/verify_env.py
   ```

3. Verifica que no haya errores al importar:
   ```powershell
   cd backend
   python -c "from main import app; print('OK')"
   ```

---

*Última actualización: 29 de noviembre de 2025*

