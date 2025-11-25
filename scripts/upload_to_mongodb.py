#!/usr/bin/env python3
"""
Script para subir archivos a MongoDB Atlas
"""
import sys
import argparse
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.mongodb_service import MongoDBService
from models import Provider


def main():
    parser = argparse.ArgumentParser(
        description="Subir archivo a MongoDB Atlas"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Ruta al archivo a subir (CSV o Excel)"
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
    if not Path(args.file).exists():
        print(f"Error: El archivo {args.file} no existe")
        sys.exit(1)
    
    # Parsear fecha
    fecha_valoracion = date.today().isoformat()
    if args.fecha:
        try:
            fecha_valoracion = date.fromisoformat(args.fecha).isoformat()
        except ValueError:
            print(f"Error: Formato de fecha inválido. Use YYYY-MM-DD")
            sys.exit(1)
    
    provider = Provider(args.provider)
    
    # Subir archivo
    mongodb = MongoDBService()
    try:
        # Leer archivo
        with open(args.file, 'rb') as f:
            file_content = f.read()
        
        file_name = Path(args.file).name
        
        print(f"Subiendo archivo a MongoDB Atlas...")
        print(f"  Archivo: {file_name}")
        print(f"  Proveedor: {provider.value}")
        print(f"  Fecha valoración: {fecha_valoracion}")
        
        file_id = mongodb.upload_file(
            file_content=file_content,
            file_name=file_name,
            provider=provider.value,
            fecha_valoracion=fecha_valoracion
        )
        
        print(f"\n✓ Archivo subido exitosamente!")
        print(f"  ID en MongoDB: {file_id}")
        print(f"\nPara ingerir este archivo, ejecuta:")
        print(f"  python scripts/ingest_mongodb.py --provider {provider.value} --file-id {file_id}")
        
    except Exception as e:
        print(f"✗ Error subiendo archivo: {str(e)}")
        sys.exit(1)
    finally:
        mongodb.close()


if __name__ == "__main__":
    main()






