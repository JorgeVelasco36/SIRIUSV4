# 📘 Guía Simple de Configuración - S.I.R.I.U.S V4

## 👋 Bienvenido

Esta guía está diseñada para personas que **no tienen experiencia en programación**. Te guiaré paso a paso para que puedas usar el asistente S.I.R.I.U.S V4.

---

## 🎯 ¿Qué es S.I.R.I.U.S V4?

S.I.R.I.U.S V4 es un asistente que te ayuda a:
- ✅ Consultar información sobre instrumentos de renta fija colombiana
- ✅ Comparar datos entre diferentes proveedores (PIP Latam y Precia)
- ✅ Hacer preguntas en lenguaje natural (como hablar con un asistente)
- ✅ Ver alertas sobre datos faltantes o inconsistentes

**Piensa en él como un asistente virtual especializado en renta fija.**

---

## ✅ Lo que YA está listo

1. ✅ **Python está instalado** - El lenguaje de programación necesario
2. ✅ **Las herramientas están instaladas** - Todo el software necesario
3. ✅ **El código está listo** - La aplicación está preparada

---

## 🔧 Lo que NECESITAS configurar

Solo necesitas configurar **3 cosas** para que el asistente funcione:

### 1️⃣ Base de Datos (Archivo donde se guardan los datos)
### 2️⃣ MongoDB Atlas (Para almacenar archivos de valoración)
### 3️⃣ Credenciales de OpenAI (Para que el asistente entienda tus preguntas)

---

## 📝 PASO 1: Crear el archivo de configuración

### ¿Qué es esto?
Es un archivo de texto que contiene las "llaves" para que el asistente acceda a los servicios que necesita.

### Cómo hacerlo:

**Opción A: Si encuentras el archivo `.env.example`**

1. **Abre el Explorador de Archivos de Windows**
   - Presiona `Windows + E` o haz clic en el ícono de carpeta en la barra de tareas

2. **Navega a la carpeta del proyecto:**
   ```
   C:\Users\TU_USUARIO\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4\backend
   ```
   *(Reemplaza TU_USUARIO con tu nombre de usuario de Windows)*

3. **Busca un archivo llamado `.env.example`**
   - Si no lo ves, puede estar oculto. En la barra superior, ve a "Ver" → marca "Elementos ocultos"

4. **Copia el archivo:**
   - Haz clic derecho en `.env.example`
   - Selecciona "Copiar"
   - Haz clic derecho en un espacio vacío
   - Selecciona "Pegar"
   - Renombra el archivo copiado a `.env` (sin el `.example`)

5. **Abre el archivo `.env` con el Bloc de notas:**
   - Haz clic derecho en `.env`
   - Selecciona "Abrir con" → "Bloc de notas"

---

**Opción B: Si NO encuentras el archivo `.env.example` (Crear desde cero)**

1. **Abre el Explorador de Archivos de Windows**
   - Presiona `Windows + E`

2. **Navega a la carpeta:**
   ```
   C:\Users\TU_USUARIO\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4\backend
   ```

3. **Crea un nuevo archivo de texto:**
   - Haz clic derecho en un espacio vacío de la carpeta
   - Selecciona "Nuevo" → "Documento de texto"
   - **IMPORTANTE:** Renombra el archivo a `.env` (con el punto al inicio)
   - Windows te preguntará si estás seguro, haz clic en "Sí"

4. **Abre el archivo `.env` con el Bloc de notas:**
   - Haz clic derecho en `.env`
   - Selecciona "Abrir con" → "Bloc de notas"

