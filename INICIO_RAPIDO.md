# 🚀 Inicio Rápido - SIRIUS V4

## ✅ Estado Actual

- ✅ Base de datos: 3,248 valoraciones cargadas
- ✅ Configuración: Todas las variables de entorno configuradas
- ✅ Pruebas: Todas las pruebas pasaron exitosamente

---

## 🎯 Activar SIRIUS

### Opción 1: Usar el script de activación (Recomendado)

Simplemente haz doble clic en:
```
ACTIVAR_SIRIUS.bat
```

### Opción 2: Iniciar manualmente

1. Abre PowerShell o Terminal
2. Navega al proyecto:
   ```powershell
   cd "C:\Users\JEVD4139\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4"
   ```
3. Inicia el servidor:
   ```powershell
   cd backend
   python -m uvicorn main:app --reload
   ```

---

## 🌐 Acceder a SIRIUS

Una vez iniciado el servidor, abre tu navegador en:

- **Interfaz Principal:** http://localhost:8000
- **Documentación API:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 💬 Usar SIRIUS

1. Abre la interfaz web en http://localhost:8000
2. Escribe tu pregunta en el chat
3. SIRIUS responderá con información sobre renta fija colombiana

### Ejemplos de preguntas:

- "¿Cuál es el precio limpio del TES CO000123 hoy en Precia?"
- "Compara PIP Latam vs Precia para el ISIN COB06CD3V967"
- "¿Qué es la TIR?"
- "Trae valoración de ayer para estos ISINs: COB06CD3V967, PAT03CB00035"

---

## 🔧 Verificar que SIRIUS está funcionando

Abre una nueva terminal y ejecuta:

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

Si responde con `{"status":"healthy"}`, ¡SIRIUS está funcionando!

---

## ⚠️ Si el servidor no inicia

1. Verifica que Python esté instalado:
   ```powershell
   python --version
   ```

2. Verifica la configuración:
   ```powershell
   python scripts/verify_env.py
   ```

3. Verifica que el puerto 8000 no esté en uso:
   ```powershell
   netstat -ano | findstr :8000
   ```

---

## 📊 Estadísticas

- **Valoraciones en BD:** 3,248
- **Proveedores:** PIP Latam, Precia
- **Chunks de conocimiento:** 122
- **Archivos en Supabase:** 2 (1,000 registros cada uno)

---

## 🆘 ¿Necesitas ayuda?

Consulta la documentación completa:
- [Guía Simple](docs/GUIA_SIMPLE.md)
- [Resultados de Pruebas](docs/RESULTADOS_PRUEBAS.md)

---

*Última actualización: 29 de noviembre de 2025*

