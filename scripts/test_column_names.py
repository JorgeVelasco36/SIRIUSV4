"""
Script para probar diferentes nombres de columnas en Supabase
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

def test_column_combinations():
    """Prueba diferentes combinaciones de nombres de columnas"""
    print("=" * 60)
    print("Probando Nombres de Columnas en Supabase")
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
    
    # Posibles variaciones de nombres de columnas
    column_variations = [
        # Nombres actuales en el código
        ["archivo_origen", "proveedor", "fecha", "timestamp_ingesta"],
        # Variaciones con mayúsculas
        ["Archivo_Origen", "Proveedor", "Fecha", "Timestamp_Ingesta"],
        ["ARCHIVO_ORIGEN", "PROVEEDOR", "FECHA", "TIMESTAMP_INGESTA"],
        # Variaciones con guiones
        ["archivo-origen", "proveedor", "fecha", "timestamp-ingesta"],
        # Variaciones sin guiones bajos
        ["archivoorigen", "proveedor", "fecha", "timestampingesta"],
        # Variaciones en inglés
        ["file_name", "provider", "date", "upload_date"],
        ["file_name", "provider", "valuation_date", "upload_timestamp"],
        # Variaciones comunes
        ["nombre_archivo", "proveedor", "fecha_valoracion", "fecha_ingesta"],
        ["archivo", "proveedor", "fecha", "fecha_ingesta"],
    ]
    
    for table_name in tables:
        print(f"\nTabla: {table_name}")
        print("-" * 60)
        
        for i, columns in enumerate(column_variations, 1):
            try:
                select_cols = ",".join(columns)
                url = f"{api_url}/{table_name}?select={select_cols}&limit=1"
                response = httpx.get(url, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    print(f"[OK] Variacion {i}: {columns}")
                    data = response.json()
                    if data and len(data) > 0:
                        print(f"     Datos encontrados: {list(data[0].keys())}")
                    else:
                        print(f"     Tabla vacia pero columnas validas")
                    break  # Si funciona, no probar más variaciones
                elif response.status_code == 400:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("message", response.text[:100])
                    if "does not exist" in error_msg or "column" in error_msg.lower():
                        # Error de columna, continuar probando
                        pass
                    else:
                        print(f"[INFO] Variacion {i}: {columns}")
                        print(f"     Error 400: {error_msg[:100]}")
                else:
                    print(f"[INFO] Variacion {i}: {columns}")
                    print(f"     Status {response.status_code}: {response.text[:100]}")
            except Exception as e:
                # Continuar con la siguiente variación
                pass
        
        # Si ninguna funcionó, intentar obtener información del esquema
        print("\nIntentando obtener informacion del esquema...")
        try:
            # Intentar con select=* para ver qué columnas devuelve
            url = f"{api_url}/{table_name}?select=*&limit=0"
            response = httpx.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                print("[INFO] select=* funciona (tabla existe)")
            else:
                print(f"[INFO] select=* falla: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"[INFO] Error: {str(e)}")
    
    return 0

if __name__ == "__main__":
    exit_code = test_column_combinations()
    sys.exit(exit_code)




