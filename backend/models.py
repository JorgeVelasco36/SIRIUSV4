"""
Database models for S.I.R.I.U.S V4
"""
from sqlalchemy import Column, String, Float, Date, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class Provider(str, enum.Enum):
    """Proveedores de valoración"""
    PIP_LATAM = "PIP_LATAM"
    PRECIA = "PRECIA"


class InstrumentType(str, enum.Enum):
    """Tipos de instrumentos de renta fija"""
    TES = "TES"
    BONO = "BONO"
    CDT = "CDT"
    PAPEL_COMERCIAL = "PAPEL_COMERCIAL"
    OTRO = "OTRO"


class Valuation(Base):
    """
    Tabla principal de valoraciones
    """
    __tablename__ = "valuations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación del instrumento
    isin = Column(String(12), index=True, nullable=False)
    emisor = Column(String(255), index=True)
    tipo_instrumento = Column(String(50), index=True)
    plazo = Column(String(50))
    
    # Valores de valoración
    precio_limpio = Column(Float)
    precio_sucio = Column(Float)
    tasa = Column(Float)
    duracion = Column(Float)
    convexidad = Column(Float)
    
    # Metadatos
    fecha = Column(Date, index=True, nullable=False)
    proveedor = Column(SQLEnum(Provider), index=True, nullable=False)
    archivo_origen = Column(String(500))
    timestamp_ingesta = Column(DateTime(timezone=True), server_default=func.now())
    
    # Campos adicionales normalizados
    fecha_vencimiento = Column(Date)
    fecha_emision = Column(Date)
    valor_nominal = Column(Float)
    cupon = Column(Float)
    frecuencia_cupon = Column(String(20))
    
    def __repr__(self):
        return f"<Valuation(isin={self.isin}, proveedor={self.proveedor}, fecha={self.fecha})>"


class FileMetadata(Base):
    """
    Metadatos de archivos procesados
    """
    __tablename__ = "files_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String(500), nullable=False)
    proveedor = Column(SQLEnum(Provider), nullable=False)
    fecha_valoracion = Column(Date, index=True, nullable=False)
    estado_procesamiento = Column(String(50), default="PROCESADO")
    registros_ingresados = Column(Integer, default=0)
    errores = Column(String(2000))
    timestamp_procesamiento = Column(DateTime(timezone=True), server_default=func.now())
    ruta_archivo = Column(String(1000))
    
    def __repr__(self):
        return f"<FileMetadata(nombre={self.nombre_archivo}, proveedor={self.proveedor})>"


class QueryLog(Base):
    """
    Log de consultas realizadas al asistente
    """
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    consulta = Column(String(2000), nullable=False)
    respuesta = Column(String(10000))
    usuario = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    isin_filtrado = Column(String(12))
    proveedor_filtrado = Column(String(50))
    fecha_filtrada = Column(Date)
    
    def __repr__(self):
        return f"<QueryLog(consulta={self.consulta[:50]}..., timestamp={self.timestamp})>"



