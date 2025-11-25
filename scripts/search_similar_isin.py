#!/usr/bin/env python3
"""
Script para buscar ISINs similares en Supabase
"""
import sys
import os
from pathlib import Path

# Cambiar al directorio backend para cargar .env
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)

sys.path.insert(0, str(backend_dir))

from services.supabase_service import SupabaseService
from config import settings

def search_similar_isin(isin: str):
    """Busca ISINs similares en Supabase"""
    print(f"=== Buscando ISINs similares a: {isin} ===\n")
    
    try:
        supabase = SupabaseService(api_key=settings.supabase_api_key)
        
        # Buscar en ambas tablas
        for table_name in [settings.supabase_table_pip, settings.supabase_table_precia]:
            print(f"\nConsultando tabla: {table_name}")
            try:
                available_columns = supabase._get_available_columns(table_name)
                
                # Buscar columna ISIN
                isin_col = None
                for col in ["ISIN", "isin", "ISIN_CODIGO", "codigo_isin"]:
                    if col in available_columns:
                        isin_col = col
                        break
                
                if not isin_col:
                    print(f"   [ERROR] No se encontró columna ISIN")
                    continue
                
                # Buscar ISINs que empiecen con "COB"
                params = {
                    "select": f"{isin_col}",
                    f"{isin_col}": f"like.COB%",
                    "limit": "20"
                }
                
                response = supabase._make_request("GET", table_name, params=params)
                
                if response:
                    print(f"   [OK] Se encontraron {len(response)} ISINs que empiezan con COB:")
                    isins_found = set()
                    for record in response:
                        isin_value = record.get(isin_col, "")
                        if isin_value:
                            isins_found.add(isin_value)
                    
                    # Mostrar ISINs similares
                    for found_isin in sorted(isins_found):
                        similarity = "EXACTO" if found_isin.upper() == isin.upper() else "SIMILAR"
                        print(f"     - {found_isin} ({similarity})")
                    
                    # Buscar el ISIN exacto (sin importar mayúsculas)
                    print(f"\n   Buscando ISIN exacto (case-insensitive)...")
                    for found_isin in isins_found:
                        if found_isin.upper() == isin.upper():
                            print(f"     [OK] ISIN encontrado: {found_isin}")
                            # Obtener datos completos de este ISIN
                            params_full = {
                                "select": "*",
                                f"{isin_col}": f"eq.{found_isin}",
                                "limit": "1"
                            }
                            full_data = supabase._make_request("GET", table_name, params=params_full)
                            if full_data:
                                print(f"     Datos del registro:")
                                for key in ["ISIN", "isin", "FECHA_VALORACION", "fecha", "PRECIO_LIMPIO", "precio_limpio", "TIR", "tasa"]:
                                    if key in full_data[0]:
                                        print(f"       {key}: {full_data[0][key]}")
                            break
                    else:
                        print(f"     [INFO] No se encontró el ISIN exacto {isin}")
                else:
                    print(f"   [INFO] No se encontraron ISINs que empiecen con COB")
                    
            except Exception as e:
                print(f"   [ERROR] Error consultando {table_name}: {str(e)}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"[ERROR] Error general: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    isin = sys.argv[1] if len(sys.argv) > 1 else "COB07CDOPY71"
    search_similar_isin(isin)

