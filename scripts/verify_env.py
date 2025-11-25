"""
Script para verificar que el archivo .env tenga las variables necesarias
"""
import sys
import os
from pathlib import Path

def main():
    """Verifica las variables de entorno necesarias"""
    print("=" * 60)
    print("Verificando Configuracion de .env")
    print("=" * 60)
    print()
    
    backend_dir = Path(__file__).parent.parent / "backend"
    env_file = backend_dir / ".env"
    
    if not env_file.exists():
        print("[ERROR] El archivo .env no existe en la carpeta backend")
        print(f"       Ruta esperada: {env_file}")
        print()
        print("SOLUCION:")
        print("1. Copia el archivo env.example a .env:")
        print(f"   cd backend")
        print(f"   copy env.example .env")
        print("2. Edita el archivo .env y configura las variables necesarias")
        return 1
    
    print(f"[OK] Archivo .env encontrado: {env_file}")
    print()
    
    # Leer el archivo .env
    required_vars = {
        "OPENAI_API_KEY": False,
        "SECRET_KEY": False,
        "SUPABASE_URL": False,
        "SUPABASE_API_KEY": False,
    }
    
    optional_vars = {
        "DATABASE_URL": False,
    }
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                # Ignorar comentarios y líneas vacías
                if not line or line.startswith('#'):
                    continue
                
                # Buscar variables
                if '=' in line:
                    key = line.split('=')[0].strip()
                    value = '='.join(line.split('=')[1:]).strip()
                    
                    if key in required_vars:
                        if value and value not in ['', 'tu_openai_api_key', 'tu_api_key_aqui', 'mi-clave-secreta-12345-abcde']:
                            required_vars[key] = True
                            print(f"[OK] {key}: Configurado")
                        else:
                            print(f"[ADVERTENCIA] {key}: No configurado o usa valor por defecto")
                    elif key in optional_vars:
                        optional_vars[key] = True
                        if value:
                            print(f"[OK] {key}: {value[:50]}...")
    
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo .env: {str(e)}")
        return 1
    
    print()
    print("=" * 60)
    print("Resumen de Verificacion")
    print("=" * 60)
    
    all_ok = True
    for var, configured in required_vars.items():
        if configured:
            print(f"[OK] {var}")
        else:
            print(f"[FALTA] {var} - REQUERIDO")
            all_ok = False
    
    if all_ok:
        print()
        print("[OK] Todas las variables requeridas estan configuradas")
        return 0
    else:
        print()
        print("[ERROR] Faltan variables requeridas en .env")
        print()
        print("SOLUCION:")
        print("1. Abre el archivo backend/.env")
        print("2. Configura las siguientes variables:")
        print("   - OPENAI_API_KEY: Obtener en https://platform.openai.com/api-keys")
        print("   - SECRET_KEY: Cualquier texto aleatorio largo")
        print("   - SUPABASE_URL: Ya deberia estar configurado")
        print("   - SUPABASE_API_KEY: Ya deberia estar configurado")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)




