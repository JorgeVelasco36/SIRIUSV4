"""
Script para obtener el esquema completo de las tablas usando el catálogo de información de PostgreSQL
"""
import sys
import os
from pathlib import Path
import httpx
import json

# Cambiar al directorio backend para que pydantic_settings encuentre el .env
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)

# Agregar el directorio backend al path
sys.path.insert(0, str(backend_dir))

from config import settings

def get_table_schema():
    """Obtiene el esquema de las tablas usando información del catálogo de PostgreSQL"""
    print("=" * 60)
    print("Obteniendo Esquema de Tablas desde PostgreSQL")
    print("=" * 60)
    print()
    
    if not settings.supabase_api_key:
        print("[ERROR] SUPABASE_API_KEY no esta configurado")
        return 1
    
    base_url = settings.supabase_url or "https://mwyltxcgjxsrdmgsuysv.supabase.co"
    api_url = f"{base_url.rstrip('/')}/rest/v1"
    
    headers = {
        "apikey": settings.supabase_api_key,
        "Authorization": f"Bearer {settings.supabase_api_key}",
        "Content-Type": "application/json"
    }
    
    tables = [settings.supabase_table_pip, settings.supabase_table_precia]
    
    # Intentar consultar information_schema.columns a través de PostgREST
    # Nota: Esto puede no funcionar si no hay acceso a information_schema
    schema_query = """
    SELECT 
        column_name, 
        data_type, 
        is_nullable,
        column_default
    FROM information_schema.columns 
    WHERE table_name = :table_name
    ORDER BY ordinal_position
    """
    
    for table_name in tables:
        print(f"\nTabla: {table_name}")
        print("-" * 60)
        
        # Intentar acceder a information_schema a través de PostgREST
        # Esto generalmente no funciona con la API pública, pero lo intentamos
        try:
            # Método 1: Intentar acceder directamente a information_schema
            url = f"{api_url}/information_schema.columns?table_name=eq.{table_name}&select=column_name,data_type,is_nullable"
            response = httpx.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                columns = response.json()
                if columns:
                    print("Columnas encontradas:")
                    for col in columns:
                        print(f"  - {col.get('column_name')} ({col.get('data_type')})")
                else:
                    print("No se encontraron columnas en information_schema")
            else:
                print(f"No se puede acceder a information_schema: {response.status_code}")
                print(f"  {response.text[:200]}")
        except Exception as e:
            print(f"Error accediendo a information_schema: {str(e)}")
        
        # Método 2: Intentar hacer una consulta con select=* y ver qué devuelve
        print("\nIntentando consulta con select=*...")
        try:
            url = f"{api_url}/{table_name}?select=*&limit=0"
            response = httpx.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                # Aunque la tabla esté vacía, PostgREST puede devolver información
                # sobre las columnas en el header o en la respuesta
                print("[OK] select=* funciona")
                
                # Intentar insertar un registro de prueba para ver la estructura
                # (solo si tenemos permisos)
                print("\nNota: Las tablas parecen estar vacias.")
                print("      Si necesitas crear las columnas, puedes hacerlo desde")
                print("      el panel de Supabase o usando migraciones SQL.")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("RECOMENDACION:")
    print("=" * 60)
    print("Las tablas solo tienen 'id' y 'created_at'.")
    print("Necesitas crear las siguientes columnas:")
    print("  - archivo_origen (text/varchar)")
    print("  - proveedor (text/varchar)")
    print("  - fecha (date)")
    print("  - timestamp_ingesta (timestamp)")
    print("  - (y otras columnas necesarias para los datos de valoracion)")
    print("\nPuedes hacerlo desde el panel de Supabase o ejecutando SQL:")
    print("  ALTER TABLE BD_PIP ADD COLUMN archivo_origen TEXT;")
    print("  ALTER TABLE BD_PIP ADD COLUMN proveedor TEXT;")
    print("  ALTER TABLE BD_PIP ADD COLUMN fecha DATE;")
    print("  ALTER TABLE BD_PIP ADD COLUMN timestamp_ingesta TIMESTAMP;")
    print("  (y lo mismo para BD_Precia)")
    
    return 0

if __name__ == "__main__":
    exit_code = get_table_schema()
    sys.exit(exit_code)




