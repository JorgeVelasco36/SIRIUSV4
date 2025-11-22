"""
Servicio de ingesta y normalización de archivos de valoración
"""
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from models import Valuation, FileMetadata, Provider
from services.supabase_service import SupabaseService
import io

logger = logging.getLogger(__name__)


class IngestionService:
    """Servicio para ingerir y normalizar archivos de valoración"""
    
    # Mapeo de columnas comunes por proveedor
    COLUMN_MAPPINGS = {
        Provider.PIP_LATAM: {
            "ISIN": "isin",
            "Código ISIN": "isin",
            "Emisor": "emisor",
            "Tipo": "tipo_instrumento",
            "Tipo Instrumento": "tipo_instrumento",
            "Plazo": "plazo",
            "Precio Limpio": "precio_limpio",
            "Precio Sucio": "precio_sucio",
            "Tasa": "tasa",
            "Duración": "duracion",
            "Convexidad": "convexidad",
            "Fecha": "fecha",
            "Fecha Valoración": "fecha",
            "Fecha Vencimiento": "fecha_vencimiento",
            "Fecha Emisión": "fecha_emision",
            "Valor Nominal": "valor_nominal",
            "Cupón": "cupon",
            "Frecuencia Cupón": "frecuencia_cupon",
        },
        Provider.PRECIA: {
            "ISIN": "isin",
            "Código ISIN": "isin",
            "Emisor": "emisor",
            "Tipo": "tipo_instrumento",
            "Tipo Instrumento": "tipo_instrumento",
            "Plazo": "plazo",
            "Precio Limpio": "precio_limpio",
            "Precio Sucio": "precio_sucio",
            "Tasa": "tasa",
            "Duración": "duracion",
            "Convexidad": "convexidad",
            "Fecha": "fecha",
            "Fecha Valoración": "fecha",
            "Fecha Vencimiento": "fecha_vencimiento",
            "Fecha Emisión": "fecha_emision",
            "Valor Nominal": "valor_nominal",
            "Cupón": "cupon",
            "Frecuencia Cupón": "frecuencia_cupon",
        }
    }
    
    def __init__(self, db: Session, supabase_email: Optional[str] = None, supabase_password: Optional[str] = None):
        self.db = db
        self.supabase = SupabaseService(email=supabase_email, password=supabase_password)
    
    def normalize_column_names(self, df: pd.DataFrame, provider: Provider) -> pd.DataFrame:
        """
        Normaliza nombres de columnas según el proveedor
        
        Args:
            df: DataFrame con datos originales
            provider: Proveedor de los datos
        
        Returns:
            DataFrame con columnas normalizadas
        """
        mapping = self.COLUMN_MAPPINGS.get(provider, {})
        df_normalized = df.copy()
        
        # Normalizar nombres de columnas
        rename_dict = {}
        for col in df.columns:
            col_upper = str(col).strip()
            if col_upper in mapping:
                rename_dict[col] = mapping[col_upper]
            else:
                # Intentar búsqueda case-insensitive
                for key, value in mapping.items():
                    if col_upper.upper() == key.upper():
                        rename_dict[col] = value
                        break
        
        df_normalized = df_normalized.rename(columns=rename_dict)
        
        return df_normalized
    
    def parse_date(self, date_value) -> Optional[date]:
        """Convierte valor a fecha"""
        if pd.isna(date_value):
            return None
        
        if isinstance(date_value, date):
            return date_value
        
        if isinstance(date_value, datetime):
            return date_value.date()
        
        try:
            return pd.to_datetime(date_value).date()
        except:
            return None
    
    def parse_float(self, value) -> Optional[float]:
        """Convierte valor a float"""
        if pd.isna(value):
            return None
        
        try:
            return float(value)
        except:
            return None
    
    def parse_string(self, value) -> Optional[str]:
        """Convierte valor a string"""
        if pd.isna(value):
            return None
        
        return str(value).strip()
    
    def process_dataframe(self, df: pd.DataFrame, provider: Provider, 
                         fecha_valoracion: date, archivo_origen: str) -> List[Valuation]:
        """
        Procesa DataFrame y crea objetos Valuation
        
        Args:
            df: DataFrame normalizado
            provider: Proveedor
            fecha_valoracion: Fecha de valoración
            archivo_origen: Nombre del archivo origen
        
        Returns:
            Lista de objetos Valuation
        """
        valuations = []
        
        # Normalizar columnas
        df_normalized = self.normalize_column_names(df, provider)
        
        # Validar que existe columna ISIN
        if "isin" not in df_normalized.columns:
            raise ValueError("No se encontró columna ISIN en el archivo")
        
        for _, row in df_normalized.iterrows():
            try:
                # Extraer ISIN (obligatorio)
                isin = self.parse_string(row.get("isin"))
                if not isin:
                    continue
                
                # Crear objeto Valuation
                valuation = Valuation(
                    isin=isin,
                    emisor=self.parse_string(row.get("emisor")),
                    tipo_instrumento=self.parse_string(row.get("tipo_instrumento")),
                    plazo=self.parse_string(row.get("plazo")),
                    precio_limpio=self.parse_float(row.get("precio_limpio")),
                    precio_sucio=self.parse_float(row.get("precio_sucio")),
                    tasa=self.parse_float(row.get("tasa")),
                    duracion=self.parse_float(row.get("duracion")),
                    convexidad=self.parse_float(row.get("convexidad")),
                    fecha=fecha_valoracion,
                    proveedor=provider,
                    archivo_origen=archivo_origen,
                    fecha_vencimiento=self.parse_date(row.get("fecha_vencimiento")),
                    fecha_emision=self.parse_date(row.get("fecha_emision")),
                    valor_nominal=self.parse_float(row.get("valor_nominal")),
                    cupon=self.parse_float(row.get("cupon")),
                    frecuencia_cupon=self.parse_string(row.get("frecuencia_cupon")),
                )
                
                valuations.append(valuation)
            except Exception as e:
                logger.warning(f"Error procesando fila: {str(e)}")
                continue
        
        return valuations
    
    def ingest_from_file(self, file_path: str, provider: Provider, 
                        fecha_valoracion: Optional[date] = None) -> Dict:
        """
        Ingiere datos desde un archivo local
        
        Args:
            file_path: Ruta del archivo
            provider: Proveedor
            fecha_valoracion: Fecha de valoración (opcional)
        
        Returns:
            Diccionario con resultado de la ingesta
        """
        try:
            # Leer archivo
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                raise ValueError(f"Formato de archivo no soportado: {file_path}")
            
            # Determinar fecha de valoración
            if not fecha_valoracion:
                fecha_valoracion = date.today()
            
            # Procesar datos
            valuations = self.process_dataframe(df, provider, fecha_valoracion, file_path)
            
            if not valuations:
                raise ValueError("No se encontraron registros válidos en el archivo")
            
            # Guardar en base de datos
            file_metadata = FileMetadata(
                nombre_archivo=file_path.split('/')[-1],
                proveedor=provider,
                fecha_valoracion=fecha_valoracion,
                estado_procesamiento="PROCESADO",
                registros_ingresados=len(valuations),
                ruta_archivo=file_path
            )
            
            self.db.add(file_metadata)
            self.db.flush()
            
            # Insertar valoraciones
            for valuation in valuations:
                self.db.add(valuation)
            
            self.db.commit()
            
            logger.info(f"Ingesta exitosa: {len(valuations)} registros de {provider.value}")
            
            return {
                "success": True,
                "message": f"Ingesta exitosa: {len(valuations)} registros",
                "records_processed": len(valuations),
                "file_metadata_id": file_metadata.id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error en ingesta: {str(e)}")
            raise
    
    def ingest_from_supabase(self, file_name: str, provider: Provider,
                             fecha_valoracion: Optional[date] = None) -> Dict:
        """
        Ingiere datos desde Supabase PostgreSQL
        
        Args:
            file_name: Nombre del archivo en Supabase
            provider: Proveedor
            fecha_valoracion: Fecha de valoración (opcional)
        
        Returns:
            Diccionario con resultado de la ingesta
        """
        try:
            # Obtener datos desde Supabase
            df = self.supabase.get_data_by_file(file_name, provider.value)
            
            if df.empty:
                raise ValueError(f"No se encontraron datos para el archivo {file_name}")
            
            # Determinar fecha de valoración
            if not fecha_valoracion:
                if 'fecha' in df.columns and not df['fecha'].isna().all():
                    fecha_valoracion = pd.to_datetime(df['fecha'].iloc[0]).date()
                else:
                    fecha_valoracion = date.today()
            
            # Procesar datos
            archivo_origen = f"Supabase:{file_name}"
            valuations = self.process_dataframe(df, provider, fecha_valoracion, archivo_origen)
            
            if not valuations:
                raise ValueError("No se encontraron registros válidos en el archivo")
            
            # Guardar en base de datos local
            file_metadata = FileMetadata(
                nombre_archivo=file_name,
                proveedor=provider,
                fecha_valoracion=fecha_valoracion,
                estado_procesamiento="PROCESADO",
                registros_ingresados=len(valuations),
                ruta_archivo=f"Supabase:{file_name}"
            )
            
            self.db.add(file_metadata)
            self.db.flush()
            
            # Insertar valoraciones
            for valuation in valuations:
                self.db.add(valuation)
            
            self.db.commit()
            
            logger.info(f"Ingesta desde Supabase exitosa: {len(valuations)} registros")
            
            return {
                "success": True,
                "message": f"Ingesta exitosa: {len(valuations)} registros",
                "records_processed": len(valuations),
                "file_metadata_id": file_metadata.id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error en ingesta desde Supabase: {str(e)}")
            raise

