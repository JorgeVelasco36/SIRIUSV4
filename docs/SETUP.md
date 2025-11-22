# Guía de Configuración - S.I.R.I.U.S V4

## Requisitos Previos

### Software Necesario

1. **Python 3.10+**
   ```bash
   python --version
   ```

2. **Node.js 18+**
   ```bash
   node --version
   ```

3. **PostgreSQL 14+**
   ```bash
   psql --version
   ```

4. **Git** (opcional, para control de versiones)

### Cuentas y Credenciales

1. **Microsoft Azure** - Para acceso a SharePoint vía Graph API
2. **OpenAI API Key** - Para procesamiento de lenguaje natural

## Configuración Paso a Paso

### 1. Clonar/Preparar el Proyecto

```bash
cd SIRIUS-V4
```

### 2. Configurar Base de Datos PostgreSQL

```bash
# Crear base de datos
createdb sirius_v4

# O usando psql
psql -U postgres
CREATE DATABASE sirius_v4;
\q
```

### 3. Configurar Backend

```bash
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de configuración
cp .env.example .env

# Editar .env con tus credenciales
# (Ver sección de Variables de Entorno)
```

### 4. Inicializar Base de Datos

```bash
# Opción 1: Usar script
python ../scripts/init_db.py

# Opción 2: Usar Alembic (recomendado para producción)
alembic upgrade head
```

### 5. Configurar Frontend

```bash
cd ../frontend

# Instalar dependencias
npm install

# Copiar archivo de configuración
cp .env.example .env

# Editar .env con la URL del backend
# REACT_APP_API_URL=http://localhost:8000
```

### 6. Configurar Variables de Entorno

#### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://usuario:password@localhost:5432/sirius_v4

# Microsoft Graph API
AZURE_CLIENT_ID=tu_client_id
AZURE_CLIENT_SECRET=tu_client_secret
AZURE_TENANT_ID=tu_tenant_id
SHAREPOINT_SITE_ID=tu_site_id
SHAREPOINT_DRIVE_ID=tu_drive_id  # Opcional

# LLM
OPENAI_API_KEY=tu_api_key
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.3

# Application
SECRET_KEY=genera-una-clave-secreta-segura
ENVIRONMENT=development
LOG_LEVEL=INFO

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000
```

#### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
```

## Obtención de Credenciales

### Microsoft Graph API (SharePoint)

1. Ir a [Azure Portal](https://portal.azure.com)
2. Azure Active Directory > App registrations
3. Crear nueva aplicación o usar existente
4. Obtener:
   - **Client ID**: Application (client) ID
   - **Tenant ID**: Directory (tenant) ID
   - **Client Secret**: Crear en "Certificates & secrets"
5. Configurar permisos:
   - `Files.Read.All`
   - `Sites.Read.All`
6. Obtener SharePoint Site ID:
   - Ir a SharePoint site
   - URL: `https://[tenant].sharepoint.com/sites/[site-name]`
   - Site ID está en la URL o se puede obtener vía Graph API

### OpenAI API

1. Ir a [OpenAI Platform](https://platform.openai.com)
2. Crear cuenta o iniciar sesión
3. Ir a API Keys
4. Crear nueva clave API
5. Copiar y guardar (solo se muestra una vez)

## Ejecutar la Aplicación

### Desarrollo

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

La aplicación estará disponible en:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Producción

Ver documentación de despliegue en `docs/DEPLOYMENT.md`

## Verificar Instalación

### 1. Verificar Backend

```bash
cd backend
python -c "from database import engine; print('DB OK')"
```

### 2. Verificar Base de Datos

```bash
psql -U postgres -d sirius_v4 -c "\dt"
```

### 3. Probar Ingesta

```bash
python scripts/ingest_file.py --file ejemplo.xlsx --provider PIP_LATAM
```

### 4. Probar Consultas

```bash
python scripts/test_query.py
```

## Solución de Problemas

### Error de Conexión a Base de Datos

- Verificar que PostgreSQL está corriendo
- Verificar credenciales en `.env`
- Verificar que la base de datos existe

### Error de Autenticación con SharePoint

- Verificar que las credenciales de Azure son correctas
- Verificar que los permisos están configurados
- Verificar que el Site ID es correcto

### Error con OpenAI API

- Verificar que la API key es válida
- Verificar que tienes créditos disponibles
- Verificar que el modelo especificado existe

### Frontend no se conecta al Backend

- Verificar que el backend está corriendo
- Verificar `REACT_APP_API_URL` en `.env` del frontend
- Verificar CORS en configuración del backend

## Próximos Pasos

1. Realizar primera ingesta de datos
2. Probar consultas en el chat
3. Configurar ingesta automática (cron job o scheduler)
4. Revisar documentación de uso en `README.md`



