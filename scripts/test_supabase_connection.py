"""
Script para validar la conexión a Supabase y verificar las tablas BD_PIP y BD_Precia
"""
import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

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
    if not settings.supabase_db_url:
        print("❌ ERROR: SUPABASE_DB_URL no está configurado en .env")
        print()
        print("Por favor, agrega la siguiente línea a tu archivo .env:")
        print("SUPABASE_DB_URL=postgresql://postgres:[YOUR_PASSWORD]@db.mwyltxcgjxsrdmgsuysv.supabase.co:5432/postgres")
        return 1
    
    print(f"✓ URL de Supabase configurada")
    print(f"  Base de datos: {settings.supabase_db_name}")
    print(f"  Tabla PIP: {settings.supabase_table_pip}")
    print(f"  Tabla Precia: {settings.supabase_table_precia}")
    print()
    
    try:
        # Crear servicio
        print("Conectando a Supabase...")
        supabase = SupabaseService()
        
        # Probar conexión
        print("Probando conexión...")
        result = supabase.test_connection()
        
        print()
        if result["success"]:
            print("✅ CONEXIÓN EXITOSA")
            print()
            print("Estado de las tablas:")
            for table_name, exists in result["tables"].items():
                status = "✅ Existe" if exists else "❌ No existe"
                print(f"  {table_name}: {status}")
            
            if result["all_tables_exist"]:
                print()
                print("✅ Todas las tablas están disponibles")
                
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
                    print(f"  ⚠️  No se pudieron listar archivos: {str(e)}")
            else:
                print()
                print("⚠️  ADVERTENCIA: Algunas tablas no existen")
                print("   Asegúrate de que las tablas BD_PIP y BD_Precia existan en Supabase")
            
            supabase.close()
            return 0
        else:
            print("❌ ERROR DE CONEXIÓN")
            print(f"   {result['message']}")
            supabase.close()
            return 1
            
    except ValueError as e:
        print(f"❌ ERROR DE CONFIGURACIÓN: {str(e)}")
        return 1
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

