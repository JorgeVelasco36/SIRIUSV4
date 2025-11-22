#!/usr/bin/env python3
"""
Script para ingesta automática desde MongoDB Atlas
"""
import sys
import argparse
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from database import SessionLocal
from models import Provider
from services.ingestion_service import IngestionService
from services.mongodb_service import MongoDBService


def main():
    parser = argparse.ArgumentParser(
        description="Ingesta automática desde MongoDB Atlas"
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
        help="Fecha de valoración (YYYY-MM-DD). Si no se especifica, usa la más reciente"
    )
    parser.add_argument(
        "--file-id",
        help="ID específico del archivo en MongoDB (opcional)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Número máximo de archivos a procesar (default: 1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo lista archivos sin ingerir"
    )
    
    args = parser.parse_args()
    
    provider = Provider(args.provider)
    
    # Conectar a MongoDB
    mongodb = MongoDBService()
    
    try:
        if args.file_id:
            # Procesar archivo específico
            print(f"Procesando archivo ID: {args.file_id}")
            files = [{"id": args.file_id}]
        else:
            # Listar archivos
            print(f"Buscando archivos en MongoDB Atlas...")
            print(f"Proveedor: {provider.value}")
            
            fecha_filtro = args.fecha if args.fecha else None
            files = mongodb.list_files(
                provider=provider.value,
                fecha_valoracion=fecha_filtro
            )
            
            if not files:
                print("No se encontraron archivos")
                return
            
            # Ordenar por fecha de subida (más recientes primero)
            files = sorted(files, key=lambda x: x.get("upload_date", datetime.min), reverse=True)
            files = files[:args.limit]
        
        print(f"Encontrados {len(files)} archivo(s):")
        for file in files:
            print(f"  - {file.get('name', 'Sin nombre')} (ID: {file.get('id')})")
            if file.get('fecha_valoracion'):
                print(f"    Fecha valoración: {file.get('fecha_valoracion')}")
        
        if args.dry_run:
            print("\nModo dry-run: no se ingirieron archivos")
            return
        
        # Ingerir cada archivo
        db: Session = SessionLocal()
        try:
            ingestion_service = IngestionService(db)
            
            for file in files:
                file_id = file.get('id')
                file_name = file.get('name', 'unknown')
                
                # Usar fecha del archivo si está disponible
                fecha_valoracion = args.fecha
                if not fecha_valoracion and file.get('fecha_valoracion'):
                    fecha_valoracion = file.get('fecha_valoracion')
                
                if fecha_valoracion:
                    fecha_valoracion = datetime.strptime(fecha_valoracion, "%Y-%m-%d").date()
                
                print(f"\nIngiriendo: {file_name}...")
                try:
                    result = ingestion_service.ingest_from_mongodb(
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
            mongodb.close()
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()



