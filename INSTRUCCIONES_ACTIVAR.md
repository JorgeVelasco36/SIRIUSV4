# 🚀 Instrucciones para Activar SIRIUS V4

## ⚠️ IMPORTANTE: El servidor DEBE iniciarse manualmente

El servidor de SIRIUS **NO** puede ejecutarse en segundo plano sin que veas la salida. Debes iniciarlo tú mismo desde una ventana de terminal.

---

## 📋 Pasos para Activar SIRIUS

### Paso 1: Abrir PowerShell o Terminal

Abre una nueva ventana de **PowerShell** o **Símbolo del sistema** (cmd).

### Paso 2: Navegar al proyecto

Copia y pega este comando:

```powershell
cd "C:\Users\JEVD4139\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4\backend"
```

### Paso 3: Iniciar el servidor

Copia y pega este comando:

```powershell
python -m uvicorn main:app --reload
```

### Paso 4: Esperar el mensaje de inicio

Deberías ver algo como esto:

```
INFO:     Will watch for changes in these directories: ['C:\\Users\\...']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**⚠️ IMPORTANTE:** Cuando veas "Application startup complete", el servidor está listo.

### Paso 5: Abrir el navegador

Una vez que veas el mensaje "Application startup complete", abre tu navegador y ve a:

**http://localhost:8000**

---

## 🎯 Alternativa: Usar el script .bat

También puedes hacer **doble clic** en el archivo:

**`INICIAR_SIRIUS_SIMPLE.bat`**

Este archivo hará todo automáticamente.

---

## ✅ Verificar que está funcionando

Abre **otra** ventana de PowerShell y ejecuta:

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health"
```

Si ves `{"status":"healthy"}`, ¡está funcionando!

---

## 🔍 Solución de Problemas

### Problema: "python no se reconoce como comando"

**Solución:**
- Verifica que Python esté instalado: `python --version`
- Si no está instalado, instálalo desde python.org
- O prueba con `py` en lugar de `python`: `py -m uvicorn main:app --reload`

### Problema: "No module named 'fastapi'"

**Solución:**
```powershell
cd backend
pip install -r requirements.txt
```

### Problema: "El puerto 8000 está en uso"

**Solución:**
```powershell
# Encontrar qué usa el puerto
netstat -ano | findstr :8000

# Detener el proceso (reemplaza PID con el número que veas)
taskkill /PID <PID> /F
```

### Problema: La página carga pero está en blanco

**Solución:**
1. Abre la consola del navegador (presiona F12)
2. Ve a la pestaña "Console"
3. Busca errores en rojo
4. Prueba recargar la página (F5 o Ctrl+R)

### Problema: "ModuleNotFoundError" o errores de importación

**Solución:**
1. Asegúrate de estar en la carpeta `backend`
2. Verifica que todas las dependencias estén instaladas:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 📝 Notas Importantes

1. **NO cierres la ventana de PowerShell** donde está corriendo el servidor
   - Si cierras la ventana, el servidor se detendrá
   - Debes mantenerla abierta mientras uses SIRIUS

2. **Para detener el servidor:**
   - Presiona `Ctrl+C` en la ventana donde está corriendo
   - O simplemente cierra la ventana

3. **Para reiniciar el servidor:**
   - Detén el servidor actual (Ctrl+C)
   - Vuelve a ejecutar: `python -m uvicorn main:app --reload`

---

## 🎬 Resumen Rápido

```powershell
# 1. Abre PowerShell
# 2. Ejecuta estos comandos:

cd "C:\Users\JEVD4139\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4\backend"
python -m uvicorn main:app --reload

# 3. Espera a ver "Application startup complete"
# 4. Abre http://localhost:8000 en tu navegador
```

---

## 🆘 ¿Aún no funciona?

Ejecuta el diagnóstico:

```powershell
cd "C:\Users\JEVD4139\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4"
DIAGNOSTICO_SIRIUS.bat
```

Este script te dirá exactamente qué está fallando.

---

*Última actualización: 29 de noviembre de 2025*

