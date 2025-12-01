# ⚡ Guía Rápida - Configuración en 5 Minutos

## 🎯 Para usuarios que quieren empezar rápido

---

## ✅ PASO 1: Crear archivo de configuración (2 minutos)

1. Ve a la carpeta: `backend`
2. Copia el archivo `.env.example` y renómbralo a `.env`
3. Ábrelo con el Bloc de notas

---

## 🔑 PASO 2: Configurar credenciales (2 minutos)

Edita estas líneas en el archivo `.env`:

```env
# OpenAI (OBLIGATORIO)
OPENAI_API_KEY=tu-clave-de-openai-aqui

# Microsoft Azure (OPCIONAL - puedes dejarlo vacío)
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
SHAREPOINT_SITE_ID=

# Clave secreta (cualquier texto aleatorio)
SECRET_KEY=mi-clave-secreta-12345
```

**💡 Importante:** 
- La clave de OpenAI es **obligatoria**
- Las de Azure son **opcionales** (solo si quieres leer SharePoint automáticamente)

---

## 💾 PASO 3: Crear base de datos (30 segundos)

Abre PowerShell y ejecuta:

```powershell
cd "ruta\a\tu\proyecto\SIRIUS\V4"
python scripts/init_db.py
```

---

## 🚀 PASO 4: Iniciar el asistente (30 segundos)

```powershell
cd backend
python -m uvicorn main:app --reload
```

---

## 🌐 PASO 5: Abrir en el navegador

Abre: **http://localhost:8000**

---

## ✅ ¡Listo!

Ya puedes usar el asistente. 

**Para cargar datos:**
```powershell
python scripts/ingest_file.py --file "archivo.xlsx" --provider PIP_LATAM
```

---

## 🆘 ¿Problemas?

Ver la [Guía Completa](GUIA_SIMPLE.md) para más detalles.









