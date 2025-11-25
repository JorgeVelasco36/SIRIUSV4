#!/usr/bin/env python3
"""
Script para inicializar la base de datos
"""
import sys
import os
from pathlib import Path

# Cambiar al directorio backend para que pydantic_settings encuentre el .env
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)

# Agregar directorio backend al path
sys.path.insert(0, str(backend_dir))

from database import engine, Base
from config import settings
# Importar modelos para que se registren en Base.metadata
from models import Valuation, FileMetadata, QueryLog


def main():
    print("Inicializando base de datos...")
    db_info = settings.database_url.split('@')[1] if '@' in settings.database_url else settings.database_url
    print(f"URL: {db_info}")
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("[OK] Tablas creadas exitosamente")
        print("\nTablas creadas:")
        table_names = list(Base.metadata.tables.keys())
        if table_names:
            for table in table_names:
                print(f"  - {table}")
        else:
            print("  (No se encontraron tablas - verifica que los modelos esten importados)")
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()



