"""
S.I.R.I.U.S V4 - API Principal
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging
import os

from database import get_db, engine, Base
from models import Provider
from schemas import (
    ChatMessage, ChatResponse, ValuationResponse, ValuationQuery,
    IngestRequest, IngestResponse, SupabaseAuthRequest, SupabaseAuthResponse
)
from services.chat_service import ChatService
from services.query_service import QueryService
from services.ingestion_service import IngestionService
from config import settings
from typing import Dict
import threading

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Almacenamiento de contexto de conversación por usuario/sesión
# Clave: user_id o session_id, Valor: dict con last_query, last_results, last_query_params
conversation_contexts: Dict[str, Dict] = {}
context_lock = threading.Lock()  # Lock para acceso thread-safe

# Inicializar FastAPI
app = FastAPI(
    title="S.I.R.I.U.S V4 API",
    description="Asistente Conversacional de Renta Fija Colombiana",
    version="4.0.0"
)

# Configurar archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
jinja_env = Environment(loader=FileSystemLoader("templates"))

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página principal con interfaz de chat"""
    template = jinja_env.get_template("base.html")
    return HTMLResponse(content=template.render())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post(f"{settings.api_v1_prefix}/auth/supabase", response_model=SupabaseAuthResponse)
async def authenticate_supabase(auth: SupabaseAuthRequest):
    """
    Endpoint para autenticar con Supabase usando correo y contraseña
    
    Valida las credenciales y verifica que las tablas existan
    """
    try:
        from services.supabase_service import SupabaseService
        
        # Autenticar con correo y contraseña
        auth_result = SupabaseService.authenticate_with_email_password(
            email=auth.email,
            password=auth.password
        )
        
        if not auth_result["success"]:
            return SupabaseAuthResponse(
                success=False,
                message="Error de autenticación. Por favor, verifica tu correo y contraseña.",
                tables_status=None
            )
        
        # Crear servicio con el access token obtenido
        supabase = SupabaseService(access_token=auth_result["access_token"])
        
        # Probar la conexión y verificar tablas
        result = supabase.test_connection()
        
        supabase.close()
        
        if result["success"]:
            return SupabaseAuthResponse(
                success=True,
                message="Autenticación exitosa",
                tables_status=result["tables"],
                access_token=auth_result.get("access_token")  # Devolver el token para que el frontend lo use
            )
        else:
            return SupabaseAuthResponse(
                success=False,
                message="Error de conexión. Por favor, verifica tu correo y contraseña.",
                tables_status=None
            )
            
    except Exception as e:
        logger.error(f"Error en autenticación de Supabase: {str(e)}")
        error_message = str(e)
        
        # Mensajes de error más amigables
        if "401" in error_message or "unauthorized" in error_message.lower() or "invalid" in error_message.lower():
            error_message = "Error de autenticación. Por favor, verifica tu correo y contraseña."
        elif "could not connect" in error_message.lower() or "connection" in error_message.lower():
            error_message = "Error de conexión. Verifica tu conexión a internet."
        else:
            error_message = "Error de autenticación. Por favor, verifica tu correo y contraseña."
        
        return SupabaseAuthResponse(
            success=False,
            message=error_message,
            tables_status=None
        )


