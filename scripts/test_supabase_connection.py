"""
Script para validar la conexión a Supabase y verificar las tablas BD_PIP y BD_Precia
"""
import sys
import os
from pathlib import Path

# Cambiar al directorio backend para que pydantic_settings encuentre el .env
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)

# Agregar el directorio backend al path
sys.path.insert(0, str(backend_dir))

from services.supabase_service import SupabaseService
from config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Prueba la conexión a Supabase"""
    print("=" * 60)
    print("Validación de Conexión a Supabase")
    print("=" * 60)
    print()
    
    # Verificar configuración
    if not settings.supabase_api_key:
        print("[ERROR] SUPABASE_API_KEY no esta configurado en .env")
        print()
        print("Por favor, agrega la siguiente linea a tu archivo .env:")
        print("SUPABASE_API_KEY=tu_api_key_aqui")
        return 1
    
    if not settings.supabase_url:
        print("[ADVERTENCIA] SUPABASE_URL no esta configurado, usando URL por defecto")
    
    print(f"[OK] Configuracion de Supabase:")
    print(f"  URL: {settings.supabase_url or 'https://mwyltxcgjxsrdmgsuysv.supabase.co'}")
    print(f"  Tabla PIP: {settings.supabase_table_pip}")
    print(f"  Tabla Precia: {settings.supabase_table_precia}")
    print()
    
    try:
        # Crear servicio
        print("Conectando a Supabase API...")
        supabase = SupabaseService()
        
        # Probar conexión
        print("Probando conexion...")
        result = supabase.test_connection()
        
        print()
        if result["success"]:
            print("[OK] CONEXION EXITOSA")
            print()
            print("Estado de las tablas:")
            for table_name, exists in result["tables"].items():
                status = "[OK] Existe" if exists else "[ERROR] No existe"
                print(f"  {table_name}: {status}")
            
            if result["all_tables_exist"]:
                print()
                print("[OK] Todas las tablas estan disponibles")
                
                # Listar algunos archivos de ejemplo
                print()
                print("Listando archivos disponibles...")
                try:
                    files_pip = supabase.list_files("PIP_LATAM")
                    files_precia = supabase.list_files("PRECIA")
                    
                    if files_pip:
                        print(f"\n  Archivos en BD_PIP: {len(files_pip)}")
                        for f in files_pip[:5]:  # Mostrar solo los primeros 5
                            print(f"    - {f['name']} ({f['record_count']} registros)")
                    
                    if files_precia:
                        print(f"\n  Archivos en BD_Precia: {len(files_precia)}")
                        for f in files_precia[:5]:  # Mostrar solo los primeros 5
                            print(f"    - {f['name']} ({f['record_count']} registros)")
                except Exception as e:
                    print(f"  [ADVERTENCIA] No se pudieron listar archivos: {str(e)}")
            else:
                print()
                print("[ADVERTENCIA] Algunas tablas no existen")
                print("   Asegurate de que las tablas BD_PIP y BD_Precia existan en Supabase")
            
            supabase.close()
            return 0
        else:
            print("[ERROR] ERROR DE CONEXION")
            print(f"   {result['message']}")
            supabase.close()
            return 1
            
    except ValueError as e:
        print(f"[ERROR] ERROR DE CONFIGURACION: {str(e)}")
        return 1
    except Exception as e:
        print(f"[ERROR] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

