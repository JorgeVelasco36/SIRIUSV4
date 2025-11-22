# S.I.R.I.U.S V4 - Asistente Conversacional de Renta Fija Colombiana

Sistema Inteligente de Renta Fija e Inversión Unificada (S.I.R.I.U.S) V4 es un asistente conversacional especializado en renta fija colombiana, diseñado para traders y directores de mesa de inversiones.

## 🎯 Características Principales

- **Ingesta Automática**: Lectura y procesamiento de archivos diarios de valoración (PIP Latam, Precia) desde MongoDB Atlas
- **Consultas en Lenguaje Natural**: Interfaz conversacional para consultas técnicas
- **Comparación de Proveedores**: Análisis comparativo entre PIP Latam y Precia
- **Filtrado Avanzado**: Búsqueda por fecha, rango de fechas, ISIN, emisor, tipo de instrumento
- **Explicaciones Técnicas**: Respuestas claras sobre valores clave (tasa, duración, precio limpio/sucio)
- **Detección de Inconsistencias**: Alertas automáticas sobre datos faltantes o inconsistentes
- **Recomendaciones Accionables**: Cada respuesta incluye 3 recomendaciones orientadas a decisiones

## 🏗️ Arquitectura

```
SIRIUS-V4/
├── backend/          # API FastAPI
├── frontend/         # SPA React + TypeScript
├── scripts/          # Scripts de utilidad
└── docs/            # Documentación adicional
```

## 🚀 Inicio Rápido

### 📚 Guías de Configuración

- **[Guía Simple para No Expertos](docs/GUIA_SIMPLE.md)** 📘 - Guía paso a paso detallada, sin jerga técnica
- **[Guía Rápida (5 minutos)](docs/GUIA_RAPIDA.md)** ⚡ - Configuración rápida para usuarios experimentados
- **[Guía Técnica Completa](docs/SETUP.md)** 🔧 - Para desarrolladores y usuarios técnicos
- **[Configuración de MongoDB Atlas](docs/MONGODB_SETUP.md)** 🍃 - Almacenar y leer archivos desde MongoDB Atlas

### Requisitos Previos

**Mínimos (Solución Simplificada):**
- Python 3.10+ ✅

**Completos (Producción):**
- Python 3.10+
- Node.js 18+ (opcional - ver alternativas)
- PostgreSQL 14+ (opcional - SQLite incluido por defecto)
- Cuenta de MongoDB Atlas (para almacenar archivos de valoración)

> 💡 **¿No puedes instalar Node.js o PostgreSQL?** Ver [docs/ALTERNATIVES.md](docs/ALTERNATIVES.md) para la versión simplificada que solo requiere Python.
> 
> 💡 **¿No eres experto en tecnología?** Empieza con la [Guía Simple](docs/GUIA_SIMPLE.md) - está diseñada para personas sin experiencia técnica.

### Instalación

1. **Clonar y configurar variables de entorno:**

```bash
# Backend
cd backend
cp .env.example .env
# Editar .env con tus credenciales

# Frontend
cd frontend
cp .env.example .env
```

2. **Configurar Base de Datos:**

```bash
# Crear base de datos PostgreSQL
createdb sirius_v4

# Ejecutar migraciones
cd backend
alembic upgrade head
```

3. **Instalar dependencias:**

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

4. **Ejecutar servicios:**

```bash
# Backend (puerto 8000)
cd backend
uvicorn main:app --reload

# Frontend (puerto 3000)
cd frontend
npm start
```

## 📋 Variables de Entorno

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sirius_v4

# MongoDB Atlas
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=sirius_v4
MONGODB_COLLECTION=valuation_files

# LLM (OpenAI o compatible)
OPENAI_API_KEY=your_api_key
LLM_MODEL=gpt-4

# App
SECRET_KEY=your_secret_key
ENVIRONMENT=development
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
```

## 🔧 Uso

### Ingesta de Datos

**Desde MongoDB Atlas:**
```bash
# Subir archivo a MongoDB
python scripts/upload_to_mongodb.py --file archivo.xlsx --provider PIP_LATAM --fecha 2025-01-15

# Ingerir desde MongoDB
python scripts/ingest_mongodb.py --provider PIP_LATAM
```

**Manual (archivo local):**
```bash
cd backend
python scripts/ingest_file.py --file path/to/valuations.xlsx --provider PIP_LATAM
```

### Consultas de Ejemplo

1. **Precio de un instrumento:**
   - "¿Cuál es el precio limpio del TES CO000123 hoy en Precia?"

2. **Comparación de proveedores:**
   - "Compara PIP Latam vs Precia para este ISIN."

3. **Múltiples ISINs:**
   - "Trae valoración de ayer para estos 5 ISINs."

4. **Análisis técnico:**
   - "Explica brevemente la diferencia entre los dos proveedores."

## 📊 Estructura de Base de Datos

### Tabla: valuations
- ISIN, Emisor, Tipo de instrumento, Plazo
- Precio limpio, Precio sucio, Tasa, Duración, Convexidad
- Fecha, Proveedor, Archivo origen, Timestamp de ingesta

### Tabla: files_metadata
- Nombre archivo, Proveedor, Fecha valoración, Estado procesamiento

### Tabla: query_logs
- Consulta, Respuesta, Usuario, Timestamp

## 🛠️ Desarrollo

### Ejecutar Tests
```bash
cd backend
pytest
```

### Linting
```bash
cd backend
black .
flake8 .

cd frontend
npm run lint
```

## 📝 Licencia

Propietario - Uso interno

## 👥 Contacto

Para soporte técnico o consultas, contactar al equipo de desarrollo.