@app.post(f"{settings.api_v1_prefix}/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    Endpoint principal de chat - Procesa consultas en lenguaje natural
    
    Ejemplos de consultas:
    - "¿Cuál es el precio limpio del TES CO000123 hoy en Precia?"
    - "Compara PIP Latam vs Precia para este ISIN."
    - "Trae valoración de ayer para estos 5 ISINs."
    """
    try:
        # Identificar usuario/sesión para mantener contexto
        user_id = message.user or "default"
        
        # Obtener contexto previo de la conversación (thread-safe)
        context = None
        with context_lock:
            context = conversation_contexts.get(user_id)
        
        # Usar el token de acceso de Supabase si está disponible
        access_token = message.supabase_access_token
        chat_service = ChatService(
            db, 
            supabase_access_token=access_token,
            conversation_context=context
        )
        response = chat_service.generate_response(message.message, message.user)
        
        # Guardar nuevo contexto después de procesar la consulta (thread-safe)
        new_context = chat_service.get_conversation_context()
        with context_lock:
            conversation_contexts[user_id] = new_context
        
        return ChatResponse(**response)
    except Exception as e:
        logger.error(f"Error en endpoint /chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando consulta: {str(e)}")


@app.get(f"{settings.api_v1_prefix}/valuations", response_model=List[ValuationResponse])
async def get_valuations(
    isin: Optional[str] = None,
    isins: Optional[str] = None,  # Coma separada
    proveedor: Optional[Provider] = None,
    fecha: Optional[date] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    emisor: Optional[str] = None,
    tipo_instrumento: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint para consultar valoraciones con filtros estructurados
    """
    try:
        # Procesar lista de ISINs
        isin_list = None
        if isins:
            isin_list = [i.strip() for i in isins.split(",")]
        
        query = ValuationQuery(
            isin=isin,
            isins=isin_list,
            proveedor=proveedor,
            fecha=fecha,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            emisor=emisor,
            tipo_instrumento=tipo_instrumento
        )
        
        query_service = QueryService(db)
        valuations = query_service.query_valuations(query)
        
        return [ValuationResponse.model_validate(v) for v in valuations]
    except Exception as e:
        logger.error(f"Error en endpoint /valuations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error consultando valoraciones: {str(e)}")


@app.get(f"{settings.api_v1_prefix}/valuations/compare")
async def compare_providers(
    isin: str,
    fecha: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint para comparar valoraciones entre proveedores
    """
    try:
        query_service = QueryService(db)
        comparison = query_service.compare_providers(isin, fecha)
        
        if "error" in comparison:
            raise HTTPException(status_code=404, detail=comparison["error"])
        
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /valuations/compare: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error comparando proveedores: {str(e)}")


@app.get(f"{settings.api_v1_prefix}/valuations/{{isin}}/alerts")
async def get_alerts(
    isin: str,
    fecha: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint para obtener alertas sobre datos faltantes o inconsistentes
    """
    try:
        query_service = QueryService(db)
        alerts = query_service.get_missing_data(isin, fecha)
        
        return {
            "isin": isin,
            "fecha": fecha.isoformat() if fecha else None,
            "alerts": alerts,
            "has_alerts": len(alerts) > 0
        }
    except Exception as e:
        logger.error(f"Error en endpoint /valuations/alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo alertas: {str(e)}")


@app.post(f"{settings.api_v1_prefix}/ingest", response_model=IngestResponse)
async def ingest_file(
    request: IngestRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint para ingerir archivos desde Supabase o ruta local
    """
    try:
        # Usar access token o API Key proporcionada, o la del .env
        ingestion_service = IngestionService(
            db,
            supabase_api_key=request.supabase_api_key,
            supabase_access_token=request.supabase_access_token
        )
        
        if request.supabase_file_name:
            # Ingesta desde Supabase
            result = ingestion_service.ingest_from_supabase(
                request.supabase_file_name,
                request.provider,
                request.fecha_valoracion
            )
        elif request.file_path:
            # Ingesta desde archivo local
            result = ingestion_service.ingest_from_file(
                request.file_path,
                request.provider,
                request.fecha_valoracion
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar file_path o supabase_file_name"
            )
        
        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Error en endpoint /ingest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en ingesta: {str(e)}")


@app.post(f"{settings.api_v1_prefix}/ingest/upload")
async def upload_file(
    file: UploadFile = File(...),
    provider: Provider = None,
    fecha_valoracion: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint para subir archivo directamente
    """
    try:
        if not provider:
            raise HTTPException(status_code=400, detail="Debe especificar el proveedor")
        
        # Guardar archivo temporalmente
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            ingestion_service = IngestionService(db)
            result = ingestion_service.ingest_from_file(
                tmp_path,
                provider,
                fecha_valoracion
            )
            return IngestResponse(**result)
        finally:
            # Limpiar archivo temporal
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /ingest/upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")


@app.get(f"{settings.api_v1_prefix}/providers")
async def list_providers():
    """Lista proveedores disponibles"""
    return {
        "providers": [
            {"value": Provider.PIP_LATAM.value, "name": "PIP Latam"},
            {"value": Provider.PRECIA.value, "name": "Precia"}
        ]
    }


@app.get(f"{settings.api_v1_prefix}/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Estadísticas generales de la base de datos"""
    try:
        from sqlalchemy import func
        from models import Valuation, FileMetadata
        
        total_valuations = db.query(func.count(Valuation.id)).scalar()
        total_files = db.query(func.count(FileMetadata.id)).scalar()
        
        by_provider = db.query(
            Valuation.proveedor,
            func.count(Valuation.id)
        ).group_by(Valuation.proveedor).all()
        
        latest_date = db.query(func.max(Valuation.fecha)).scalar()
        
        return {
            "total_valuations": total_valuations,
            "total_files": total_files,
            "by_provider": {p.value: count for p, count in by_provider},
            "latest_valuation_date": latest_date.isoformat() if latest_date else None
        }
    except Exception as e:
        logger.error(f"Error en endpoint /stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

