"""
Script para descubrir las columnas reales de las tablas en Supabase
haciendo consultas que generen errores informativos
"""
import sys
import os
from pathlib import Path
import httpx
import json
import re

# Cambiar al directorio backend para que pydantic_settings encuentre el .env
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)

# Agregar el directorio backend al path
sys.path.insert(0, str(backend_dir))

from config import settings

def extract_column_name_from_error(error_msg):
    """Extrae el nombre de la columna del mensaje de error"""
    # Buscar patrones como "column BD_PIP.archivo_origen does not exist"
    patterns = [
        r"column\s+[\"']?[\w\.]+[\"']?\.([\w_]+)\s+does not exist",
        r"column\s+[\"']?([\w_]+)[\"']?\s+does not exist",
        r"[\"']([\w_]+)[\"']\s+does not exist",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_msg, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def discover_columns():
    """Descubre las columnas haciendo consultas que generen errores"""
    print("=" * 60)
    print("Descubriendo Columnas Reales en Supabase")
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
    
    # Columnas comunes a probar
    test_columns = [
        "id", "ID", "Id",
        "archivo_origen", "Archivo_Origen", "ARCHIVO_ORIGEN", "archivo-origen", "archivoorigen",
        "proveedor", "Proveedor", "PROVEEDOR",
        "fecha", "Fecha", "FECHA", "fecha_valoracion", "Fecha_Valoracion",
        "timestamp_ingesta", "Timestamp_Ingesta", "TIMESTAMP_INGESTA", "timestamp-ingesta",
        "fecha_ingesta", "Fecha_Ingesta", "upload_date", "upload_timestamp",
        "created_at", "created_at", "updated_at",
    ]
    
    for table_name in tables:
        print(f"\nTabla: {table_name}")
        print("-" * 60)
        
        valid_columns = []
        invalid_columns = []
        
        # Probar cada columna individualmente
        for col in test_columns:
            try:
                # Intentar seleccionar solo esta columna
                url = f"{api_url}/{table_name}?select={col}&limit=1"
                response = httpx.get(url, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    valid_columns.append(col)
                    print(f"[OK] {col}")
                elif response.status_code == 400:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("message", response.text)
                    
                    # Si el error menciona que la columna no existe, es inválida
                    if "does not exist" in error_msg or "column" in error_msg.lower():
                        invalid_columns.append(col)
                        extracted = extract_column_name_from_error(error_msg)
                        if extracted and extracted.lower() != col.lower():
                            print(f"[NO] {col} (error menciona: {extracted})")
                        else:
                            print(f"[NO] {col}")
                    else:
                        # Otro tipo de error, podría ser válida
                        print(f"[?] {col} - Error: {error_msg[:80]}")
                else:
                    print(f"[?] {col} - Status: {response.status_code}")
            except Exception as e:
                print(f"[ERROR] {col} - {str(e)[:80]}")
        
        print(f"\nColumnas validas encontradas: {valid_columns}")
        print(f"Columnas invalidas: {len(invalid_columns)}")
        
        # Si encontramos columnas válidas, intentar una consulta combinada
        if valid_columns:
            print(f"\nProbando consulta combinada con: {', '.join(valid_columns)}")
            try:
                select_cols = ",".join(valid_columns)
                url = f"{api_url}/{table_name}?select={select_cols}&limit=1"
                response = httpx.get(url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        print(f"[OK] Consulta combinada exitosa")
                        print(f"     Columnas en respuesta: {list(data[0].keys())}")
                    else:
                        print(f"[OK] Consulta combinada exitosa (tabla vacia)")
                else:
                    print(f"[ERROR] Consulta combinada falla: {response.status_code}")
                    print(f"     {response.text[:200]}")
            except Exception as e:
                print(f"[ERROR] Consulta combinada: {str(e)}")
    
    return 0

if __name__ == "__main__":
    exit_code = discover_columns()
    sys.exit(exit_code)




