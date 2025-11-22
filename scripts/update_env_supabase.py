"""
Script para actualizar el archivo .env con la configuración de Supabase
"""
import os
import sys
import re

def update_env_file(env_path, supabase_url, supabase_password=None):
    """
    Actualiza el archivo .env con la configuración de Supabase
    
    Args:
        env_path: Ruta al archivo .env
        supabase_url: URL completa de Supabase (con o sin contraseña)
        supabase_password: Contraseña para reemplazar [YOUR_PASSWORD] si está en la URL
    """
    if not os.path.exists(env_path):
        print(f"❌ El archivo {env_path} no existe")
        return False
    
    # Leer el archivo actual
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Si la URL tiene [YOUR_PASSWORD] y se proporcionó una contraseña, reemplazarla
    if supabase_password and '[YOUR_PASSWORD]' in supabase_url:
        supabase_url = supabase_url.replace('[YOUR_PASSWORD]', supabase_password)
    
    # Preparar las nuevas líneas
    new_lines = []
    new_lines.append("")
    new_lines.append("# Supabase PostgreSQL Configuration")
    new_lines.append(f"SUPABASE_DB_URL={supabase_url}")
    new_lines.append("SUPABASE_DB_NAME=postgres")
    new_lines.append("SUPABASE_TABLE_PIP=BD_PIP")
    new_lines.append("SUPABASE_TABLE_PRECIA=BD_Precia")
    new_lines.append("")
    new_lines.append("# MongoDB Atlas (deprecated - ya no se usa)")
    new_lines.append("# MONGODB_URI=")
    new_lines.append("# MONGODB_DATABASE=sirius_v4")
    new_lines.append("# MONGODB_COLLECTION=valuation_files")
    
    # Verificar si ya existe configuración de Supabase
    if 'SUPABASE_DB_URL' in content:
        # Actualizar la línea existente
        content = re.sub(
            r'SUPABASE_DB_URL=.*',
            f'SUPABASE_DB_URL={supabase_url}',
            content
        )
        # Asegurar que las otras configuraciones existan
        if 'SUPABASE_DB_NAME' not in content:
            content += f"\nSUPABASE_DB_NAME=postgres"
        if 'SUPABASE_TABLE_PIP' not in content:
            content += f"\nSUPABASE_TABLE_PIP=BD_PIP"
        if 'SUPABASE_TABLE_PRECIA' not in content:
            content += f"\nSUPABASE_TABLE_PRECIA=BD_Precia"
    else:
        # Agregar al final del archivo
        content += "\n" + "\n".join(new_lines)
    
    # Escribir el archivo actualizado
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Archivo {env_path} actualizado exitosamente")
    return True


if __name__ == "__main__":
    # Ruta al archivo .env
    backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
    env_path = os.path.join(backend_dir, '.env')
    
    # URL de Supabase desde la imagen
    # El usuario debe reemplazar [YOUR_PASSWORD] con su contraseña real
    default_supabase_url = "postgresql://postgres:[YOUR_PASSWORD]@db.mwyltxcgjxsrdmgsuysv.supabase.co:5432/postgres"
    
    print("=" * 60)
    print("Actualización de .env para Supabase")
    print("=" * 60)
    print()
    print("IMPORTANTE: Debes reemplazar [YOUR_PASSWORD] con tu contraseña real")
    print()
    
    # Pedir la contraseña al usuario
    password = input("Ingresa la contraseña de Supabase (o presiona Enter para dejar [YOUR_PASSWORD]): ").strip()
    
    if password:
        supabase_url = default_supabase_url.replace('[YOUR_PASSWORD]', password)
    else:
        supabase_url = default_supabase_url
        print("⚠️  Se dejará [YOUR_PASSWORD] en el archivo. Debes reemplazarlo manualmente.")
    
    if update_env_file(env_path, supabase_url):
        print()
        print("✅ Configuración completada")
        print()
        print("Próximos pasos:")
        print("1. Verifica que la contraseña esté correcta en el archivo .env")
        print("2. Ejecuta: python scripts/test_supabase_connection.py")
    else:
        print("❌ Error actualizando el archivo")
        sys.exit(1)

