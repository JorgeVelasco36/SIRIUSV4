# Guía para Subir SIRIUS V4 a GitHub

## 📋 Pasos para Guardar el Proyecto en GitHub

### Paso 1: Verificar que Git esté instalado

Abre PowerShell y ejecuta:
```powershell
git --version
```

Si Git no está instalado, descárgalo desde: https://git-scm.com/download/win

### Paso 2: Inicializar el repositorio (si no está inicializado)

```powershell
cd "C:\Users\JEVD4139\Desktop\Documentos\Micro Inteligencia Artificial\Proyecto\SIRIUS\V4"
git init
```

### Paso 3: Agregar todos los archivos

```powershell
git add .
```

### Paso 4: Crear el commit inicial

```powershell
git commit -m "Migración a Supabase: Autenticación con correo/contraseña y corrección de errores

- Migración completa de MongoDB a Supabase
- Autenticación con correo y contraseña en lugar de API Key
- Verificación y mapeo de columnas de Supabase
- Corrección de errores en endpoint de chat
- Actualización de servicios de ingesta
- Documentación actualizada"
```

### Paso 5: Crear un repositorio en GitHub

1. Ve a https://github.com
2. Haz clic en el botón "+" en la esquina superior derecha
3. Selecciona "New repository"
4. Nombre del repositorio: `SIRIUS-V4` (o el nombre que prefieras)
5. Descripción: "Sistema Inteligente de Renta Fija e Inversión Unificada V4"
6. Elige si será público o privado
7. **NO** marques "Initialize this repository with a README" (ya tenemos uno)
8. Haz clic en "Create repository"

### Paso 6: Conectar el repositorio local con GitHub

GitHub te mostrará comandos después de crear el repositorio. Ejecuta estos comandos (reemplaza `TU_USUARIO` con tu usuario de GitHub):

```powershell
git remote add origin https://github.com/TU_USUARIO/SIRIUS-V4.git
git branch -M main
git push -u origin main
```

### Paso 7: Autenticación

Si es la primera vez que usas Git en esta máquina, GitHub te pedirá autenticarte. Puedes usar:

- **Personal Access Token** (recomendado): 
  1. Ve a GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
  2. Genera un nuevo token con permisos `repo`
  3. Úsalo como contraseña cuando Git te lo pida

- **GitHub CLI**: Instala GitHub CLI y autentica con `gh auth login`

## 🔒 Archivos que NO se suben a GitHub

El archivo `.gitignore` está configurado para **NO** subir:
- Archivos `.env` (con credenciales)
- Bases de datos locales (`*.db`, `*.sqlite`)
- Archivos de Python compilados (`__pycache__/`)
- Node modules (`node_modules/`)
- Archivos temporales y logs

## ✅ Verificación

Después de hacer push, verifica que todo se subió correctamente:

1. Ve a tu repositorio en GitHub: `https://github.com/TU_USUARIO/SIRIUS-V4`
2. Verifica que todos los archivos estén presentes
3. Verifica que el archivo `.env` **NO** esté presente (por seguridad)

## 🔄 Actualizaciones Futuras

Para actualizar el repositorio después de hacer cambios:

```powershell
git add .
git commit -m "Descripción de los cambios realizados"
git push
```

## 📝 Notas Importantes

- **NUNCA** subas archivos `.env` con credenciales reales
- El archivo `env.example` está incluido como plantilla
- Las bases de datos locales no se suben (están en `.gitignore`)
- Los archivos de configuración sensibles están excluidos

## 🆘 Problemas Comunes

### Error: "remote origin already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/TU_USUARIO/SIRIUS-V4.git
```

### Error: "authentication failed"
- Verifica que tu token de acceso sea válido
- Regenera el token si es necesario
- Asegúrate de usar HTTPS, no SSH

### Error: "failed to push some refs"
```powershell
git pull origin main --allow-unrelated-histories
git push -u origin main
```




