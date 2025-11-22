#!/usr/bin/env python3
"""
Script para inicializar la base de datos
"""
import sys
from pathlib import Path

# Agregar directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import engine, Base
from config import settings


def main():
    print("Inicializando base de datos...")
    print(f"URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'N/A'}")
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✓ Tablas creadas exitosamente")
        print("\nTablas creadas:")
        for table in Base.metadata.tables:
            print(f"  - {table}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()



