# Alternativas Sin Instalación Adicional - S.I.R.I.U.S V4

## 🎯 Solución Implementada

Si no puedes instalar **Node.js** ni **PostgreSQL**, hemos adaptado el proyecto para funcionar completamente solo con **Python 3.10+**.

## ✅ Cambios Realizados

### 1. Base de Datos: SQLite (en lugar de PostgreSQL)

**Ventajas:**
- ✅ Viene incluido con Python (no requiere instalación)
- ✅ Base de datos en archivo local (`sirius_v4.db`)
- ✅ Mismo rendimiento para uso individual/pequeño equipo
- ✅ Compatible con SQLAlchemy (mismo código)

**Configuración:**
- Por defecto usa SQLite: `sqlite:///./sirius_v4.db`
- Si tienes PostgreSQL, puedes cambiarlo en `.env`: `DATABASE_URL=postgresql://...`

### 2. Frontend: HTML/CSS/JS (en lugar de React)

**Ventajas:**
- ✅ No requiere Node.js
- ✅ Servido directamente desde FastAPI
- ✅ Misma funcionalidad: chat, filtros, tablas
- ✅ Interfaz moderna y responsive

**Ubicación:**
- Templates: `backend/templates/base.html`
- CSS: `backend/static/css/style.css`
- JavaScript: `backend/static/js/app.js`

## 🚀 Instalación Simplificada

### Requisitos ÚNICOS

1. **Python 3.10+** ✅ (ya lo tienes instalado)

### Pasos de Instalación

```bash
# 1. Ir al directorio del proyecto
cd backend

# 2. Instalar dependencias (solo Python)
pip install -r requirements.txt

# 3. Configurar variables de entorno
# Copiar .env.example a .env y editar
# NOTA: DATABASE_URL ya está configurado para SQLite por defecto

# 4. Inicializar base de datos (crea el archivo SQLite automáticamente)
python ../scripts/init_db.py

# 5. Ejecutar la aplicación
uvicorn main:app --reload
```

### Acceder a la Aplicación

Abre tu navegador en: **http://localhost:8000**

¡Eso es todo! No necesitas instalar nada más.

## 📊 Comparación

| Característica | Versión Original | Versión Alternativa |
|---------------|------------------|---------------------|
| **Base de Datos** | PostgreSQL 14+ | SQLite (incluido) |
| **Frontend** | React + Node.js 18+ | HTML/CSS/JS (servido por FastAPI) |
| **Instalaciones Requeridas** | 3 (Python, Node, PostgreSQL) | 1 (solo Python) |
| **Funcionalidad** | Completa | Completa |
| **Rendimiento** | Excelente (producción) | Excelente (desarrollo/pequeño equipo) |

## 🔄 Migración Futura

Si más adelante puedes instalar PostgreSQL y Node.js:

1. **Para PostgreSQL:**
   - Cambiar `DATABASE_URL` en `.env` a PostgreSQL
   - Instalar `psycopg2-binary`: `pip install psycopg2-binary`
   - Ejecutar migraciones: `alembic upgrade head`

2. **Para React Frontend:**
   - El código React original está en `frontend/`
   - Solo necesitas instalar Node.js y ejecutar `npm install && npm start`

## ⚠️ Limitaciones de SQLite

SQLite es perfecto para:
- ✅ Desarrollo
- ✅ Uso individual
- ✅ Pequeños equipos (< 10 usuarios concurrentes)
- ✅ Datos < 100GB

Para producción con muchos usuarios, considera PostgreSQL.

## 🛠️ Estructura del Frontend Alternativo

```
backend/
├── templates/
│   └── base.html          # Template principal HTML
├── static/
│   ├── css/
│   │   └── style.css     # Estilos
│   └── js/
│       └── app.js         # Lógica JavaScript
└── main.py                # Sirve el frontend en /
```

## 📝 Notas Importantes

1. **Base de datos SQLite:**
   - Se crea automáticamente en `backend/sirius_v4.db`
   - No requiere configuración adicional
   - Puedes hacer backup copiando el archivo `.db`

2. **Frontend integrado:**
   - Accede directamente a `http://localhost:8000`
   - No necesitas ejecutar servidor separado
   - API disponible en `http://localhost:8000/api/v1/`

3. **Misma funcionalidad:**
   - Todas las características funcionan igual
   - Chat, filtros, comparaciones, alertas
   - Ingesta de archivos

## 🎉 Ventajas de Esta Solución

1. **Simplicidad:** Solo Python necesario
2. **Portabilidad:** Todo en un solo proyecto
3. **Rapidez:** Sin compilación de frontend
4. **Mantenimiento:** Menos dependencias
5. **Funcionalidad:** 100% de las características

## 🔍 Verificación

Para verificar que todo funciona:

```bash
# 1. Verificar Python
python --version  # Debe ser 3.10+

# 2. Verificar dependencias
python -c "import fastapi, sqlalchemy, jinja2; print('OK')"

# 3. Ejecutar aplicación
cd backend
uvicorn main:app --reload

# 4. Abrir navegador
# http://localhost:8000
```

## 📚 Documentación Adicional

- `docs/SETUP.md` - Guía de configuración completa
- `docs/USAGE.md` - Guía de uso
- `README.md` - Documentación principal