5. **Copia y pega este contenido en el archivo:**
   ```
   DATABASE_URL=sqlite:///./sirius_v4.db
   MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DATABASE=sirius_v4
   MONGODB_COLLECTION=valuation_files
   OPENAI_API_KEY=tu_openai_api_key_aqui
   LLM_MODEL=gpt-4
   LLM_TEMPERATURE=0.3
   SECRET_KEY=mi-clave-secreta-12345-abcde
   ENVIRONMENT=development
   LOG_LEVEL=INFO
   API_V1_PREFIX=/api/v1
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

6. **Guarda el archivo:**
   - Presiona `Ctrl + S` o ve a "Archivo" → "Guardar"

---

## 🔑 PASO 2: Configurar las credenciales

Ahora necesitas editar el archivo `.env` que acabas de abrir. Te explico cada sección:

### 📊 Sección 1: Base de Datos (YA ESTÁ CONFIGURADA)

Busca esta línea en el archivo:
```
DATABASE_URL=sqlite:///./sirius_v4.db
```

**✅ NO NECESITAS CAMBIAR NADA AQUÍ** - Ya está configurada para usar SQLite (un archivo local).

---

### 🍃 Sección 2: MongoDB Atlas (Almacenamiento de Archivos)

MongoDB Atlas es donde se almacenan los archivos de valoración. Es más simple que SharePoint y no requiere autenticación compleja.

**¿Dónde obtener el connection string?**

1. **Ve a:** https://www.mongodb.com/cloud/atlas/register
2. **Crea una cuenta** gratuita (hay tier gratuito disponible)
3. **Crea un cluster** (toma 3-5 minutos)
4. **Configura un usuario** de base de datos
5. **Obtén el connection string:**
   - Ve a "Database" → "Connect"
   - Selecciona "Connect your application"
   - Copia el connection string

En el archivo `.env`, reemplaza:
```
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=sirius_v4
MONGODB_COLLECTION=valuation_files
```

**Ejemplo de cómo debería verse:**
```
MONGODB_URI=mongodb+srv://sirius_user:MiPassword123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=sirius_v4
MONGODB_COLLECTION=valuation_files
```

**⚠️ IMPORTANTE:** 
- Reemplaza `usuario` y `password` con tus credenciales reales
- Reemplaza `cluster.mongodb.net` con la URL de tu cluster
- Si tu contraseña tiene caracteres especiales, codifícalos (ej: `@` → `%40`)

**💡 Consejo:** Si no tienes MongoDB Atlas configurado aún, puedes dejar estos valores vacíos temporalmente. El asistente funcionará, pero no podrá leer archivos desde MongoDB automáticamente.

**📖 Para más detalles sobre configuración de MongoDB Atlas, consulta:** [docs/MONGODB_SETUP.md](MONGODB_SETUP.md)

---

### 🤖 Sección 3: OpenAI (Para el asistente inteligente)

Necesitas una clave de API de OpenAI para que el asistente entienda tus preguntas en lenguaje natural.

**¿Dónde obtenerla?**

1. **Ve a:** https://platform.openai.com
2. **Crea una cuenta** o inicia sesión
3. **Ve a:** "API Keys" (Claves de API)
4. **Haz clic en:** "Create new secret key" (Crear nueva clave secreta)
5. **Copia la clave** (solo se muestra una vez, guárdala bien)

En el archivo `.env`, reemplaza:
```
OPENAI_API_KEY=tu_api_key_aqui
```

**Ejemplo de cómo debería verse:**
```
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234
```

**⚠️ IMPORTANTE:** 
- Esta clave es como una contraseña, no la compartas
- Si la pierdes, tendrás que crear una nueva
- Puede tener un costo asociado (consulta los precios en OpenAI)

---

### 🔒 Sección 4: Clave Secreta de la Aplicación

Busca esta línea:
```
SECRET_KEY=genera-una-clave-secreta-segura
```

**Reemplázala con cualquier texto aleatorio**, por ejemplo:
```
SECRET_KEY=mi-clave-super-secreta-12345-abcde
```

**💡 Consejo:** Puede ser cualquier texto largo y aleatorio. No tiene que ser algo específico.

---

## 💾 PASO 3: Guardar el archivo

1. **En el Bloc de notas**, presiona `Ctrl + S` o ve a "Archivo" → "Guardar"
2. **Cierra el Bloc de notas**

---

## 🗄️ PASO 4: Crear la base de datos

La base de datos es como un archivo donde se guardan todos los datos. Se crea automáticamente.

### Cómo hacerlo:

1. **Abre la Terminal de Windows (PowerShell):**
   - Presiona `Windows + X`
   - Selecciona "Windows PowerShell" o "Terminal"

2. **Navega a la carpeta del proyecto:**
   Escribe este comando y presiona Enter:
   ```powershell
   cd "C:\Users\TU_USUARIO\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4"
   ```
   *(Reemplaza TU_USUARIO con tu nombre de usuario)*

3. **Ejecuta el comando para crear la base de datos:**
   ```powershell
   python scripts/init_db.py
   ```

4. **Deberías ver un mensaje como:**
   ```
   ✓ Tablas creadas exitosamente
   ```

**✅ ¡Listo!** La base de datos está creada.

---

## 🚀 PASO 5: Ejecutar el asistente

Ahora puedes iniciar el asistente.

### Cómo hacerlo:

1. **En la Terminal (PowerShell), escribe:**
   ```powershell
   cd backend
   python -m uvicorn main:app --reload
   ```

2. **Deberías ver mensajes como:**
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete.
   ```

