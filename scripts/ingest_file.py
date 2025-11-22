#!/usr/bin/env python3
"""
Script para ingesta manual de archivos de valoración
"""
import sys
import os
import argparse
from datetime import datetime, date
from pathlib import Path

# Agregar directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from database import SessionLocal
from models import Provider
from services.ingestion_service import IngestionService


def main():
    parser = argparse.ArgumentParser(
        description="Ingesta manual de archivos de valoración"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Ruta al archivo a ingerir (CSV o Excel)"
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["PIP_LATAM", "PRECIA"],
        help="Proveedor de los datos"
    )
    parser.add_argument(
        "--fecha",
        help="Fecha de valoración (YYYY-MM-DD). Si no se especifica, usa hoy"
    )
    
    args = parser.parse_args()
    
    # Validar que el archivo existe
    if not os.path.exists(args.file):
        print(f"Error: El archivo {args.file} no existe")
        sys.exit(1)
    
    # Parsear fecha
    fecha_valoracion = None
    if args.fecha:
        try:
            fecha_valoracion = datetime.strptime(args.fecha, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Formato de fecha inválido. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        fecha_valoracion = date.today()
    
    # Convertir string a enum
    provider = Provider(args.provider)
    
    # Realizar ingesta
    db: Session = SessionLocal()
    try:
        ingestion_service = IngestionService(db)
        result = ingestion_service.ingest_from_file(
            args.file,
            provider,
            fecha_valoracion
        )
        
        print(f"✓ Ingesta exitosa!")
        print(f"  - Registros procesados: {result['records_processed']}")
        print(f"  - Archivo: {args.file}")
        print(f"  - Proveedor: {provider.value}")
        print(f"  - Fecha valoración: {fecha_valoracion}")
        print(f"  - ID metadata: {result['file_metadata_id']}")
        
    except Exception as e:
        print(f"✗ Error en ingesta: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()



