"""
Servicio para integración con Microsoft Graph API (SharePoint)
Soporta autenticación interactiva de usuario
"""
import httpx
from msal import PublicClientApplication, ConfidentialClientApplication
from typing import Optional, List
from config import settings
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class SharePointService:
    """Servicio para interactuar con SharePoint a través de Microsoft Graph API"""
    
    def __init__(self, use_interactive_auth: bool = True):
        """
        Inicializa el servicio de SharePoint
        
        Args:
            use_interactive_auth: Si True, usa autenticación interactiva (usuario/contraseña)
                                 Si False, usa client credentials (aplicación)
        """
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        self.tenant_id = settings.azure_tenant_id
        self.site_id = settings.sharepoint_site_id
        self.drive_id = settings.sharepoint_drive_id
        self.use_interactive_auth = use_interactive_auth
        
        # Configurar según el tipo de autenticación
        if use_interactive_auth and not self.client_secret:
            # Autenticación interactiva (usuario)
            self.app = PublicClientApplication(
                client_id=self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            self.scopes = ["https://graph.microsoft.com/Files.Read.All", 
                          "https://graph.microsoft.com/Sites.Read.All"]
        else:
            # Autenticación de aplicación (client credentials)
            self.app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            self.scopes = ["https://graph.microsoft.com/.default"]
        
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.token_cache_file = Path("sharepoint_token_cache.json")
    
    def _load_token_cache(self):
        """Carga el caché de tokens desde archivo"""
        if self.token_cache_file.exists():
            try:
                with open(self.token_cache_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def _save_token_cache(self, cache):
        """Guarda el caché de tokens en archivo"""
        try:
            with open(self.token_cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            logger.warning(f"No se pudo guardar el caché de tokens: {str(e)}")
    
    def authenticate_interactive(self) -> str:
        """
        Autenticación interactiva - abre el navegador para que el usuario inicie sesión
        
        Returns:
            Token de acceso
        """
        try:
            # Cargar caché si existe
            cache = self._load_token_cache()
            if cache:
                self.app.token_cache.deserialize(json.dumps(cache))
            
            # Intentar obtener token del caché
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(
                    scopes=self.scopes,
                    account=accounts[0]
                )
                if result and "access_token" in result:
                    self._save_token_cache(self.app.token_cache.serialize())
                    return result["access_token"]
            
            # Si no hay token en caché, autenticación interactiva
            result = self.app.acquire_token_interactive(
                scopes=self.scopes
            )
            
            if "access_token" in result:
                self._save_token_cache(self.app.token_cache.serialize())
                return result["access_token"]
            else:
                error = result.get("error_description", "Unknown error")
                logger.error(f"Error en autenticación interactiva: {error}")
                raise Exception(f"Error de autenticación: {error}")
                
        except Exception as e:
            logger.error(f"Excepción en autenticación interactiva: {str(e)}")
            raise
    
    def get_access_token(self) -> str:
        """Obtiene token de acceso para Microsoft Graph API"""
        try:
            if self.use_interactive_auth and not self.client_secret:
                # Autenticación interactiva
                return self.authenticate_interactive()
            else:
                # Autenticación de aplicación (client credentials)
                result = self.app.acquire_token_for_client(scopes=self.scopes)
                
                if "access_token" in result:
                    return result["access_token"]
                else:
                    error = result.get("error_description", "Unknown error")
                    logger.error(f"Error obteniendo token: {error}")
                    raise Exception(f"Error de autenticación: {error}")
        except Exception as e:
            logger.error(f"Excepción al obtener token: {str(e)}")
            raise
    
    def _get_headers(self) -> dict:
        """Obtiene headers con token de autenticación"""
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def list_files_in_folder(self, folder_id: str, file_extension: Optional[str] = None, site_id: Optional[str] = None) -> List[dict]:
        """
        Lista archivos en una carpeta específica de SharePoint usando el ID de la carpeta
        
        Args:
            folder_id: ID de la carpeta en SharePoint
            file_extension: Extensión de archivo a filtrar (ej: "xlsx", "csv")
            site_id: ID del sitio (opcional, usa self.site_id si no se proporciona)
        
        Returns:
            Lista de archivos con metadatos
        """
        try:
            headers = self._get_headers()
            site = site_id or self.site_id
            
            # Usar el ID de la carpeta directamente
            url = f"{self.graph_endpoint}/sites/{site}/drive/items/{folder_id}/children"
            
            response = httpx.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            files = response.json().get("value", [])
            
            # Filtrar por extensión si se especifica
            if file_extension:
                files = [
                    f for f in files 
                    if f.get("name", "").lower().endswith(f".{file_extension.lower()}")
                ]
            
            return files
        except Exception as e:
            logger.error(f"Error listando archivos en carpeta {folder_id}: {str(e)}")
            raise
    
    def list_files(self, folder_path: str = "", file_extension: Optional[str] = None) -> List[dict]:
        """
        Lista archivos en SharePoint
        
        Args:
            folder_path: Ruta de la carpeta (ej: "Valoraciones/2025")
            file_extension: Extensión de archivo a filtrar (ej: "xlsx", "csv")
        
        Returns:
            Lista de archivos con metadatos
        """
        try:
            headers = self._get_headers()
            
            # Construir URL
            if self.drive_id:
                base_url = f"{self.graph_endpoint}/sites/{self.site_id}/drives/{self.drive_id}"
            else:
                base_url = f"{self.graph_endpoint}/sites/{self.site_id}/drive"
            
            if folder_path:
                url = f"{base_url}/root:/{folder_path}:/children"
            else:
                url = f"{base_url}/root/children"
            
            response = httpx.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            files = response.json().get("value", [])
            
            # Filtrar por extensión si se especifica
            if file_extension:
                files = [
                    f for f in files 
                    if f.get("name", "").lower().endswith(f".{file_extension.lower()}")
                ]
            
            return files
        except Exception as e:
            logger.error(f"Error listando archivos: {str(e)}")
            raise
    
    def download_file(self, file_id: str) -> bytes:
        """
        Descarga un archivo de SharePoint
        
        Args:
            file_id: ID del archivo en SharePoint
        
        Returns:
            Contenido del archivo en bytes
        """
        try:
            headers = self._get_headers()
            
            url = f"{self.graph_endpoint}/sites/{self.site_id}/drive/items/{file_id}/content"
            
            response = httpx.get(url, headers=headers, timeout=60.0)
            response.raise_for_status()
            
            return response.content
        except Exception as e:
            logger.error(f"Error descargando archivo {file_id}: {str(e)}")
            raise
    
    def get_file_by_name(self, file_name: str, folder_path: str = "") -> Optional[dict]:
        """
        Busca un archivo por nombre
        
        Args:
            file_name: Nombre del archivo
            folder_path: Ruta de la carpeta
        
        Returns:
            Metadatos del archivo o None si no se encuentra
        """
        try:
            files = self.list_files(folder_path=folder_path)
            
            for file in files:
                if file.get("name") == file_name:
                    return file
            
            return None
        except Exception as e:
            logger.error(f"Error buscando archivo {file_name}: {str(e)}")
            raise
