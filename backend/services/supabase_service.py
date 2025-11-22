"""
Servicio para integración con Supabase PostgreSQL
Lee archivos de valoración almacenados en las tablas BD_PIP y BD_Precia
"""
from sqlalchemy import create_engine, text, inspect
from typing import Optional, List, Dict
from config import settings
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class SupabaseService:
    """Servicio para interactuar con Supabase PostgreSQL"""
    
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Inicializa la conexión con Supabase
        
        Args:
            email: Email del usuario de Supabase (opcional, si no se proporciona usa .env)
            password: Contraseña del usuario de Supabase (opcional, si no se proporciona usa .env)
        """
        self.database_name = settings.supabase_db_name
        self.table_pip = settings.supabase_table_pip
        self.table_precia = settings.supabase_table_precia
        
        # Construir URL de conexión
        if email and password:
            # Usar credenciales proporcionadas
            # Nota: En Supabase, el usuario de la base de datos es siempre 'postgres'
            # El email es solo para referencia, la contraseña es la de la base de datos
            base_url = settings.supabase_db_url
            if base_url and '[YOUR_PASSWORD]' not in base_url:
                # Extraer host y puerto de la URL existente
                import re
                match = re.search(r'@([^:]+):(\d+)/(.+)', base_url)
                if match:
                    host = match.group(1)
                    port = match.group(2)
                    db_name = match.group(3)
                    # Construir URL con la contraseña proporcionada
                    # El usuario siempre es 'postgres' en Supabase
                    self.supabase_url = f"postgresql://postgres:{password}@{host}:{port}/{db_name}"
                else:
                    # Si no podemos parsear, usar la estructura por defecto
                    self.supabase_url = f"postgresql://postgres:{password}@db.mwyltxcgjxsrdmgsuysv.supabase.co:5432/postgres"
            else:
                # URL por defecto de Supabase (del .env o hardcoded)
                self.supabase_url = f"postgresql://postgres:{password}@db.mwyltxcgjxsrdmgsuysv.supabase.co:5432/postgres"
        else:
            # Usar configuración del .env
            self.supabase_url = settings.supabase_db_url
            if not self.supabase_url or '[YOUR_PASSWORD]' in self.supabase_url:
                raise ValueError("SUPABASE_DB_URL no está configurado correctamente en .env o se requieren credenciales")
        
        try:
            self.engine = create_engine(
                self.supabase_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            logger.info(f"Conectado a Supabase: {self.database_name}")
        except Exception as e:
            logger.error(f"Error conectando a Supabase: {str(e)}")
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
            
            if provider:
                table_name = self.get_table_name(provider)
                query = f"""
                    SELECT DISTINCT 
                        archivo_origen as name,
                        proveedor as provider,
                        fecha as fecha_valoracion,
                        MAX(timestamp_ingesta) as upload_date,
                        COUNT(*) as record_count
                    FROM "{table_name}"
                    WHERE 1=1
                """
                
                if fecha_valoracion:
                    query += f" AND fecha = '{fecha_valoracion}'"
                
                query += ' GROUP BY archivo_origen, proveedor, fecha ORDER BY upload_date DESC'
                
                with self.engine.connect() as conn:
                    result = conn.execute(text(query))
                    for row in result:
                        files.append({
                            "name": row.name or "N/A",
                            "provider": row.provider,
                            "fecha_valoracion": str(row.fecha_valoracion) if row.fecha_valoracion else None,
                            "upload_date": row.upload_date,
                            "record_count": row.record_count
                        })
            else:
                # Buscar en ambas tablas
                for table_name in [self.table_pip, self.table_precia]:
                    query = f"""
                        SELECT DISTINCT 
                            archivo_origen as name,
                            proveedor as provider,
                            fecha as fecha_valoracion,
                            MAX(timestamp_ingesta) as upload_date,
                            COUNT(*) as record_count
                        FROM "{table_name}"
                        WHERE 1=1
                    """
                    
                    if fecha_valoracion:
                        query += f" AND fecha = '{fecha_valoracion}'"
                    
                    query += ' GROUP BY archivo_origen, proveedor, fecha ORDER BY upload_date DESC'
                    
                    with self.engine.connect() as conn:
                        result = conn.execute(text(query))
                        for row in result:
                            files.append({
                                "name": row.name or "N/A",
                                "provider": row.provider,
                                "fecha_valoracion": str(row.fecha_valoracion) if row.fecha_valoracion else None,
                                "upload_date": row.upload_date,
                                "record_count": row.record_count
                            })
            
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
            query = f"""
                SELECT * FROM "{table_name}"
                WHERE archivo_origen = :file_name
                ORDER BY id
            """
            
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params={"file_name": file_name})
            
            return df
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
            query = f"""
                SELECT DISTINCT 
                    archivo_origen as name,
                    proveedor as provider,
                    fecha as fecha_valoracion,
                    MAX(timestamp_ingesta) as upload_date,
                    COUNT(*) as record_count
                FROM "{table_name}"
                GROUP BY archivo_origen, proveedor, fecha
                ORDER BY upload_date DESC
                LIMIT {limit}
            """
            
            files = []
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                for row in result:
                    files.append({
                        "name": row.name or "N/A",
                        "provider": row.provider,
                        "fecha_valoracion": str(row.fecha_valoracion) if row.fecha_valoracion else None,
                        "upload_date": row.upload_date,
                        "record_count": row.record_count
                    })
            
            return files
        except Exception as e:
            logger.error(f"Error obteniendo archivos recientes: {str(e)}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Verifica si una tabla existe en la base de datos"""
        try:
            inspector = inspect(self.engine)
            return table_name in inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error verificando existencia de tabla: {str(e)}")
            return False
    
    def test_connection(self) -> Dict:
        """
        Prueba la conexión a Supabase y verifica que las tablas existan
        
        Returns:
            Diccionario con el resultado de la prueba
        """
        try:
            with self.engine.connect() as conn:
                # Probar conexión básica
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            # Verificar tablas
            pip_exists = self.table_exists(self.table_pip)
            precia_exists = self.table_exists(self.table_precia)
            
            return {
                "success": True,
                "message": "Conexión exitosa a Supabase",
                "database": self.database_name,
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
                "database": self.database_name,
                "tables": {
                    self.table_pip: False,
                    self.table_precia: False
                },
                "all_tables_exist": False
            }
    
    def close(self):
        """Cierra la conexión con Supabase"""
        if self.engine:
            self.engine.dispose()
            logger.info("Conexión con Supabase cerrada")

