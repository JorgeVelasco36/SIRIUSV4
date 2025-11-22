"""
Servicio para integración con MongoDB Atlas
Lee archivos de valoración almacenados en MongoDB
"""
from pymongo import MongoClient
from gridfs import GridFS
from typing import Optional, List, Dict
from config import settings
import logging
import io
import pandas as pd

logger = logging.getLogger(__name__)


class MongoDBService:
    """Servicio para interactuar con MongoDB Atlas"""
    
    def __init__(self):
        """Inicializa la conexión con MongoDB Atlas"""
        self.mongodb_uri = settings.mongodb_uri
        self.database_name = settings.mongodb_database
        self.collection_name = settings.mongodb_collection
        
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI no está configurado en .env")
        
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            self.fs = GridFS(self.db)
            logger.info(f"Conectado a MongoDB Atlas: {self.database_name}")
        except Exception as e:
            logger.error(f"Error conectando a MongoDB Atlas: {str(e)}")
            raise
    
    def list_files(self, provider: Optional[str] = None, 
                   fecha_valoracion: Optional[str] = None) -> List[Dict]:
        """
        Lista archivos disponibles en MongoDB
        
        Args:
            provider: Filtrar por proveedor (PIP_LATAM, PRECIA)
            fecha_valoracion: Filtrar por fecha (formato: YYYY-MM-DD)
        
        Returns:
            Lista de archivos con metadatos
        """
        try:
            query = {}
            
            if provider:
                query["metadata.provider"] = provider
            
            if fecha_valoracion:
                query["metadata.fecha_valoracion"] = fecha_valoracion
            
            # Buscar en GridFS
            files = []
            for file_info in self.fs.find(query):
                files.append({
                    "id": str(file_info._id),
                    "name": file_info.filename,
                    "provider": file_info.metadata.get("provider") if file_info.metadata else None,
                    "fecha_valoracion": file_info.metadata.get("fecha_valoracion") if file_info.metadata else None,
                    "upload_date": file_info.upload_date,
                    "length": file_info.length
                })
            
            return files
        except Exception as e:
            logger.error(f"Error listando archivos: {str(e)}")
            raise
    
    def get_file(self, file_id: str) -> bytes:
        """
        Obtiene un archivo desde MongoDB GridFS
        
        Args:
            file_id: ID del archivo en MongoDB (ObjectId como string)
        
        Returns:
            Contenido del archivo en bytes
        """
        try:
            from bson import ObjectId
            # Convertir string a ObjectId si es necesario
            if isinstance(file_id, str):
                file_id = ObjectId(file_id)
            file_data = self.fs.get(file_id)
            return file_data.read()
        except Exception as e:
            logger.error(f"Error obteniendo archivo {file_id}: {str(e)}")
            raise
    
    def get_file_by_name(self, file_name: str, provider: Optional[str] = None) -> Optional[Dict]:
        """
        Busca un archivo por nombre
        
        Args:
            file_name: Nombre del archivo
            provider: Proveedor (opcional)
        
        Returns:
            Metadatos del archivo o None si no se encuentra
        """
        try:
            query = {"filename": file_name}
            if provider:
                query["metadata.provider"] = provider
            
            file_info = self.fs.find_one(query)
            
            if file_info:
                return {
                    "id": str(file_info._id),
                    "name": file_info.filename,
                    "provider": file_info.metadata.get("provider") if file_info.metadata else None,
                    "fecha_valoracion": file_info.metadata.get("fecha_valoracion") if file_info.metadata else None,
                    "upload_date": file_info.upload_date,
                    "length": file_info.length
                }
            
            return None
        except Exception as e:
            logger.error(f"Error buscando archivo {file_name}: {str(e)}")
            raise
    
    def upload_file(self, file_content: bytes, file_name: str, 
                   provider: str, fecha_valoracion: str, metadata: Optional[Dict] = None) -> str:
        """
        Sube un archivo a MongoDB GridFS
        
        Args:
            file_content: Contenido del archivo en bytes
            file_name: Nombre del archivo
            provider: Proveedor (PIP_LATAM, PRECIA)
            fecha_valoracion: Fecha de valoración (YYYY-MM-DD)
            metadata: Metadatos adicionales (opcional)
        
        Returns:
            ID del archivo subido
        """
        try:
            file_metadata = {
                "provider": provider,
                "fecha_valoracion": fecha_valoracion,
                **(metadata or {})
            }
            
            file_id = self.fs.put(
                file_content,
                filename=file_name,
                metadata=file_metadata
            )
            
            logger.info(f"Archivo {file_name} subido a MongoDB con ID: {file_id}")
            return str(file_id)
        except Exception as e:
            logger.error(f"Error subiendo archivo {file_name}: {str(e)}")
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
            files = []
            query = {"metadata.provider": provider}
            
            for file_info in self.fs.find(query).sort("upload_date", -1).limit(limit):
                files.append({
                    "id": str(file_info._id),
                    "name": file_info.filename,
                    "provider": file_info.metadata.get("provider") if file_info.metadata else None,
                    "fecha_valoracion": file_info.metadata.get("fecha_valoracion") if file_info.metadata else None,
                    "upload_date": file_info.upload_date,
                    "length": file_info.length
                })
            
            return files
        except Exception as e:
            logger.error(f"Error obteniendo archivos recientes: {str(e)}")
            raise
    
    def close(self):
        """Cierra la conexión con MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Conexión con MongoDB cerrada")

