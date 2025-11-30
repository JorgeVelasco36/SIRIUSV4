# Arquitectura del Sistema - S.I.R.I.U.S V4

## Visión General

S.I.R.I.U.S V4 es un sistema de asistente conversacional especializado en renta fija colombiana, diseñado con una arquitectura de microservicios que separa claramente el backend (API) del frontend (interfaz de usuario).

## Componentes Principales

### 1. Backend (FastAPI)

**Ubicación:** `backend/`

**Responsabilidades:**
- Procesamiento de consultas en lenguaje natural
- Ingesta y normalización de datos
- Consultas estructuradas a la base de datos
- Integración con SharePoint (Microsoft Graph API)
- Generación de respuestas con LLM

**Estructura:**
```
backend/
├── main.py                 # Punto de entrada, endpoints FastAPI
├── config.py               # Configuración y variables de entorno
├── database.py             # Conexión y sesión de base de datos
├── models.py               # Modelos SQLAlchemy
├── schemas.py              # Schemas Pydantic para validación
├── services/               # Lógica de negocio
│   ├── chat_service.py     # Procesamiento de lenguaje natural
│   ├── query_service.py    # Consultas estructuradas
│   ├── ingestion_service.py # Ingesta y normalización
│   └── sharepoint_service.py # Integración SharePoint
└── alembic/               # Migraciones de base de datos
```

### 2. Frontend (React + TypeScript)

**Ubicación:** `frontend/`

**Responsabilidades:**
- Interfaz de usuario de chat
- Visualización de datos (tablas)
- Filtros rápidos
- Comunicación con API backend

**Estructura:**
```
frontend/
├── src/
│   ├── components/        # Componentes React
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageInput.tsx
│   │   ├── FiltersPanel.tsx
│   │   └── ValuationTable.tsx
│   ├── services/
│   │   └── api.ts          # Cliente API
│   └── App.tsx             # Componente principal
```

### 3. Base de Datos (PostgreSQL)

**Tablas Principales:**

1. **valuations**
   - Almacena todas las valoraciones
   - Índices en: ISIN, fecha, proveedor
   - Campos: precios, tasas, duración, convexidad, etc.

2. **files_metadata**
   - Metadatos de archivos procesados
   - Trazabilidad de ingesta
   - Estado de procesamiento

3. **query_logs**
   - Historial de consultas
   - Auditoría y análisis

### 4. Scripts de Utilidad

**Ubicación:** `scripts/`

- `ingest_file.py`: Ingesta manual desde archivo local
- `ingest_sharepoint.py`: Ingesta automática desde SharePoint
- `test_query.py`: Pruebas de consultas
- `init_db.py`: Inicialización de base de datos

## Flujo de Datos

### Ingesta de Datos

```
Archivo (CSV/Excel) o SharePoint
    ↓
IngestionService
    ↓
Normalización de columnas
    ↓
Validación y limpieza
    ↓
Base de Datos (PostgreSQL)
```

### Procesamiento de Consultas

```
Usuario (Frontend)
    ↓
POST /api/v1/chat
    ↓
ChatService
    ↓
Extract Intent (LLM)
    ↓
QueryService
    ↓
Base de Datos
    ↓
Generar Respuesta (LLM)
    ↓
Formatear y Agregar Recomendaciones
    ↓
Respuesta al Usuario
```

## Integraciones Externas

### 1. Microsoft Graph API (SharePoint)

**Propósito:** Obtener archivos de valoración diarios

**Autenticación:** OAuth 2.0 Client Credentials Flow

**Endpoints utilizados:**
- `GET /sites/{site-id}/drive/root/children` - Listar archivos
- `GET /sites/{site-id}/drive/items/{item-id}/content` - Descargar archivo

### 2. OpenAI API

**Propósito:** Procesamiento de lenguaje natural

**Modelo:** GPT-4 (configurable)

**Uso:**
- Extracción de intención de consultas
- Generación de respuestas naturales

## Patrones de Diseño

### 1. Service Layer Pattern

Cada servicio encapsula lógica de negocio específica:
- `ChatService`: Lógica de chat y NLP
- `QueryService`: Consultas a base de datos
- `IngestionService`: Procesamiento de archivos
- `SharePointService`: Integración externa

### 2. Repository Pattern (implícito)

Los servicios actúan como repositorios, abstraen el acceso a datos.

### 3. Dependency Injection

FastAPI usa dependency injection para sesiones de base de datos.

## Seguridad

### Autenticación

- Microsoft Graph API: OAuth 2.0 Client Credentials
- OpenAI API: API Key

### Validación

- Pydantic schemas para validación de entrada
- SQLAlchemy para validación de datos en BD

### CORS

Configurado para permitir solo orígenes específicos.

## Escalabilidad

### Base de Datos

- Índices en columnas frecuentemente consultadas
- Particionamiento potencial por fecha (futuro)

### API

- FastAPI es asíncrono y escalable
- Pool de conexiones configurado

### Frontend

- React optimizado con lazy loading potencial
- Componentes modulares

## Monitoreo y Logging

- Logging estructurado en backend
- Query logs en base de datos
- Errores capturados y registrados

## Extensibilidad

### Agregar Nuevo Proveedor

1. Agregar enum en `models.py`
2. Agregar mapeo de columnas en `IngestionService`
3. Actualizar lógica de comparación

### Agregar Nuevos Campos

1. Agregar columna en modelo `Valuation`
2. Crear migración Alembic
3. Actualizar mapeo de columnas
4. Actualizar schemas Pydantic

### Agregar Nuevas Funcionalidades de Chat

1. Extender `extract_intent` en `ChatService`
2. Agregar nueva lógica en `generate_response`
3. Actualizar frontend si es necesario

## Consideraciones de Rendimiento

1. **Caché:** Potencial implementación de Redis para consultas frecuentes
2. **Paginación:** Implementada en endpoints de consulta
3. **Índices:** Optimizados para consultas comunes
4. **Lazy Loading:** En frontend para grandes datasets

## Próximas Mejoras

1. Autenticación de usuarios
2. Caché de respuestas frecuentes
3. Webhooks para ingesta automática
4. Dashboard de analytics
5. Exportación de reportes
6. Notificaciones de alertas








