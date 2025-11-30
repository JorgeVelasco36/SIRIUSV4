#!/usr/bin/env python3
"""
Script para explorar carpetas de SharePoint y obtener IDs
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.sharepoint_service import SharePointService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("EXPLORADOR DE SHAREPOINT")
    print("=" * 60)
    
    # ID de la carpeta principal del enlace proporcionado
    main_folder_id = "IgCINeOLvbBpTZz4ukbBVs5VAc2a27LW1rBOdCkZZNRn9zg"
    
    try:
        service = SharePointService(use_interactive_auth=True)
        
        print(f"\nExplorando carpeta principal (ID: {main_folder_id})...")
        print("-" * 60)
        
        items = service.list_files_in_folder(main_folder_id)
        
        if not items:
            print("No se encontraron elementos en esta carpeta.")
            return
        
        print(f"\nEncontrados {len(items)} elementos:\n")
        
        for item in items:
            item_type = "📁 CARPETA" if "folder" in item.get("mimeType", "").lower() or "folder" in item else "📄 ARCHIVO"
            name = item.get("name", "Sin nombre")
            item_id = item.get("id", "Sin ID")
            size = item.get("size", 0)
            
            if item_type == "📁 CARPETA":
                print(f"{item_type}: {name}")
                print(f"   ID: {item_id}")
                print()
            else:
                size_mb = size / (1024 * 1024) if size > 0 else 0
                print(f"{item_type}: {name}")
                print(f"   ID: {item_id}")
                print(f"   Tamaño: {size_mb:.2f} MB" if size_mb > 0 else "   Tamaño: N/A")
                print()
        
        # Buscar carpetas específicas
        print("\n" + "=" * 60)
        print("BUSCANDO CARPETAS ESPECÍFICAS")
        print("=" * 60)
        
        precia_folder = None
        pip_folder = None
        
        for item in items:
            name = item.get("name", "").upper()
            if "PRECIA" in name:
                precia_folder = item
            elif "PIP" in name or "LATAM" in name:
                pip_folder = item
        
        if precia_folder:
            print(f"\n✓ Carpeta PRECIA encontrada:")
            print(f"   Nombre: {precia_folder.get('name')}")
            print(f"   ID: {precia_folder.get('id')}")
        
        if pip_folder:
            print(f"\n✓ Carpeta PIP LATAM encontrada:")
            print(f"   Nombre: {pip_folder.get('name')}")
            print(f"   ID: {pip_folder.get('id')}")
        
        if not precia_folder and not pip_folder:
            print("\n⚠ No se encontraron las carpetas 'Precia' o 'PIP Latam'")
            print("   Revisa los nombres de las carpetas en SharePoint")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nVerifica:")
        print("1. Que hayas ejecutado sharepoint_auth.py primero")
        print("2. Que las credenciales estén correctas en .env")
        print("3. Que tengas acceso a SharePoint")
        sys.exit(1)


if __name__ == "__main__":
    main()








