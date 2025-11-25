#!/usr/bin/env python3
"""
Script para verificar el ISIN exacto en Supabase con diferentes variaciones
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

def verify_isin_exact(isin: str):
    """Verifica el ISIN con diferentes variaciones"""
    print(f"=== Verificando ISIN: {isin} ===\n")
    
    # Variaciones del ISIN a probar
    variations = [
        isin,  # Original
        isin.upper(),  # Mayúsculas
        isin.lower(),  # Minúsculas
        isin.replace("0", "O"),  # Reemplazar 0 por O
        isin.replace("O", "0"),  # Reemplazar O por 0
    ]
    
    try:
        supabase = SupabaseService(api_key=settings.supabase_api_key)
        
        # Buscar en ambas tablas
        for table_name in [settings.supabase_table_pip, settings.supabase_table_precia]:
            print(f"\n{'='*60}")
            print(f"Tabla: {table_name}")
            print(f"{'='*60}")
            
            try:
                available_columns = supabase._get_available_columns(table_name)
                print(f"Columnas disponibles: {len(available_columns)}")
                
                # Buscar columna ISIN
                isin_col = None
                for col in ["ISIN", "isin", "ISIN_CODIGO", "codigo_isin"]:
                    if col in available_columns:
                        isin_col = col
                        print(f"Columna ISIN encontrada: {isin_col}")
                        break
                
                if not isin_col:
                    print("[ERROR] No se encontró columna ISIN")
                    continue
                
                # Probar cada variación
                found = False
                for variation in variations:
                    print(f"\nProbando variación: {variation}")
                    
                    # Método 1: Búsqueda exacta (eq)
                    params_eq = {
                        "select": "*",
                        f"{isin_col}": f"eq.{variation}",
                        "limit": "1"
                    }
                    
                    try:
                        response_eq = supabase._make_request("GET", table_name, params=params_eq)
                        if response_eq and len(response_eq) > 0:
                            print(f"  [OK] Encontrado con búsqueda exacta (eq)")
                            record = response_eq[0]
                            print(f"  ISIN en BD: {record.get(isin_col, 'N/A')}")
                            print(f"  Datos encontrados:")
                            for key in ["ISIN", "isin", "EMISOR", "emisor", "FECHA_VALORACION", "fecha", "TIR", "tasa", "PRECIO_LIMPIO", "precio_limpio"]:
                                if key in record:
                                    print(f"    {key}: {record[key]}")
                            found = True
                            break
                    except Exception as e:
                        print(f"  [ERROR] Error con búsqueda exacta: {str(e)}")
                    
                    # Método 2: Búsqueda con ilike (case-insensitive)
                    # Nota: PostgREST no tiene ilike directo, pero podemos probar con diferentes casos
                    for case_variation in [variation.upper(), variation.lower(), variation]:
                        params_ilike = {
                            "select": "*",
                            f"{isin_col}": f"eq.{case_variation}",
                            "limit": "1"
                        }
                        try:
                            response_ilike = supabase._make_request("GET", table_name, params=params_ilike)
                            if response_ilike and len(response_ilike) > 0:
                                print(f"  [OK] Encontrado con variación de mayúsculas: {case_variation}")
                                record = response_ilike[0]
                                print(f"  ISIN en BD: {record.get(isin_col, 'N/A')}")
                                found = True
                                break
                        except:
                            continue
                    
                    if found:
                        break
                
                if not found:
                    print(f"\n[INFO] No se encontró el ISIN {isin} en {table_name}")
                    print("Buscando ISINs similares...")
                    
                    # Buscar ISINs que contengan parte del ISIN
                    prefix = isin[:8] if len(isin) >= 8 else isin
                    params_similar = {
                        "select": f"{isin_col}",
                        f"{isin_col}": f"like.{prefix}%",
                        "limit": "10"
                    }
                    try:
                        response_similar = supabase._make_request("GET", table_name, params=params_similar)
                        if response_similar:
                            print(f"ISINs similares encontrados ({len(response_similar)}):")
                            for record in response_similar:
                                similar_isin = record.get(isin_col, "")
                                if similar_isin:
                                    print(f"  - {similar_isin}")
                    except Exception as e:
                        print(f"Error buscando similares: {str(e)}")
                        
            except Exception as e:
                print(f"[ERROR] Error consultando {table_name}: {str(e)}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"[ERROR] Error general: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    isin = sys.argv[1] if len(sys.argv) > 1 else "COB07CD0PY71"
    verify_isin_exact(isin)

