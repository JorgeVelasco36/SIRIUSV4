# 🍃 Configuración de MongoDB Atlas - S.I.R.I.U.S V4

## 📍 ¿Qué es MongoDB Atlas?

MongoDB Atlas es un servicio en la nube que almacena los archivos de valoración. Reemplaza a SharePoint como fuente de datos.

**Ventajas:**
- ✅ No requiere autenticación compleja
- ✅ Acceso directo con connection string
- ✅ Almacenamiento escalable
- ✅ Fácil de configurar

---

## 🔧 Configuración Paso a Paso

### PASO 1: Crear cuenta en MongoDB Atlas

1. **Ve a:** https://www.mongodb.com/cloud/atlas/register
2. **Crea una cuenta** gratuita (M0 - Free tier disponible)
3. **Inicia sesión** en tu cuenta

---

### PASO 2: Crear un Cluster

1. **En el dashboard**, haz clic en "Build a Database"
2. **Selecciona:** "M0 FREE" (gratis para empezar)
3. **Elige una región** cercana (ej: N. Virginia, Oregon)
4. **Nombre del cluster:** `sirius-v4` (o el que prefieras)
5. **Haz clic en "Create"**

**⏱️ Tiempo estimado:** 3-5 minutos para crear el cluster

---

### PASO 3: Configurar Usuario de Base de Datos

1. **En "Database Access"** (menú lateral izquierdo)
2. **Haz clic en "Add New Database User"**
3. **Método de autenticación:** Password
4. **Usuario:** `sirius_user` (o el que prefieras)
5. **Contraseña:** Genera una contraseña segura (guárdala bien)
6. **Database User Privileges:** "Read and write to any database"
7. **Haz clic en "Add User"**

**⚠️ IMPORTANTE:** Guarda el usuario y contraseña, los necesitarás para el connection string.

---

### PASO 4: Configurar Acceso de Red

1. **En "Network Access"** (menú lateral izquierdo)
2. **Haz clic en "Add IP Address"**
3. **Opción 1 (Desarrollo):** Haz clic en "Allow Access from Anywhere"
   - Esto permite acceso desde cualquier IP (solo para desarrollo)
4. **Opción 2 (Producción):** Agrega tu IP específica
5. **Haz clic en "Confirm"**

---

### PASO 5: Obtener Connection String

1. **En "Database"** (menú lateral izquierdo)
2. **Haz clic en "Connect"** en tu cluster
3. **Selecciona:** "Connect your application"
4. **Driver:** Python
5. **Version:** 4.6 or later
6. **Copia el connection string** que aparece

**Ejemplo:**
```
mongodb+srv://sirius_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

7. **Reemplaza `<password>`** con la contraseña que creaste en el Paso 3

**Ejemplo final:**
```
mongodb+srv://sirius_user:MiPassword123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

---

### PASO 6: Configurar el archivo .env

Edita el archivo `.env` en la carpeta `backend`:

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://sirius_user:MiPassword123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=sirius_v4
MONGODB_COLLECTION=valuation_files
```

**⚠️ IMPORTANTE:** 
- Reemplaza el connection string con el tuyo
- Reemplaza la contraseña con la real
- No compartas este archivo (está en .gitignore)

---

## 📤 Subir Archivos a MongoDB

### Opción 1: Subir un archivo específico

```powershell
python scripts/upload_to_mongodb.py --file "ruta/al/archivo.xlsx" --provider PIP_LATAM --fecha 2025-01-15
```

**Parámetros:**
- `--file`: Ruta al archivo (Excel o CSV)
- `--provider`: `PIP_LATAM` o `PRECIA`
- `--fecha`: Fecha de valoración (YYYY-MM-DD), opcional (usa hoy si no se especifica)

**Ejemplo:**
```powershell
python scripts/upload_to_mongodb.py --file "C:\Documentos\valoraciones_precia_2025-01-15.xlsx" --provider PRECIA --fecha 2025-01-15
```

---

### Opción 2: Subir múltiples archivos

Puedes crear un script simple para subir varios archivos:

```powershell
# Subir archivo de Precia
python scripts/upload_to_mongodb.py --file "precia_2025-01-15.xlsx" --provider PRECIA --fecha 2025-01-15

