"""
Script para inspeccionar las columnas de las tablas BD_PIP y BD_Precia en Supabase
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

def main():
    """Inspecciona las columnas de las tablas en Supabase"""
    print("=" * 60)
    print("Inspeccionando Columnas de Supabase")
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
    
    for table_name in tables:
        print(f"Tabla: {table_name}")
        print("-" * 60)
        
        try:
            # Intentar obtener una fila para ver las columnas
            url = f"{api_url}/{table_name}?select=*&limit=1"
            response = httpx.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    columns = list(data[0].keys())
                    print(f"Columnas encontradas ({len(columns)}):")
                    for col in sorted(columns):
                        value = data[0].get(col)
                        value_type = type(value).__name__
                        print(f"  - {col} ({value_type})")
                else:
                    print("  Tabla vacia - intentando obtener estructura...")
                    # Si está vacía, intentar con una consulta que siempre funcione
                    url2 = f"{api_url}/{table_name}?select=*&limit=0"
                    response2 = httpx.get(url2, headers=headers, timeout=10.0)
                    if response2.status_code == 200:
                        print("  Tabla existe pero no tiene datos")
                    else:
                        print(f"  Error: {response2.status_code} - {response2.text[:200]}")
            else:
                print(f"  Error HTTP {response.status_code}: {response.text[:200]}")
        
        except Exception as e:
            print(f"  Error: {str(e)}")
        
        print()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)




