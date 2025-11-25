#!/usr/bin/env python3
"""
Script para autenticación inicial con SharePoint
Abre el navegador para que el usuario inicie sesión
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
    print("AUTENTICACIÓN CON SHAREPOINT")
    print("=" * 60)
    print("\nEste script abrirá tu navegador para que inicies sesión.")
    print("Después de iniciar sesión, el token se guardará para uso futuro.\n")
    
    input("Presiona Enter para continuar...")
    
    try:
        service = SharePointService(use_interactive_auth=True)
        
        print("\nAbriendo navegador para autenticación...")
        token = service.authenticate_interactive()
        
        print("\n✓ Autenticación exitosa!")
        print("✓ Token guardado para uso futuro")
        print("\nAhora puedes usar el asistente para acceder a SharePoint.")
        
    except Exception as e:
        print(f"\n✗ Error en autenticación: {str(e)}")
        print("\nVerifica:")
        print("1. Que las credenciales de Azure estén configuradas en .env")
        print("2. Que tengas acceso a SharePoint")
        print("3. Que la aplicación tenga los permisos necesarios")
        sys.exit(1)


if __name__ == "__main__":
    main()






