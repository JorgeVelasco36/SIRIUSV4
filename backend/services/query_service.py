"""
Servicio de consultas estructuradas a la base de datos
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict
from datetime import date
from models import Valuation, Provider
from schemas import ValuationQuery
import logging

logger = logging.getLogger(__name__)


class QueryService:
    """Servicio para realizar consultas estructuradas a las valoraciones"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def query_valuations(self, query: ValuationQuery) -> List[Valuation]:
        """
        Consulta valoraciones según filtros
        
        Args:
            query: Objeto ValuationQuery con filtros
        
        Returns:
            Lista de valoraciones que cumplen los criterios
        """
        query_builder = self.db.query(Valuation)
        
        # Filtro por ISIN
        if query.isin:
            query_builder = query_builder.filter(Valuation.isin == query.isin)
        
        # Filtro por múltiples ISINs
        if query.isins:
            query_builder = query_builder.filter(Valuation.isin.in_(query.isins))
        
        # Filtro por proveedor
        if query.proveedor:
            query_builder = query_builder.filter(Valuation.proveedor == query.proveedor)
        
        # Filtro por fecha exacta
        if query.fecha:
            query_builder = query_builder.filter(Valuation.fecha == query.fecha)
        
        # Filtro por rango de fechas
        if query.fecha_inicio:
            query_builder = query_builder.filter(Valuation.fecha >= query.fecha_inicio)
        
        if query.fecha_fin:
            query_builder = query_builder.filter(Valuation.fecha <= query.fecha_fin)
        
        # Filtro por emisor
        if query.emisor:
            query_builder = query_builder.filter(
                Valuation.emisor.ilike(f"%{query.emisor}%")
            )
        
        # Filtro por tipo de instrumento
        if query.tipo_instrumento:
            query_builder = query_builder.filter(
                Valuation.tipo_instrumento.ilike(f"%{query.tipo_instrumento}%")
            )
        
        return query_builder.order_by(Valuation.fecha.desc(), Valuation.isin).all()
    
    def get_latest_valuation(self, isin: str, provider: Optional[Provider] = None) -> Optional[Valuation]:
        """
        Obtiene la valoración más reciente de un ISIN
        
        Args:
            isin: Código ISIN
            provider: Proveedor (opcional)
        
        Returns:
            Valoración más reciente o None
        """
        query_builder = self.db.query(Valuation).filter(Valuation.isin == isin)
        
        if provider:
            query_builder = query_builder.filter(Valuation.proveedor == provider)
        
        return query_builder.order_by(Valuation.fecha.desc()).first()
    
    def compare_providers(self, isin: str, fecha: Optional[date] = None) -> Dict:
        """
        Compara valoraciones entre proveedores para un ISIN
        
        Args:
            isin: Código ISIN
            fecha: Fecha de valoración (opcional, usa la más reciente si no se especifica)
        
        Returns:
            Diccionario con comparación de proveedores
        """
        if not fecha:
            # Obtener fecha más reciente disponible
            latest = self.db.query(Valuation.fecha).filter(
                Valuation.isin == isin
            ).order_by(Valuation.fecha.desc()).first()
            
            if not latest:
                return {"error": "No se encontraron valoraciones para este ISIN"}
            
            fecha = latest[0]
        
        # Obtener valoraciones de ambos proveedores
        pip_latam = self.db.query(Valuation).filter(
            and_(
                Valuation.isin == isin,
                Valuation.fecha == fecha,
                Valuation.proveedor == Provider.PIP_LATAM
            )
        ).first()
        
        precia = self.db.query(Valuation).filter(
            and_(
                Valuation.isin == isin,
                Valuation.fecha == fecha,
                Valuation.proveedor == Provider.PRECIA
            )
        ).first()
        
        comparison = {
            "isin": isin,
            "fecha": fecha,
            "pip_latam": None,
            "precia": None,
            "diferencias": {}
        }
        
        if pip_latam:
            comparison["pip_latam"] = {
                "precio_limpio": pip_latam.precio_limpio,
                "precio_sucio": pip_latam.precio_sucio,
                "tasa": pip_latam.tasa,
                "duracion": pip_latam.duracion,
                "convexidad": pip_latam.convexidad,
            }
        
        if precia:
            comparison["precia"] = {
                "precio_limpio": precia.precio_limpio,
                "precio_sucio": precia.precio_sucio,
                "tasa": precia.tasa,
                "duracion": precia.duracion,
                "convexidad": precia.convexidad,
            }
        
        # Calcular diferencias
        if pip_latam and precia:
            if pip_latam.precio_limpio and precia.precio_limpio:
                comparison["diferencias"]["precio_limpio"] = (
                    precia.precio_limpio - pip_latam.precio_limpio
                )
            
            if pip_latam.tasa and precia.tasa:
                comparison["diferencias"]["tasa"] = (
                    precia.tasa - pip_latam.tasa
                )
            
            if pip_latam.duracion and precia.duracion:
                comparison["diferencias"]["duracion"] = (
                    precia.duracion - pip_latam.duracion
                )
        
        return comparison
    
    def get_missing_data(self, isin: str, fecha: Optional[date] = None) -> List[str]:
        """
        Identifica datos faltantes o inconsistentes
        
        Args:
            isin: Código ISIN
            fecha: Fecha de valoración (opcional)
        
        Returns:
            Lista de alertas sobre datos faltantes
        """
        alerts = []
        
        if not fecha:
            latest = self.get_latest_valuation(isin)
            if not latest:
                alerts.append(f"No se encontraron valoraciones para ISIN {isin}")
                return alerts
            fecha = latest.fecha
        
        # Verificar ambos proveedores
        pip_latam = self.db.query(Valuation).filter(
            and_(
                Valuation.isin == isin,
                Valuation.fecha == fecha,
                Valuation.proveedor == Provider.PIP_LATAM
            )
        ).first()
        
        precia = self.db.query(Valuation).filter(
            and_(
                Valuation.isin == isin,
                Valuation.fecha == fecha,
                Valuation.proveedor == Provider.PRECIA
            )
        ).first()
        
        if not pip_latam:
            alerts.append(f"No se encontró valoración en PIP Latam para ISIN {isin} en fecha {fecha}")
        
        if not precia:
            alerts.append(f"No se encontró valoración en Precia para ISIN {isin} en fecha {fecha}")
        
        # Verificar campos críticos
        for provider_name, valuation in [("PIP Latam", pip_latam), ("Precia", precia)]:
            if valuation:
                if not valuation.precio_limpio:
                    alerts.append(f"Precio limpio faltante en {provider_name} para ISIN {isin}")
                if not valuation.tasa:
                    alerts.append(f"Tasa faltante en {provider_name} para ISIN {isin}")
        
        return alerts






