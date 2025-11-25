"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from models import Provider


class ValuationBase(BaseModel):
    """Base schema for valuation"""
    isin: str = Field(..., max_length=12)
    emisor: Optional[str] = None
    tipo_instrumento: Optional[str] = None
    plazo: Optional[str] = None
    precio_limpio: Optional[float] = None
    precio_sucio: Optional[float] = None
    tasa: Optional[float] = None
    duracion: Optional[float] = None
    convexidad: Optional[float] = None
    fecha: date
    proveedor: Provider
    archivo_origen: Optional[str] = None


class ValuationCreate(ValuationBase):
    """Schema for creating a valuation"""
    pass


class ValuationResponse(ValuationBase):
    """Schema for valuation response"""
    id: int
    timestamp_ingesta: datetime
    fecha_vencimiento: Optional[date] = None
    fecha_emision: Optional[date] = None
    valor_nominal: Optional[float] = None
    cupon: Optional[float] = None
    frecuencia_cupon: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Schema for chat message"""
    message: str = Field(..., min_length=1, max_length=2000)
    user: Optional[str] = None
    filters: Optional[dict] = None


class ChatResponse(BaseModel):
    """Schema for chat response"""
    answer: str
    data: Optional[List[dict]] = None
    recommendations: List[str] = Field(default_factory=list)
    metadata: Optional[dict] = None


class ValuationQuery(BaseModel):
    """Schema for structured valuation query"""
    isin: Optional[str] = None
    isins: Optional[List[str]] = None
    proveedor: Optional[Provider] = None
    fecha: Optional[date] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    emisor: Optional[str] = None
    tipo_instrumento: Optional[str] = None


class IngestRequest(BaseModel):
    """Schema for file ingestion request"""
    provider: Provider
    file_path: Optional[str] = None
    supabase_file_name: Optional[str] = None  # Nombre del archivo en Supabase
    fecha_valoracion: Optional[date] = None
    supabase_api_key: Optional[str] = None  # API Key de Supabase (opcional, deprecated)
    supabase_access_token: Optional[str] = None  # Access token JWT de Supabase (opcional)


class IngestResponse(BaseModel):
    """Schema for ingestion response"""
    success: bool
    message: str
    records_processed: int
    file_metadata_id: Optional[int] = None


class SupabaseAuthRequest(BaseModel):
    """Schema for Supabase authentication request"""
    email: str = Field(..., min_length=1)  # Correo electrónico
    password: str = Field(..., min_length=1)  # Contraseña


class SupabaseAuthResponse(BaseModel):
    """Schema for Supabase authentication response"""
    success: bool
    message: str
    tables_status: Optional[dict] = None
    access_token: Optional[str] = None  # Token JWT para usar en peticiones

