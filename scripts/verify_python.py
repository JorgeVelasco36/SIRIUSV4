#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de verificación de instalación de Python para S.I.R.I.U.S V4
"""
import sys
import subprocess
from pathlib import Path
import io

# Configurar salida UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_python_version():
    """Verifica que Python sea 3.10+"""
    print("=" * 60)
    print("VERIFICACIÓN DE INSTALACIÓN DE PYTHON")
    print("=" * 60)
    
    version = sys.version_info
    print(f"\n✓ Python {version.major}.{version.minor}.{version.micro} detectado")
    print(f"  Ubicación: {sys.executable}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"\n✗ ERROR: Se requiere Python 3.10 o superior")
        print(f"  Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✓ Versión compatible (3.10+)")
        return True

def check_pip():
    """Verifica que pip esté disponible"""
    print("\n" + "-" * 60)
    print("VERIFICANDO PIP...")
    print("-" * 60)
    
    try:
        import pip
        print(f"✓ pip disponible: versión {pip.__version__}")
        return True
    except ImportError:
        print("✗ ERROR: pip no está disponible")
        return False

def check_backend_structure():
    """Verifica que la estructura del backend esté presente"""
    print("\n" + "-" * 60)
    print("VERIFICANDO ESTRUCTURA DEL BACKEND...")
    print("-" * 60)
    
    backend_path = Path(__file__).parent.parent / "backend"
    
    required_files = [
        "main.py",
        "config.py",
        "database.py",
        "models.py",
        "schemas.py",
        "requirements.txt"
    ]
    
    all_present = True
    for file in required_files:
        file_path = backend_path / file
        if file_path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - NO ENCONTRADO")
            all_present = False
    
    return all_present

def check_dependencies():
    """Verifica si las dependencias están instaladas"""
    print("\n" + "-" * 60)
    print("VERIFICANDO DEPENDENCIAS...")
    print("-" * 60)
    
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "pandas",
        "openai",
        "pydantic"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} instalado")
        except ImportError:
            print(f"✗ {package} NO instalado")
            missing.append(package)
    
    if missing:
        print(f"\n⚠ ADVERTENCIA: Faltan {len(missing)} paquetes")
        print("  Ejecuta: pip install -r backend/requirements.txt")
        return False
    else:
        print("\n✓ Todas las dependencias principales están instaladas")
        return True

def check_project_imports():
    """Intenta importar módulos del proyecto"""
    print("\n" + "-" * 60)
    print("VERIFICANDO MÓDULOS DEL PROYECTO...")
    print("-" * 60)
    
    backend_path = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    modules_to_check = [
        ("config", "config"),
        ("database", "database"),
        ("models", "models"),
    ]
    
    all_ok = True
    for module_name, display_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {display_name}.py se puede importar")
        except Exception as e:
            print(f"✗ {display_name}.py - Error: {str(e)[:50]}")
            all_ok = False
    
    return all_ok

def main():
    """Ejecuta todas las verificaciones"""
    results = []
    
    results.append(("Versión de Python", check_python_version()))
    results.append(("Pip", check_pip()))
    results.append(("Estructura del Backend", check_backend_structure()))
    results.append(("Dependencias", check_dependencies()))
    results.append(("Módulos del Proyecto", check_project_imports()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ TODAS LAS VERIFICACIONES PASARON")
        print("\nPython está correctamente instalado y configurado para S.I.R.I.U.S V4")
    else:
        print("⚠ ALGUNAS VERIFICACIONES FALLARON")
        print("\nRevisa los errores arriba y corrige los problemas antes de continuar")
        print("\nPróximos pasos sugeridos:")
        print("1. Instalar dependencias: pip install -r backend/requirements.txt")
        print("2. Configurar variables de entorno: copiar backend/.env.example a backend/.env")
        print("3. Inicializar base de datos: python scripts/init_db.py")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

