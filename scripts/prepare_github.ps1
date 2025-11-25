# Script PowerShell para preparar el repositorio para GitHub

Write-Host "=== Preparando repositorio para GitHub ===" -ForegroundColor Cyan

# Verificar si Git está instalado
try {
    $gitVersion = git --version
    Write-Host "Git encontrado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git no está instalado. Por favor instala Git primero." -ForegroundColor Red
    exit 1
}

# Inicializar repositorio si no existe
if (-not (Test-Path .git)) {
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Yellow
    git init
}

# Verificar estado
Write-Host "`nVerificando estado del repositorio..." -ForegroundColor Cyan
git status --short

# Agregar todos los archivos
Write-Host "`nAgregando archivos al staging..." -ForegroundColor Yellow
git add .

# Crear commit
Write-Host "Creando commit..." -ForegroundColor Yellow
$commitMessage = @"
Migración a Supabase: Autenticación con correo/contraseña y corrección de errores

- Migración completa de MongoDB a Supabase
- Autenticación con correo y contraseña en lugar de API Key
- Verificación y mapeo de columnas de Supabase
- Corrección de errores en endpoint de chat
- Actualización de servicios de ingesta
- Documentación actualizada
"@

git commit -m $commitMessage

Write-Host "`n=== Repositorio preparado ===" -ForegroundColor Green
Write-Host ""
Write-Host "Para subir a GitHub, ejecuta:" -ForegroundColor Cyan
Write-Host "  git remote add origin <URL_DEL_REPOSITORIO>" -ForegroundColor White
Write-Host "  git branch -M main" -ForegroundColor White
Write-Host "  git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "O si ya tienes un repositorio remoto configurado:" -ForegroundColor Cyan
Write-Host "  git push -u origin main" -ForegroundColor White




