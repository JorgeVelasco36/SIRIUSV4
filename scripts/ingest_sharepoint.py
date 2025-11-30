#!/usr/bin/env python3
"""
Script para ingesta automática desde SharePoint
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
from services.sharepoint_service import SharePointService


def main():
    parser = argparse.ArgumentParser(
        description="Ingesta automática desde SharePoint"
    )
    parser.add_argument(
        "--folder",
        default="",
        help="Carpeta en SharePoint (ej: 'Valoraciones/2025')"
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["PIP_LATAM", "PRECIA"],
        help="Proveedor de los datos"
    )
    parser.add_argument(
        "--file-extension",
        default="xlsx",
        choices=["xlsx", "xls", "csv"],
        help="Extensión de archivo a buscar"
    )
    parser.add_argument(
        "--fecha",
        help="Fecha de valoración (YYYY-MM-DD). Si no se especifica, intenta extraer del nombre del archivo"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo lista archivos sin ingerir"
    )
    
    args = parser.parse_args()
    
    provider = Provider(args.provider)
    
    # Conectar a SharePoint
    sharepoint = SharePointService()
    
    try:
        # Listar archivos
        print(f"Buscando archivos en SharePoint...")
        files = sharepoint.list_files(
            folder_path=args.folder,
            file_extension=args.file_extension
        )
        
        if not files:
            print("No se encontraron archivos")
            return
        
        print(f"Encontrados {len(files)} archivo(s):")
        for file in files:
            print(f"  - {file.get('name')} (ID: {file.get('id')})")
        
        if args.dry_run:
            print("\nModo dry-run: no se ingirieron archivos")
            return
        
        # Ingerir cada archivo
        db: Session = SessionLocal()
        try:
            ingestion_service = IngestionService(db)
            
            for file in files:
                file_id = file.get('id')
                file_name = file.get('name')
                
                # Intentar extraer fecha del nombre del archivo
                fecha_valoracion = args.fecha
                if not fecha_valoracion:
                    # Lógica simple: buscar patrón de fecha en el nombre
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file_name)
                    if date_match:
                        fecha_valoracion = date_match.group(1)
                    else:
                        fecha_valoracion = date.today().isoformat()
                
                fecha_valoracion = datetime.strptime(fecha_valoracion, "%Y-%m-%d").date()
                
                print(f"\nIngiriendo: {file_name}...")
                try:
                    result = ingestion_service.ingest_from_sharepoint(
                        file_id,
                        provider,
                        fecha_valoracion
                    )
                    print(f"✓ {file_name}: {result['records_processed']} registros")
                except Exception as e:
                    print(f"✗ Error con {file_name}: {str(e)}")
                    continue
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()








