#!/usr/bin/env python3
"""
Script para probar la consulta de un ISIN específico
"""
import sys
import os
from pathlib import Path

# Cambiar al directorio backend para cargar .env
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)

sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from services.query_service import QueryService
from services.supabase_service import SupabaseService
from schemas import ValuationQuery
from config import settings
import httpx

def test_isin_query(isin: str):
    """Prueba la consulta de un ISIN"""
    print(f"=== Probando consulta para ISIN: {isin} ===\n")
    
    db = SessionLocal()
    try:
        query_service = QueryService(db)
        
        # Crear query
        query = ValuationQuery(isin=isin)
        
        # 1. Consultar BD local
        print("1. Consultando base de datos local...")
        results_local = query_service.query_valuations(query)
        print(f"   Resultados en BD local: {len(results_local)}")
        if results_local:
            for r in results_local:
                print(f"   - ISIN: {r.isin}, Proveedor: {r.proveedor.value}, Fecha: {r.fecha}, Precio: {r.precio_limpio}")
        else:
            print("   [INFO] No se encontraron resultados en BD local")
        
        # 2. Consultar Supabase directamente
        print("\n2. Consultando Supabase directamente...")
        try:
            # Intentar con API key
            supabase = SupabaseService(api_key=settings.supabase_api_key)
            
            # Buscar en ambas tablas
            for table_name in [settings.supabase_table_pip, settings.supabase_table_precia]:
                print(f"\n   Consultando tabla: {table_name}")
                try:
                    available_columns = supabase._get_available_columns(table_name)
                    print(f"   Columnas disponibles: {len(available_columns)}")
                    
                    # Buscar columna ISIN
                    isin_col = None
                    for col in ["ISIN", "isin", "ISIN_CODIGO", "codigo_isin"]:
                        if col in available_columns:
                            isin_col = col
                            print(f"   Columna ISIN encontrada: {isin_col}")
                            break
                    
                    if not isin_col:
                        print(f"   [ERROR] No se encontró columna ISIN en {table_name}")
                        continue
                    
                    # Consultar Supabase (pasar solo el nombre de la tabla)
                    params = {
                        "select": "*",
                        f"{isin_col}": f"eq.{isin}",
                        "limit": "5"
                    }
                    
                    print(f"   Tabla: {table_name}")
                    print(f"   Parámetros: {params}")
                    
                    # Pasar solo el nombre de la tabla, _make_request construye la URL
                    response = supabase._make_request("GET", table_name, params=params)
                    
                    if response and len(response) > 0:
                        print(f"   [OK] Se encontraron {len(response)} registros")
                        for i, record in enumerate(response[:3], 1):
                            print(f"\n   Registro {i}:")
                            # Mostrar campos relevantes
                            for key in ["ISIN", "isin", "FECHA_VALORACION", "fecha", "PRECIO_LIMPIO", "precio_limpio", "TIR", "tasa"]:
                                if key in record:
                                    print(f"     {key}: {record[key]}")
                    else:
                        print(f"   [INFO] No se encontraron registros para ISIN {isin} en {table_name}")
                        
                except Exception as e:
                    print(f"   [ERROR] Error consultando {table_name}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            print(f"   [ERROR] Error general consultando Supabase: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 3. Probar consulta directa con token (si está disponible)
        print("\n3. Probando consulta directa con QueryService...")
        # Nota: Necesitaríamos un token de acceso real para probar esto
        
    finally:
        db.close()

if __name__ == "__main__":
    isin = sys.argv[1] if len(sys.argv) > 1 else "COB07CDOPY71"
    test_isin_query(isin)