# Subir archivo de PIP Latam
python scripts/upload_to_mongodb.py --file "pip_latam_2025-01-15.xlsx" --provider PIP_LATAM --fecha 2025-01-15
```

---

## 📥 Ingerir Archivos desde MongoDB

### Opción 1: Ingerir archivo específico

```powershell
python scripts/ingest_mongodb.py --provider PIP_LATAM --file-id "ID_DEL_ARCHIVO"
```

### Opción 2: Ingerir archivo más reciente

```powershell
python scripts/ingest_mongodb.py --provider PIP_LATAM
```

Esto ingiere el archivo más reciente del proveedor especificado.

### Opción 3: Ingerir archivo de fecha específica

```powershell
python scripts/ingest_mongodb.py --provider PRECIA --fecha 2025-01-15
```

### Opción 4: Listar archivos sin ingerir (dry-run)

```powershell
python scripts/ingest_mongodb.py --provider PIP_LATAM --dry-run
```

---

## 🔍 Explorar Archivos en MongoDB

Puedes ver los archivos disponibles directamente en MongoDB Atlas:

1. **Ve a:** https://cloud.mongodb.com
2. **Inicia sesión**
3. **Selecciona tu cluster**
4. **Haz clic en "Browse Collections"**
5. **Busca la colección:** `fs.files` (GridFS almacena archivos aquí)
6. **Verás todos los archivos** con sus metadatos

---

## 📊 Estructura de Datos en MongoDB

Los archivos se almacenan usando **GridFS**, que es el sistema de MongoDB para archivos grandes.

**Colecciones creadas automáticamente:**
- `fs.files` - Metadatos de los archivos
- `fs.chunks` - Chunks (pedazos) de los archivos

**Metadatos almacenados:**
- `filename`: Nombre del archivo
- `metadata.provider`: Proveedor (PIP_LATAM, PRECIA)
- `metadata.fecha_valoracion`: Fecha de valoración (YYYY-MM-DD)
- `upload_date`: Fecha de subida
- `length`: Tamaño del archivo

---

## ❌ Solución de Problemas

### Error: "ServerSelectionTimeoutError"

**Causa:** No puedes conectarte a MongoDB Atlas

**Solución:**
1. Verifica que tu IP esté en la lista de "Network Access"
2. Verifica que el connection string sea correcto
3. Verifica que el usuario y contraseña sean correctos
4. Verifica tu conexión a internet

---

### Error: "Authentication failed"

**Causa:** Usuario o contraseña incorrectos

**Solución:**
1. Verifica el connection string en `.env`
2. Asegúrate de haber reemplazado `<password>` con la contraseña real
3. Verifica que el usuario exista en "Database Access"

---

### Error: "No se encontraron archivos"

**Causa:** No hay archivos en MongoDB o el filtro es muy restrictivo

**Solución:**
1. Verifica que hayas subido archivos primero
2. Usa `--dry-run` para ver qué archivos están disponibles
3. Verifica que el proveedor sea correcto (PIP_LATAM o PRECIA)

---

### Error: "Connection string malformado"

**Causa:** El connection string tiene caracteres especiales sin codificar

**Solución:**
- Si tu contraseña tiene caracteres especiales, codifícalos:
  - `@` → `%40`
  - `#` → `%23`
  - `$` → `%24`
  - `%` → `%25`
  - `&` → `%26`
  - `+` → `%2B`
  - `=` → `%3D`

**Ejemplo:**
```
# Contraseña original: P@ssw0rd#123
# Connection string: mongodb+srv://user:P%40ssw0rd%23123@cluster...
```

---

## 🔐 Seguridad

### Buenas Prácticas

1. **No compartas el connection string** - Contiene credenciales
2. **Usa IP whitelist en producción** - No "Allow from anywhere"
3. **Rota contraseñas regularmente** - Cambia la contraseña del usuario periódicamente
4. **Usa usuarios con permisos mínimos** - Solo "Read and write" necesario
5. **Haz backup regularmente** - MongoDB Atlas tiene opciones de backup

---

## 💰 Costos

### Tier Gratuito (M0)

- ✅ 512 MB de almacenamiento
- ✅ Compartido (puede ser lento en horas pico)
- ✅ Ideal para desarrollo y pruebas

### Tier de Pago (M10+)

- 💰 Desde $9/mes
- ✅ Más almacenamiento
- ✅ Mejor rendimiento
- ✅ Backup automático

**Para producción con muchos archivos, considera un tier de pago.**

---

## 📝 Flujo de Trabajo Recomendado

1. **Subir archivos diarios:**
   ```powershell
   python scripts/upload_to_mongodb.py --file "archivo.xlsx" --provider PIP_LATAM --fecha 2025-01-15
   ```

2. **Ingerir archivos automáticamente:**
   ```powershell
   python scripts/ingest_mongodb.py --provider PIP_LATAM
   ```

3. **Verificar en la base de datos:**
   - Usa el asistente para consultar los datos
   - O ejecuta: `python scripts/test_query.py`

---

## 🎯 Próximos Pasos

Después de configurar MongoDB Atlas:

1. ✅ Sube algunos archivos de prueba
2. ✅ Verifica que se puedan ingerir correctamente
3. ✅ Configura un proceso automatizado (cron job o scheduler)
4. ✅ Monitorea el uso de almacenamiento en MongoDB Atlas

---

## 📚 Recursos Adicionales

- **Documentación MongoDB Atlas:** https://docs.atlas.mongodb.com
- **GridFS Documentation:** https://docs.mongodb.com/manual/core/gridfs/
- **Connection String Guide:** https://docs.atlas.mongodb.com/connect-to-cluster/

---

*Última actualización: Noviembre 2025*