3. **¡El asistente está funcionando!** 🎉

---

## 🌐 PASO 6: Abrir el asistente en el navegador

1. **Abre tu navegador web** (Chrome, Edge, Firefox, etc.)

2. **Escribe en la barra de direcciones:**
   ```
   http://localhost:8000
   ```

3. **Presiona Enter**

4. **Deberías ver la interfaz del asistente S.I.R.I.U.S V4**

---

## 💬 Cómo usar el asistente

### Hacer una pregunta:

1. **Escribe tu pregunta** en el cuadro de texto en la parte inferior
2. **Presiona Enter** o haz clic en "Enviar"

### Ejemplos de preguntas:

- "¿Cuál es el precio limpio del TES CO000123 hoy en Precia?"
- "Compara PIP Latam vs Precia para el ISIN CO000123456"
- "Trae valoración de ayer para estos ISINs: CO000123456, CO000789012"

### Usar filtros:

En el panel izquierdo puedes:
- **Seleccionar una fecha** específica
- **Elegir un proveedor** (PIP Latam o Precia)
- **Escribir ISINs** separados por coma

---

## 📊 Cargar datos (Ingesta)

Para que el asistente tenga datos con los que trabajar, necesitas cargar archivos de valoración.

### Opción 1: Cargar archivo manualmente

1. **Prepara tu archivo** (Excel o CSV) con los datos de valoración
2. **En la Terminal**, detén el asistente (presiona `Ctrl + C`)
3. **Ejecuta:**
   ```powershell
   python scripts/ingest_file.py --file "ruta/a/tu/archivo.xlsx" --provider PIP_LATAM
   ```
   *(Reemplaza "ruta/a/tu/archivo.xlsx" con la ruta real de tu archivo)*

4. **Deberías ver:**
   ```
   ✓ Ingesta exitosa!
     - Registros procesados: 150
   ```

5. **Vuelve a iniciar el asistente:**
   ```powershell
   python -m uvicorn main:app --reload
   ```

### Opción 2: Cargar desde MongoDB Atlas (si está configurado)

**Primero, sube archivos a MongoDB:**
```powershell
python scripts/upload_to_mongodb.py --file "archivo.xlsx" --provider PIP_LATAM --fecha 2025-01-15
```

**Luego, ingiere los archivos:**
```powershell
# Ingerir archivo más reciente
python scripts/ingest_mongodb.py --provider PIP_LATAM

# O ingerir archivo específico
python scripts/ingest_mongodb.py --provider PIP_LATAM --file-id "ID_DEL_ARCHIVO"
```

**📖 Para más información sobre MongoDB Atlas, consulta:** [docs/MONGODB_SETUP.md](MONGODB_SETUP.md)

---

## ❌ Solución de Problemas Comunes

