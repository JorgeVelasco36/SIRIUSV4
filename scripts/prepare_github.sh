#!/bin/bash
# Script para preparar el repositorio para GitHub

echo "=== Preparando repositorio para GitHub ==="

# Verificar si Git está instalado
if ! command -v git &> /dev/null; then
    echo "ERROR: Git no está instalado. Por favor instala Git primero."
    exit 1
fi

# Inicializar repositorio si no existe
if [ ! -d .git ]; then
    echo "Inicializando repositorio Git..."
    git init
fi

# Agregar todos los archivos
echo "Agregando archivos al staging..."
git add .

# Crear commit
echo "Creando commit..."
git commit -m "Migración a Supabase: Autenticación con correo/contraseña y corrección de errores

- Migración completa de MongoDB a Supabase
- Autenticación con correo y contraseña en lugar de API Key
- Verificación y mapeo de columnas de Supabase
- Corrección de errores en endpoint de chat
- Actualización de servicios de ingesta
- Documentación actualizada"

echo ""
echo "=== Repositorio preparado ==="
echo ""
echo "Para subir a GitHub, ejecuta:"
echo "  git remote add origin <URL_DEL_REPOSITORIO>"
echo "  git branch -M main"
echo "  git push -u origin main"




