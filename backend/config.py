"""
Configuration settings for S.I.R.I.U.S V4 Backend
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    # Si no se especifica, usa SQLite (no requiere instalación)
    database_url: str = "sqlite:///./sirius_v4.db"
    
    # Supabase PostgreSQL (reemplaza a MongoDB)
    supabase_db_url: str = ""  # Connection string de Supabase
    supabase_db_name: str = "postgres"  # Nombre de la base de datos
    supabase_table_pip: str = "BD_PIP"  # Tabla para PIP_LATAM
    supabase_table_precia: str = "BD_Precia"  # Tabla para PRECIA
    
    # MongoDB Atlas (deprecated - ya no se usa)
    # mongodb_uri: str = ""
    # mongodb_database: str = "sirius_v4"
    # mongodb_collection: str = "valuation_files"
    
    # Microsoft Graph API (opcional - solo si aún necesitas SharePoint)
    # Para autenticación interactiva (usuario/contraseña), solo necesitas CLIENT_ID y TENANT_ID
    # Para autenticación de aplicación, también necesitas CLIENT_SECRET
    azure_client_id: str = ""
    azure_client_secret: str = ""  # Opcional para autenticación interactiva
    azure_tenant_id: str = ""
    sharepoint_site_id: str = ""  # Ejemplo: "FIDUCIARIACOOMEVA"
    sharepoint_drive_id: str = ""  # Opcional
    
    # LLM (obligatorio)
    openai_api_key: str
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.3
    
    # Application
    secret_key: str = "cambiar-en-produccion"
    environment: str = "development"
    log_level: str = "INFO"
    
    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