### Problema 1: "No se puede abrir el archivo .env"

**Solución:**
- Asegúrate de estar en la carpeta correcta: `backend`
- Verifica que el archivo se llame exactamente `.env` (con el punto al inicio)
- Intenta abrirlo con el Bloc de notas directamente

---

### Problema 2: "Error al crear la base de datos"

**Solución:**
- Verifica que Python esté instalado: escribe `python --version` en la Terminal
- Asegúrate de estar en la carpeta correcta del proyecto
- Intenta ejecutar el comando de nuevo

---

### Problema 3: "El asistente no inicia"

**Solución:**
- Verifica que el archivo `.env` esté en la carpeta `backend`
- Revisa que todas las credenciales estén correctamente escritas (sin espacios extra)
- Asegúrate de que no haya errores de escritura en el archivo `.env`

---

### Problema 4: "Error al hacer una pregunta"

**Solución:**
- Verifica que tu clave de OpenAI sea válida
- Asegúrate de tener créditos en tu cuenta de OpenAI
- Revisa que hayas cargado datos en la base de datos

---

### Problema 5: "No encuentro la carpeta del proyecto"

**Solución:**
1. Abre el Explorador de Archivos
2. En la barra de direcciones, escribe:
   ```
   %USERPROFILE%\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4
   ```
3. Presiona Enter

---

## 📋 Checklist Final

Antes de usar el asistente, verifica que tengas:

- [ ] Archivo `.env` creado en la carpeta `backend`
- [ ] MongoDB Atlas configurado (connection string en .env)
- [ ] Clave de OpenAI configurada
- [ ] Clave secreta (SECRET_KEY) configurada
- [ ] Base de datos creada (ejecutaste `init_db.py`)
- [ ] Asistente ejecutándose (uvicorn corriendo)
- [ ] Navegador abierto en `http://localhost:8000`
- [ ] Datos cargados en la base de datos (al menos un archivo de valoración)

---

## 🆘 ¿Necesitas ayuda?

Si tienes problemas:

1. **Revisa esta guía** paso a paso
2. **Verifica el checklist** de arriba
3. **Lee los mensajes de error** - suelen indicar qué está mal
4. **Contacta al equipo técnico** si el problema persiste

---

## 🎉 ¡Felicidades!

Si llegaste hasta aquí y el asistente está funcionando, ¡has completado la configuración exitosamente!

Ahora puedes:
- ✅ Hacer preguntas sobre valoraciones
- ✅ Comparar proveedores
- ✅ Ver alertas y recomendaciones
- ✅ Cargar nuevos datos cuando sea necesario

**¡Disfruta usando S.I.R.I.U.S V4!** 🚀

---

## 📝 Notas Adicionales

### ¿Qué hace cada cosa?

- **Base de datos (SQLite):** Guarda todos los datos de valoración. Es un archivo llamado `sirius_v4.db` en la carpeta `backend`.

- **MongoDB Atlas:** Es donde se almacenan los archivos de valoración. El asistente puede leerlos automáticamente desde allí.

- **OpenAI:** Es el "cerebro" del asistente. Entiende tus preguntas en lenguaje natural y genera respuestas inteligentes.

- **FastAPI/Uvicorn:** Es el "motor" que hace funcionar el asistente. Es como el servidor que responde a tus solicitudes.

### ¿Puedo usar el asistente sin MongoDB Atlas?

**Sí.** Puedes cargar archivos manualmente usando el script `ingest_file.py`. El asistente funcionará igual de bien. MongoDB Atlas solo es necesario si quieres almacenar y gestionar archivos en la nube.

### ¿Puedo usar el asistente sin OpenAI?

**No.** OpenAI es necesario para que el asistente entienda tus preguntas en lenguaje natural. Sin esta clave, el asistente no podrá procesar consultas.

### ¿Cuánto cuesta usar OpenAI?

Depende de cuánto uses el asistente. Consulta los precios en: https://openai.com/pricing

---

*Última actualización: Noviembre 2025*

