#!/usr/bin/env python3
"""
Script para verificar si un ISIN existe en la base de datos local y en Supabase
"""
import sys
import os
from pathlib import Path

# Cambiar al directorio backend para cargar .env
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)

sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models import Valuation
from services.supabase_service import SupabaseService
from config import settings
import httpx

def check_local_db(isin: str):
    """Verifica si el ISIN existe en la base de datos local"""
    db = SessionLocal()
    try:
        result = db.query(Valuation).filter(Valuation.isin == isin).first()
        if result:
            print(f"[OK] ISIN {isin} encontrado en BD local:")
            print(f"  - Proveedor: {result.proveedor.value}")
            print(f"  - Fecha: {result.fecha}")
            print(f"  - Precio Limpio: {result.precio_limpio}")
            print(f"  - Tasa: {result.tasa}")
            return True
        else:
            print(f"[INFO] ISIN {isin} NO encontrado en BD local")
            return False
    finally:
        db.close()

def check_supabase(isin: str):
    """Verifica si el ISIN existe en Supabase"""
    try:
        # Intentar con API key primero
        supabase = SupabaseService(api_key=settings.supabase_api_key)
        
        # Buscar en ambas tablas
        for table_name in [settings.supabase_table_pip, settings.supabase_table_precia]:
            try:
                # Obtener columnas disponibles
                available_columns = supabase._get_available_columns(table_name)
                
                # Buscar columna ISIN
                isin_col = None
                for col in ["ISIN", "isin", "ISIN_CODIGO", "codigo_isin"]:
                    if col in available_columns:
                        isin_col = col
                        break
                
                if not isin_col:
                    print(f"[ADVERTENCIA] No se encontró columna ISIN en {table_name}")
                    continue
                
                # Consultar Supabase
                url = f"{supabase.api_url}/{table_name}"
                params = {
                    "select": "*",
                    f"{isin_col}": f"eq.{isin}",
                    "limit": "1"
                }
                
                response = supabase._make_request("GET", url, params=params)
                
                if response and len(response) > 0:
                    print(f"[OK] ISIN {isin} encontrado en Supabase (tabla {table_name}):")
                    record = response[0]
                    print(f"  - Columnas disponibles: {list(record.keys())[:5]}...")
                    return True
                else:
                    print(f"[INFO] ISIN {isin} NO encontrado en Supabase (tabla {table_name})")
            except Exception as e:
                print(f"[ERROR] Error consultando {table_name}: {str(e)}")
                continue
        
        return False
    except Exception as e:
        print(f"[ERROR] Error consultando Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    isin = sys.argv[1] if len(sys.argv) > 1 else "COB07CD0PY71"
    
    print(f"=== Verificando ISIN: {isin} ===\n")
    
    print("1. Verificando base de datos local...")
    found_local = check_local_db(isin)
    
    print("\n2. Verificando Supabase...")
    found_supabase = check_supabase(isin)
    
    print("\n=== Resumen ===")
    print(f"BD Local: {'[OK]' if found_local else '[NO]'}")
    print(f"Supabase: {'[OK]' if found_supabase else '[NO]'}")
    
    if not found_local and not found_supabase:
        print("\n[ADVERTENCIA] El ISIN no se encontró en ninguna base de datos.")
        print("Posibles causas:")
        print("  - El ISIN no existe en Supabase")
        print("  - El ISIN no ha sido ingerido a la BD local")
        print("  - El formato del ISIN es incorrecto")

