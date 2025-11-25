"""
Servicio para integración con Supabase usando API REST
Lee archivos de valoración almacenados en las tablas BD_PIP y BD_Precia
"""
import httpx
from typing import Optional, List, Dict
from config import settings
import logging
import pandas as pd
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SupabaseService:
    """Servicio para interactuar con Supabase usando API REST"""
    
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        """
        Inicializa la conexión con Supabase usando API REST
        
        Args:
            api_key: API Key de Supabase (anon key) - opcional
            access_token: Access token JWT obtenido de autenticación con correo/contraseña - opcional
        """
        self.table_pip = settings.supabase_table_pip
        self.table_precia = settings.supabase_table_precia
        
        # Obtener URL del proyecto
        self.base_url = settings.supabase_url
        if not self.base_url:
            # Si no está configurada, construir desde el ref del token
            # Del token JWT podemos extraer el ref: mwyltxcgjxsrdmgsuysv
            self.base_url = "https://mwyltxcgjxsrdmgsuysv.supabase.co"
        
        # Asegurar que la URL no termine con /
        self.base_url = self.base_url.rstrip('/')
        self.api_url = f"{self.base_url}/rest/v1"
        self.auth_url = f"{self.base_url}/auth/v1"
        
        # Determinar qué tipo de autenticación usar
        if access_token:
            # Usar access token de autenticación con correo/contraseña
            self.api_key = settings.supabase_api_key  # Necesitamos el anon key para apikey header
            self.access_token = access_token
            auth_header = f"Bearer {access_token}"
        elif api_key:
            # Usar API Key directamente
            self.api_key = api_key
            self.access_token = None
            auth_header = f"Bearer {api_key}"
        else:
            # Usar API Key del .env
            self.api_key = settings.supabase_api_key
            self.access_token = None
            auth_header = f"Bearer {self.api_key}"
        
        if not self.api_key:
            raise ValueError("SUPABASE_API_KEY no está configurado en .env")
        
        # Configurar headers para todas las peticiones
        self.headers = {
            "apikey": self.api_key,
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        logger.info(f"Conectado a Supabase API: {self.base_url}")
    
    @staticmethod
    def authenticate_with_email_password(email: str, password: str, base_url: Optional[str] = None) -> Dict:
        """
        Autentica con Supabase usando correo y contraseña
        
        Args:
            email: Correo electrónico del usuario
            password: Contraseña del usuario
            base_url: URL del proyecto Supabase (opcional, usa settings si no se proporciona)
        
        Returns:
            Diccionario con access_token y otros datos de la sesión
        """
        if not base_url:
            base_url = settings.supabase_url or "https://mwyltxcgjxsrdmgsuysv.supabase.co"
        
        base_url = base_url.rstrip('/')
        auth_url = f"{base_url}/auth/v1/token?grant_type=password"
        
        # Necesitamos el anon key para autenticación
        anon_key = settings.supabase_api_key
        if not anon_key:
            raise ValueError("SUPABASE_API_KEY no está configurado en .env")
        
        headers = {
            "apikey": anon_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "email": email,
            "password": password
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(auth_url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "access_token": result.get("access_token"),
                    "refresh_token": result.get("refresh_token"),
                    "expires_in": result.get("expires_in"),
                    "user": result.get("user")
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"Error de autenticación: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 400:
                error_data = e.response.json() if e.response.content else {}
                error_msg = error_data.get("error_description", "Credenciales inválidas")
                raise Exception(f"Error de autenticación: {error_msg}")
            raise Exception(f"Error de autenticación: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error en autenticación: {str(e)}")
            raise
    
    def get_table_name(self, provider: str) -> str:
        """Obtiene el nombre de la tabla según el proveedor"""
        provider_upper = provider.upper()
        if provider_upper == "PIP_LATAM" or provider_upper == "PIP":
            return self.table_pip
        elif provider_upper == "PRECIA":
            return self.table_precia
        else:
            raise ValueError(f"Proveedor no reconocido: {provider}")
    
    def _make_request(self, method: str, table: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict:
        """
        Realiza una petición HTTP a la API REST de Supabase
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            table: Nombre de la tabla
            params: Parámetros de consulta
            data: Datos para POST/PATCH
        
        Returns:
            Respuesta de la API como diccionario
        """
        url = f"{self.api_url}/{table}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                if method == "GET":
                    response = client.get(url, headers=self.headers, params=params)
                elif method == "POST":
                    response = client.post(url, headers=self.headers, json=data, params=params)
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")
                
                response.raise_for_status()
                return response.json() if response.content else {}
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP {e.response.status_code}: {e.response.text}")
            raise Exception(f"Error en petición a Supabase: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error en petición a Supabase: {str(e)}")
            raise
    
    def _get_available_columns(self, table_name: str) -> List[str]:
        """
        Detecta las columnas disponibles en una tabla
        Intenta hacer una consulta con select=* y devuelve las claves del primer registro
        """
        try:
            params = {"select": "*", "limit": "1"}
            data = self._make_request("GET", table_name, params=params)
            if isinstance(data, list) and len(data) > 0:
                return list(data[0].keys())
            return []
        except Exception as e:
            logger.warning(f"No se pudieron detectar columnas en {table_name}: {str(e)}")
            return []
    
    def list_files(self, provider: Optional[str] = None, 
                   fecha_valoracion: Optional[str] = None) -> List[Dict]:
        """
        Lista archivos disponibles en Supabase
        
        Args:
            provider: Filtrar por proveedor (PIP_LATAM, PRECIA)
            fecha_valoracion: Filtrar por fecha (formato: YYYY-MM-DD)
        
        Returns:
            Lista de archivos con metadatos
        """
        try:
            files = []
            tables_to_query = []
            
            if provider:
                tables_to_query = [self.get_table_name(provider)]
            else:
                tables_to_query = [self.table_pip, self.table_precia]
            
            for table_name in tables_to_query:
                # Detectar columnas disponibles
                available_columns = self._get_available_columns(table_name)
                
                # Mapear nombres de columnas esperados a posibles variaciones
                # Incluye variaciones en mayúsculas/minúsculas y nombres alternativos
                column_mapping = {
                    "archivo_origen": ["TIPO_ARCHIVO", "tipo_archivo", "archivo_origen", "archivo", "file_name", "nombre_archivo"],
                    "proveedor": ["FUENTE", "fuente", "proveedor", "provider", "PROVEEDOR"],
                    "fecha": ["FECHA_VALORACION", "fecha_valoracion", "fecha", "date", "valuation_date", "FECHA"],
                    "timestamp_ingesta": ["created_at", "CREATED_AT", "timestamp_ingesta", "timestamp", "upload_date", "fecha_ingesta"]
                }
                
                # Encontrar las columnas reales disponibles
                selected_columns = []
                for expected_col, variations in column_mapping.items():
                    found = False
                    for variation in variations:
                        if variation in available_columns:
                            selected_columns.append(variation)
                            found = True
                            break
                    if not found:
                        logger.warning(f"Columna {expected_col} no encontrada en {table_name}. Columnas disponibles: {available_columns}")
                
                # Si no encontramos las columnas necesarias, usar select=*
                if len(selected_columns) < 2:
                    logger.warning(f"Usando select=* para {table_name} porque no se encontraron las columnas esperadas")
                    params = {"select": "*", "limit": "1000"}
                else:
                    # Construir parámetros de consulta (sintaxis PostgREST)
                    params = {
                        "select": ",".join(selected_columns),
                        "limit": "1000"
                    }
                    
                    # Intentar ordenar por timestamp si está disponible
                    timestamp_col = None
                    for col in ["created_at", "CREATED_AT", "timestamp_ingesta", "timestamp", "upload_date"]:
                        if col in available_columns:
                            timestamp_col = col
                            break
                    if timestamp_col:
                        params["order"] = f"{timestamp_col}.desc"
                
                if fecha_valoracion:
                    # Intentar filtrar por fecha
                    fecha_col = None
                    for col in ["FECHA_VALORACION", "fecha_valoracion", "fecha", "date", "valuation_date", "FECHA"]:
                        if col in available_columns:
                            fecha_col = col
                            break
                    if fecha_col:
                        params[fecha_col] = f"eq.{fecha_valoracion}"
                
                # Obtener datos
                try:
                    data = self._make_request("GET", table_name, params=params)
                except Exception as e:
                    error_msg = str(e)
                    if "does not exist" in error_msg or "column" in error_msg.lower():
                        logger.error(f"Error: Las columnas necesarias no existen en {table_name}. "
                                   f"Ejecuta el script SQL en scripts/create_supabase_columns.sql para crear las columnas.")
                        raise Exception(f"Columnas faltantes en {table_name}. Ver logs para más detalles.")
                    raise
                
                if isinstance(data, list):
                    # Agrupar por archivo_origen (o la columna equivalente)
                    file_groups = {}
                    archivo_col = None
                    proveedor_col = None
                    fecha_col = None
                    timestamp_col = None
                    
                    # Encontrar las columnas reales en los datos
                    if len(data) > 0:
                        row_keys = list(data[0].keys())
                        for key in row_keys:
                            key_lower = key.lower()
                            key_upper = key.upper()
                            # Mapeo de archivo_origen
                            if key_upper == "TIPO_ARCHIVO" or "archivo" in key_lower or "file" in key_lower:
                                archivo_col = key
                            # Mapeo de proveedor
                            if key_upper == "FUENTE" or "proveedor" in key_lower or "provider" in key_lower:
                                proveedor_col = key
                            # Mapeo de fecha
                            if key_upper == "FECHA_VALORACION" or key_lower in ["fecha", "fecha_valoracion", "date", "valuation_date"]:
                                fecha_col = key
                            # Mapeo de timestamp
                            if key_upper == "CREATED_AT" or "timestamp" in key_lower or "created_at" in key_lower or "upload" in key_lower:
                                timestamp_col = key
                    
                    for row in data:
                        file_name = row.get(archivo_col) if archivo_col else row.get("archivo_origen", "N/A")
                        if file_name and file_name != "N/A":
                            if file_name not in file_groups:
                                file_groups[file_name] = {
                                    "name": file_name,
                                    "provider": row.get(proveedor_col) if proveedor_col else row.get("proveedor"),
                                    "fecha_valoracion": str(row.get(fecha_col)) if fecha_col and row.get(fecha_col) else None,
                                    "upload_date": row.get(timestamp_col) if timestamp_col else row.get("timestamp_ingesta"),
                                    "record_count": 0
                                }
                            file_groups[file_name]["record_count"] += 1
                    
                    files.extend(list(file_groups.values()))
            
            # Ordenar por fecha de subida (más recientes primero)
            files.sort(key=lambda x: x.get("upload_date") or datetime.min, reverse=True)
            
            return files
        except Exception as e:
            logger.error(f"Error listando archivos: {str(e)}")
            raise
    
    def get_data_by_file(self, file_name: str, provider: str) -> pd.DataFrame:
        """
        Obtiene datos de un archivo específico desde Supabase
        
        Args:
            file_name: Nombre del archivo
            provider: Proveedor (PIP_LATAM, PRECIA)
        
        Returns:
            DataFrame con los datos
        """
        try:
            table_name = self.get_table_name(provider)
            
            # Detectar columnas disponibles
            available_columns = self._get_available_columns(table_name)
            
            # Encontrar la columna de archivo_origen
            archivo_col = None
            for col in ["TIPO_ARCHIVO", "tipo_archivo", "archivo_origen", "archivo", "file_name", "nombre_archivo"]:
                if col in available_columns:
                    archivo_col = col
                    break
            
            if not archivo_col:
                # Si no encontramos la columna, intentar con el nombre esperado
                archivo_col = "TIPO_ARCHIVO"  # Intentar con el nombre real primero
                logger.warning(f"Columna archivo_origen no detectada, intentando con {archivo_col}")
            
            # Construir parámetros de consulta (sintaxis PostgREST)
            params = {
                "select": "*",
                archivo_col: f"eq.{file_name}",
            }
            
            # Intentar ordenar por id si está disponible
            if "id" in available_columns:
                params["order"] = "id.asc"
            
            # Obtener datos
            try:
                data = self._make_request("GET", table_name, params=params)
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg or "column" in error_msg.lower():
                    logger.error(f"Error: La columna {archivo_col} no existe en {table_name}. "
                               f"Ejecuta el script SQL en scripts/create_supabase_columns.sql para crear las columnas.")
                    raise Exception(f"Columna {archivo_col} no existe en {table_name}. Ver logs para más detalles.")
                raise
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                return df
            else:
                return pd.DataFrame()  # DataFrame vacío si no hay datos
                
        except Exception as e:
            logger.error(f"Error obteniendo datos del archivo {file_name}: {str(e)}")
            raise
    
    def get_latest_files(self, provider: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene los archivos más recientes de un proveedor
        
        Args:
            provider: Proveedor (PIP_LATAM, PRECIA)
            limit: Número máximo de archivos a retornar
        
        Returns:
            Lista de archivos ordenados por fecha de subida (más recientes primero)
        """
        try:
            table_name = self.get_table_name(provider)
            
            # Detectar columnas disponibles
            available_columns = self._get_available_columns(table_name)
            
            # Mapear nombres de columnas esperados a posibles variaciones
            # Incluye variaciones en mayúsculas/minúsculas y nombres alternativos
            column_mapping = {
                "archivo_origen": ["TIPO_ARCHIVO", "tipo_archivo", "archivo_origen", "archivo", "file_name", "nombre_archivo"],
                "proveedor": ["FUENTE", "fuente", "proveedor", "provider", "PROVEEDOR"],
                "fecha": ["FECHA_VALORACION", "fecha_valoracion", "fecha", "date", "valuation_date", "FECHA"],
                "timestamp_ingesta": ["created_at", "CREATED_AT", "timestamp_ingesta", "timestamp", "upload_date", "fecha_ingesta"]
            }
            
            # Encontrar las columnas reales disponibles
            selected_columns = []
            for expected_col, variations in column_mapping.items():
                for variation in variations:
                    if variation in available_columns:
                        selected_columns.append(variation)
                        break
            
            # Si no encontramos las columnas necesarias, usar select=*
            if len(selected_columns) < 2:
                logger.warning(f"Usando select=* para {table_name} porque no se encontraron las columnas esperadas")
                params = {"select": "*", "limit": str(limit)}
            else:
                params = {
                    "select": ",".join(selected_columns),
                    "limit": str(limit)
                }
                
                # Intentar ordenar por timestamp si está disponible
                timestamp_col = None
                for col in ["created_at", "CREATED_AT", "timestamp_ingesta", "timestamp", "upload_date"]:
                    if col in available_columns:
                        timestamp_col = col
                        break
                if timestamp_col:
                    params["order"] = f"{timestamp_col}.desc"
            
            # Obtener datos
            try:
                data = self._make_request("GET", table_name, params=params)
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg or "column" in error_msg.lower():
                    logger.error(f"Error: Las columnas necesarias no existen en {table_name}. "
                               f"Ejecuta el script SQL en scripts/create_supabase_columns.sql para crear las columnas.")
                    raise Exception(f"Columnas faltantes en {table_name}. Ver logs para más detalles.")
                raise
            
            if isinstance(data, list):
                # Agrupar por archivo_origen (o la columna equivalente)
                file_groups = {}
                archivo_col = None
                proveedor_col = None
                fecha_col = None
                timestamp_col = None
                
                # Encontrar las columnas reales en los datos
                if len(data) > 0:
                    row_keys = list(data[0].keys())
                    for key in row_keys:
                        key_lower = key.lower()
                        key_upper = key.upper()
                        # Mapeo de archivo_origen
                        if key_upper == "TIPO_ARCHIVO" or "archivo" in key_lower or "file" in key_lower:
                            archivo_col = key
                        # Mapeo de proveedor
                        if key_upper == "FUENTE" or "proveedor" in key_lower or "provider" in key_lower:
                            proveedor_col = key
                        # Mapeo de fecha
                        if key_upper == "FECHA_VALORACION" or key_lower in ["fecha", "fecha_valoracion", "date", "valuation_date"]:
                            fecha_col = key
                        # Mapeo de timestamp
                        if key_upper == "CREATED_AT" or "timestamp" in key_lower or "created_at" in key_lower or "upload" in key_lower:
                            timestamp_col = key
                
                for row in data:
                    file_name = row.get(archivo_col) if archivo_col else row.get("archivo_origen", "N/A")
                    if file_name and file_name != "N/A":
                        if file_name not in file_groups:
                            file_groups[file_name] = {
                                "name": file_name,
                                "provider": row.get(proveedor_col) if proveedor_col else row.get("proveedor"),
                                "fecha_valoracion": str(row.get(fecha_col)) if fecha_col and row.get(fecha_col) else None,
                                "upload_date": row.get(timestamp_col) if timestamp_col else row.get("timestamp_ingesta"),
                                "record_count": 0
                            }
                        file_groups[file_name]["record_count"] += 1
                
                return list(file_groups.values())
            
            return []
        except Exception as e:
            logger.error(f"Error obteniendo archivos recientes: {str(e)}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Verifica si una tabla existe en la base de datos"""
        try:
            # Intentar hacer una petición simple a la tabla
            params = {"select": "id", "limit": "1"}
            self._make_request("GET", table_name, params=params)
            return True
        except Exception as e:
            logger.debug(f"Tabla {table_name} no existe o no es accesible: {str(e)}")
            return False
    
    def test_connection(self) -> Dict:
        """
        Prueba la conexión a Supabase y verifica que las tablas existan
        
        Returns:
            Diccionario con el resultado de la prueba
        """
        try:
            # Probar conexión básica haciendo una petición simple
            test_url = f"{self.api_url}/"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(test_url, headers=self.headers)
                response.raise_for_status()
            
            # Verificar tablas
            pip_exists = self.table_exists(self.table_pip)
            precia_exists = self.table_exists(self.table_precia)
            
            return {
                "success": True,
                "message": "Conexión exitosa a Supabase API",
                "base_url": self.base_url,
                "tables": {
                    self.table_pip: pip_exists,
                    self.table_precia: precia_exists
                },
                "all_tables_exist": pip_exists and precia_exists
            }
        except Exception as e:
            logger.error(f"Error probando conexión: {str(e)}")
            return {
                "success": False,
                "message": f"Error de conexión: {str(e)}",
                "base_url": self.base_url,
                "tables": {
                    self.table_pip: False,
                    self.table_precia: False
                },
                "all_tables_exist": False
            }
    
    def close(self):
        """Cierra la conexión con Supabase (no necesario para API REST, pero mantiene compatibilidad)"""
        logger.info("Conexión con Supabase API cerrada")
