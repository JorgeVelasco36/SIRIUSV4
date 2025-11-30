# Estructura del Proyecto S.I.R.I.U.S V4

```
SIRIUS-V4/
│
├── backend/                    # Backend FastAPI
│   ├── __init__.py
│   ├── main.py                # Punto de entrada, endpoints
│   ├── config.py              # Configuración
│   ├── database.py            # Conexión BD
│   ├── models.py              # Modelos SQLAlchemy
│   ├── schemas.py             # Schemas Pydantic
│   ├── requirements.txt       # Dependencias Python
│   ├── alembic.ini            # Config Alembic
│   ├── .env.example           # Ejemplo de variables de entorno
│   │
│   ├── services/              # Servicios de negocio
│   │   ├── __init__.py
│   │   ├── chat_service.py    # Procesamiento NLP
│   │   ├── query_service.py   # Consultas estructuradas
│   │   ├── ingestion_service.py # Ingesta y normalización
│   │   └── sharepoint_service.py # Integración SharePoint
│   │
│   └── alembic/              # Migraciones de BD
│       ├── env.py
│       ├── script.py.mako
│       └── versions/          # Migraciones (generadas)
│
├── frontend/                   # Frontend React
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── index.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── App.css
│   │   │
│   │   ├── components/        # Componentes React
│   │   │   ├── Header.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── Message.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── FiltersPanel.tsx
│   │   │   └── ValuationTable.tsx
│   │   │
│   │   └── services/
│   │       └── api.ts          # Cliente API
│   │
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example
│
├── scripts/                    # Scripts de utilidad
│   ├── ingest_file.py         # Ingesta manual
│   ├── ingest_sharepoint.py   # Ingesta desde SharePoint
│   ├── test_query.py          # Pruebas de consultas
│   └── init_db.py             # Inicialización BD
│
├── docs/                       # Documentación
│   ├── SETUP.md               # Guía de configuración
│   ├── USAGE.md               # Guía de uso
│   └── ARCHITECTURE.md        # Arquitectura del sistema
│
├── README.md                   # Documentación principal
├── .gitignore                 # Archivos ignorados por Git
└── PROJECT_STRUCTURE.md       # Este archivo
```

## Descripción de Directorios

### backend/
Contiene toda la lógica del servidor:
- **main.py**: Define todos los endpoints de la API
- **models.py**: Define las tablas de la base de datos
- **services/**: Contiene la lógica de negocio separada por responsabilidad

### frontend/
Aplicación React con TypeScript:
- **components/**: Componentes reutilizables de la UI
- **services/**: Cliente para comunicarse con el backend

### scripts/
Scripts Python para tareas comunes:
- Ingesta de datos
- Pruebas
- Utilidades

### docs/
Documentación completa del proyecto:
- Configuración
- Uso
- Arquitectura

## Archivos Importantes

### Configuración
- `backend/.env`: Variables de entorno del backend (no versionado)
- `frontend/.env`: Variables de entorno del frontend (no versionado)
- `backend/config.py`: Carga y valida configuración

### Base de Datos
- `backend/models.py`: Define el esquema de la BD
- `backend/alembic/`: Migraciones de base de datos

### Dependencias
- `backend/requirements.txt`: Dependencias Python
- `frontend/package.json`: Dependencias Node.js

## Flujo de Trabajo Típico

1. **Configuración inicial**: Seguir `docs/SETUP.md`
2. **Ingesta de datos**: Usar scripts en `scripts/`
3. **Desarrollo**: Modificar código en `backend/` o `frontend/`
4. **Pruebas**: Usar `scripts/test_query.py`
5. **Despliegue**: Seguir guías de despliegue

## Convenciones

- **Python**: PEP 8, type hints donde sea posible
- **TypeScript**: Strict mode, interfaces para tipos
- **Commits**: Mensajes descriptivos
- **Documentación**: Docstrings en funciones importantes








