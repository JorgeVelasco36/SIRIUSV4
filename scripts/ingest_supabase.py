#!/usr/bin/env python3
"""
Script para ingesta automática desde Supabase PostgreSQL
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
from services.supabase_service import SupabaseService


def main():
    parser = argparse.ArgumentParser(
        description="Ingesta automática desde Supabase PostgreSQL"
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["PIP_LATAM", "PRECIA"],
        help="Proveedor de los datos"
    )
    parser.add_argument(
        "--fecha",
        help="Fecha de valoración (YYYY-MM-DD). Si no se especifica, usa la más reciente"
    )
    parser.add_argument(
        "--file-name",
        help="Nombre específico del archivo en Supabase (opcional)"
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
    
    # Conectar a Supabase
    supabase = SupabaseService()
    
    try:
        if args.file_name:
            # Procesar archivo específico
            print(f"Procesando archivo: {args.file_name}")
            files = [{"name": args.file_name}]
        else:
            # Listar archivos
            print(f"Buscando archivos en Supabase...")
            print(f"Proveedor: {provider.value}")
            
            fecha_filtro = args.fecha if args.fecha else None
            files = supabase.list_files(
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
            print(f"  - {file.get('name', 'Sin nombre')}")
            if file.get('fecha_valoracion'):
                print(f"    Fecha valoración: {file.get('fecha_valoracion')}")
            if file.get('record_count'):
                print(f"    Registros: {file.get('record_count')}")
        
        if args.dry_run:
            print("\nModo dry-run: no se ingirieron archivos")
            return
        
        # Ingerir cada archivo
        db: Session = SessionLocal()
        try:
            ingestion_service = IngestionService(db)
            
            for file in files:
                file_name = file.get('name')
                
                # Usar fecha del archivo si está disponible
                fecha_valoracion = args.fecha
                if not fecha_valoracion and file.get('fecha_valoracion'):
                    fecha_valoracion = file.get('fecha_valoracion')
                
                if fecha_valoracion:
                    fecha_valoracion = datetime.strptime(fecha_valoracion, "%Y-%m-%d").date()
                
                print(f"\nIngiriendo: {file_name}...")
                try:
                    result = ingestion_service.ingest_from_supabase(
                        file_name,
                        provider,
                        fecha_valoracion
                    )
                    print(f"✓ {file_name}: {result['records_processed']} registros")
                except Exception as e:
                    print(f"✗ Error con {file_name}: {str(e)}")
                    continue
            
        finally:
            db.close()
            supabase.close()
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

