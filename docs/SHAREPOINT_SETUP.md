# 🔗 Configuración de SharePoint - S.I.R.I.U.S V4

## 📍 Información del SharePoint

**Enlace proporcionado:**
```
https://grupocoomeva.sharepoint.com/:f:/s/FIDUCIARIACOOMEVA/fic/FVP/IgCINeOLvbBpTZz4ukbBVs5VAc2a27LW1rBOdCkZZNRn9zg?e=adVGrf
```

**Información extraída:**
- **Dominio:** grupocoomeva.sharepoint.com
- **Site:** FIDUCIARIACOOMEVA
- **Carpetas:** Precia y PIP Latam
- **Folder ID:** IgCINeOLvbBpTZz4ukbBVs5VAc2a27LW1rBOdCkZZNRn9zg

---

## 🔧 Configuración Paso a Paso

### PASO 1: Configurar Azure App Registration

1. **Ve a Azure Portal:** https://portal.azure.com
2. **Inicia sesión** con tu cuenta corporativa
3. **Busca:** "Azure Active Directory" → "App registrations"
4. **Crea una nueva aplicación:**
   - Haz clic en "New registration"
   - **Name:** SIRIUS V4
   - **Supported account types:** Accounts in this organizational directory only
   - **Redirect URI:** 
     - Platform: Public client/native
     - URI: `http://localhost`

5. **Configura permisos:**
   - Ve a "API permissions"
   - Haz clic en "Add a permission"
   - Selecciona "Microsoft Graph"
   - Selecciona "Delegated permissions"
   - Agrega:
     - `Files.Read.All`
     - `Sites.Read.All`
   - Haz clic en "Add permissions"
   - **IMPORTANTE:** Haz clic en "Grant admin consent" si eres administrador

6. **Copia los valores:**
   - **Application (client) ID** → Este es tu `AZURE_CLIENT_ID`
   - **Directory (tenant) ID** → Este es tu `AZURE_TENANT_ID`
   - **NO necesitas Client Secret** para autenticación interactiva

---

### PASO 2: Configurar el archivo .env

Edita el archivo `.env` en la carpeta `backend`:

```env
# Microsoft Graph API (SharePoint)
AZURE_CLIENT_ID=tu-client-id-de-azure
AZURE_TENANT_ID=tu-tenant-id-de-azure
# Deja estos vacíos para autenticación interactiva
AZURE_CLIENT_SECRET=
SHAREPOINT_SITE_ID=FIDUCIARIACOOMEVA
SHAREPOINT_DRIVE_ID=
```

**Ejemplo:**
```env
AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789abc
AZURE_TENANT_ID=87654321-4321-4321-4321-cba987654321
AZURE_CLIENT_SECRET=
SHAREPOINT_SITE_ID=FIDUCIARIACOOMEVA
SHAREPOINT_DRIVE_ID=
```

---

### PASO 3: Autenticación Inicial

La primera vez que uses SharePoint, necesitas autenticarte:

1. **Abre PowerShell** en la carpeta del proyecto

2. **Ejecuta el script de autenticación:**
   ```powershell
   python scripts/sharepoint_auth.py
   ```

3. **Se abrirá tu navegador:**
   - Inicia sesión con tu usuario corporativo
   - Acepta los permisos solicitados
   - El token se guardará automáticamente

4. **Verás un mensaje de éxito:**
   ```
   ✓ Autenticación exitosa!
   ✓ Token guardado para uso futuro
   ```

---

### PASO 4: Obtener IDs de las Carpetas

Para usar las carpetas "Precia" y "PIP Latam", necesitas sus IDs:

**Opción A: Desde el enlace proporcionado**

El enlace ya contiene el ID de la carpeta principal:
```
Folder ID: IgCINeOLvbBpTZz4ukbBVs5VAc2a27LW1rBOdCkZZNRn9zg
```

**Opción B: Usar el script de exploración**

Crea un script temporal para listar las carpetas:

```python
from backend.services.sharepoint_service import SharePointService

service = SharePointService(use_interactive_auth=True)
folder_id = "IgCINeOLvbBpTZz4ukbBVs5VAc2a27LW1rBOdCkZZNRn9zg"
files = service.list_files_in_folder(folder_id)

for item in files:
    print(f"{item['name']} - ID: {item['id']}")
```

---

## 📊 Uso del Servicio

### Listar archivos en una carpeta específica

```python
from backend.services.sharepoint_service import SharePointService

service = SharePointService(use_interactive_auth=True)

# Carpeta Precia
precia_folder_id = "ID_DE_LA_CARPETA_PRECIA"
precia_files = service.list_files_in_folder(precia_folder_id, file_extension="xlsx")

# Carpeta PIP Latam
pip_folder_id = "ID_DE_LA_CARPETA_PIP_LATAM"
pip_files = service.list_files_in_folder(pip_folder_id, file_extension="xlsx")
```

### Descargar un archivo

```python
file_id = "ID_DEL_ARCHIVO"
file_content = service.download_file(file_id)
```

---

## 🔄 Renovación de Tokens

El token se renueva automáticamente cuando:
- El token expira (normalmente después de 1 hora)
- El token de refresh es válido (puede durar días/semanas)

Si el token expira completamente:
1. Ejecuta nuevamente: `python scripts/sharepoint_auth.py`
2. Se abrirá el navegador para reautenticarte

---

## ❌ Solución de Problemas

### Error: "No se puede obtener token"

**Solución:**
- Verifica que `AZURE_CLIENT_ID` y `AZURE_TENANT_ID` estén correctos
- Ejecuta `python scripts/sharepoint_auth.py` para reautenticarte
- Verifica que la aplicación tenga los permisos correctos en Azure

### Error: "Access denied"

**Solución:**
- Verifica que hayas dado consentimiento a la aplicación
- Verifica que tengas acceso a la carpeta de SharePoint
- Contacta al administrador para que otorgue permisos

### Error: "Site not found"

**Solución:**
- Verifica que `SHAREPOINT_SITE_ID` sea correcto
- El Site ID debe ser solo el nombre del sitio: `FIDUCIARIACOOMEVA`
- No incluyas la URL completa

### El navegador no se abre

**Solución:**
- Asegúrate de tener un navegador predeterminado configurado
- Intenta abrir manualmente: http://localhost
- Verifica que no haya un firewall bloqueando

---

## 🔐 Seguridad

- **Token Cache:** Se guarda en `sharepoint_token_cache.json`
- **No compartas este archivo** - contiene credenciales de acceso
- **Agrega a .gitignore:** El archivo ya está en .gitignore por defecto

---

## 📝 Notas Importantes

1. **Autenticación por Usuario:** Cada usuario debe autenticarse con su propia cuenta
2. **Permisos:** El usuario debe tener acceso a las carpetas de SharePoint
3. **Token Persistente:** Una vez autenticado, no necesitas volver a hacerlo hasta que expire
4. **Múltiples Usuarios:** Cada usuario tendrá su propio token cache

---

## 🎯 Próximos Pasos

Después de configurar SharePoint:

1. ✅ Autenticarte con `sharepoint_auth.py`
2. ✅ Obtener los IDs de las carpetas "Precia" y "PIP Latam"
3. ✅ Configurar los scripts de ingesta para usar estos IDs
4. ✅ Probar la ingesta desde SharePoint

---

*Última actualización: Noviembre 2025*









