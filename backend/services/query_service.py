"""
Servicio de consultas estructuradas a la base de datos
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict
from datetime import date, datetime
from models import Valuation, Provider
from schemas import ValuationQuery
from services.supabase_service import SupabaseService
from services.ingestion_service import IngestionService
from config import settings
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class QueryService:
    """Servicio para realizar consultas estructuradas a las valoraciones"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def query_valuations(self, query: ValuationQuery, supabase_access_token: Optional[str] = None) -> List[Valuation]:
        """
        Consulta valoraciones según filtros
        
        Args:
            query: Objeto ValuationQuery con filtros
            supabase_access_token: Token de acceso a Supabase (opcional, para consulta directa)
        
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
            # Si también hay tipo_instrumento con el mismo valor, es un nemotécnico
            # Buscar en emisor O tipo_instrumento (OR)
            if query.tipo_instrumento and query.emisor == query.tipo_instrumento:
                query_builder = query_builder.filter(
                    or_(
                        Valuation.emisor.ilike(f"%{query.emisor}%"),
                        Valuation.tipo_instrumento.ilike(f"%{query.emisor}%")
                    )
                )
            else:
                query_builder = query_builder.filter(
                    Valuation.emisor.ilike(f"%{query.emisor}%")
                )
        
        # Filtro por tipo de instrumento (solo si no se usó en el filtro de emisor)
        if query.tipo_instrumento and not (query.emisor and query.emisor == query.tipo_instrumento):
            query_builder = query_builder.filter(
                Valuation.tipo_instrumento.ilike(f"%{query.tipo_instrumento}%")
            )
        
        # Filtro por fecha de vencimiento
        if query.fecha_vencimiento:
            query_builder = query_builder.filter(Valuation.fecha_vencimiento == query.fecha_vencimiento)
        
        # Filtro por cupón/tasa facial (con tolerancia para diferencias pequeñas por redondeo)
        if query.cupon is not None:
            # Permitir pequeña diferencia por redondeo (0.01%)
            query_builder = query_builder.filter(
                Valuation.cupon >= query.cupon - 0.01,
                Valuation.cupon <= query.cupon + 0.01
            )
        
        results = query_builder.order_by(Valuation.fecha.desc(), Valuation.isin).all()
        
        # Para nemotécnicos, siempre consultar Supabase directamente porque la BD local puede no tener todos los datos
        # Para ISINs, solo consultar Supabase si no hay resultados en BD local
        is_nemotecnico_search = (query.emisor and query.tipo_instrumento and 
                                query.emisor == query.tipo_instrumento and not query.isin)
        
        should_query_supabase = False
        if is_nemotecnico_search:
            # Para nemotécnicos, siempre consultar Supabase (puede haber más datos allí)
            should_query_supabase = True
            logger.info(f"Búsqueda por nemotécnico detectada, consultando Supabase para obtener todos los resultados disponibles...")
        elif not results and query.isin:
            # Para ISINs, solo si no hay resultados en BD local
            should_query_supabase = True
        
        # Consultar Supabase directamente si es necesario
        if should_query_supabase:
            # Intentar con access token primero, luego con API key como fallback
            auth_method = None
            auth_value = None
            
            # Determinar descripción de búsqueda
            if query.isin:
                search_desc = f"ISIN {query.isin}"
            elif query.emisor and query.tipo_instrumento and query.emisor == query.tipo_instrumento:
                search_desc = f"nemotécnico {query.emisor}"
            else:
                search_desc = "criterios especificados"
            
            if supabase_access_token:
                auth_method = "access_token"
                auth_value = supabase_access_token
                logger.info(f"No se encontraron resultados en BD local para {search_desc}, consultando Supabase con access token...")
            elif settings.supabase_api_key:
                auth_method = "api_key"
                auth_value = settings.supabase_api_key
                logger.info(f"No se encontraron resultados en BD local para {search_desc}, consultando Supabase con API key...")
            
            if auth_value:
                try:
                    supabase_results = self._query_supabase_directly(query, auth_value, use_api_key=(auth_method == "api_key"))
                    if supabase_results:
                        logger.info(f"Se encontraron {len(supabase_results)} valoraciones en Supabase para {search_desc}")
                        # Si es búsqueda por nemotécnico, usar los resultados de Supabase (más completos)
                        # Si es búsqueda por ISIN y no había resultados locales, usar los de Supabase
                        if is_nemotecnico_search:
                            # Para nemotécnicos, priorizar resultados de Supabase
                            results = supabase_results
                        elif not results:
                            # Para ISINs sin resultados locales, usar los de Supabase
                            results = supabase_results
                        else:
                            # Combinar resultados (evitar duplicados)
                            existing_isins_dates = {(r.isin, r.fecha, r.proveedor) for r in results}
                            for r in supabase_results:
                                if (r.isin, r.fecha, r.proveedor) not in existing_isins_dates:
                                    results.append(r)
                    else:
                        logger.warning(f"No se encontraron resultados en Supabase para {search_desc}")
                except Exception as e:
                    logger.error(f"Error consultando Supabase directamente: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning(f"No hay credenciales de Supabase disponibles para consultar {search_desc}")
        
        # Aplicar filtro de cupón final si es necesario (por si hay resultados de BD local que no se filtraron)
        if query.cupon is not None and results:
            cupon_min = query.cupon - 0.01
            cupon_max = query.cupon + 0.01
            resultados_antes = len(results)
            results = [
                r for r in results 
                if r.cupon is not None 
                and cupon_min <= r.cupon <= cupon_max
            ]
            resultados_despues = len(results)
            if resultados_antes != resultados_despues:
                logger.info(f"Filtro final de cupón {query.cupon}: {resultados_antes} → {resultados_despues} resultados")
        
        logger.info(f"Total de resultados encontrados después de todos los filtros: {len(results)}")
        return results
    
    def _query_supabase_directly(self, query: ValuationQuery, auth_value: str, use_api_key: bool = False) -> List[Valuation]:
        """
        Consulta Supabase directamente cuando no hay resultados en BD local
        
        Args:
            query: Objeto ValuationQuery con filtros
            auth_value: Token de acceso o API key de Supabase
            use_api_key: Si es True, usa auth_value como API key, sino como access token
        
        Returns:
            Lista de valoraciones encontradas en Supabase
        """
        try:
            if use_api_key:
                supabase = SupabaseService(api_key=auth_value)
                ingestion_service = IngestionService(self.db, supabase_api_key=auth_value)
            else:
                supabase = SupabaseService(access_token=auth_value)
                ingestion_service = IngestionService(self.db, supabase_access_token=auth_value)
            
            # Buscar en ambas tablas
            all_valuations = []
            for provider in [Provider.PIP_LATAM, Provider.PRECIA]:
                if query.proveedor and query.proveedor != provider:
                    continue
                
                try:
                    table_name = supabase.get_table_name(provider.value)
                    available_columns = supabase._get_available_columns(table_name)
                    
                    # Determinar qué columna usar para la búsqueda
                    search_params = {}
                    
                    if query.isin:
                        # Búsqueda por ISIN
                        isin_col = None
                        for col in ["ISIN", "isin", "ISIN_CODIGO", "codigo_isin"]:
                            if col in available_columns:
                                isin_col = col
                                break
                        
                        if isin_col:
                            search_params[f"{isin_col}"] = f"eq.{query.isin}"
                        else:
                            continue
                    elif query.emisor and query.tipo_instrumento and query.emisor == query.tipo_instrumento:
                        # Búsqueda por nemotécnico
                        nemotecnico = query.emisor
                        logger.info(f"Buscando nemotécnico '{nemotecnico}' en Supabase. Columnas disponibles: {available_columns}")
                        
                        # Buscar en columna NEMOTECNICO primero (si existe)
                        nemotecnico_col = None
                        for col in ["NEMOTECNICO", "nemotecnico", "Nemotecnico", "NEMOTÉCNICO", "nemotécnico"]:
                            if col in available_columns:
                                nemotecnico_col = col
                                break
                        
                        # Si no hay columna nemotécnico, buscar en EMISION/emisor
                        if not nemotecnico_col:
                            for col in ["EMISION", "emisor", "EMISOR", "EMISOR_NOMBRE"]:
                                if col in available_columns:
                                    nemotecnico_col = col
                                    break
                        
                        # Si aún no encontramos, buscar en tipo_instrumento
                        if not nemotecnico_col:
                            for col in ["TIPO_ACTIVO", "tipo_instrumento", "TIPO_INSTRUMENTO", "TIPO"]:
                                if col in available_columns:
                                    nemotecnico_col = col
                                    break
                        
                        if nemotecnico_col:
                            # PostgREST: sintaxis correcta para búsquedas con comodines
                            # Usar ilike con % en lugar de * (PostgREST espera % para comodines)
                            # Sintaxis: col=ilike.%texto%
                            search_params[f"{nemotecnico_col}"] = f"ilike.%{nemotecnico}%"
                            logger.info(f"Buscando nemotécnico '{nemotecnico}' en columna '{nemotecnico_col}' con ilike.%{nemotecnico}%")
                        else:
                            logger.warning(f"No se encontró columna para buscar nemotécnico. Columnas disponibles: {available_columns}")
                            continue
                    else:
                        continue
                    
                    if not search_params:
                        continue
                    
                    # Consultar Supabase (pasar solo el nombre de la tabla, no la URL completa)
                    params = {
                        "select": "*",
                        "limit": "100"
                    }
                    params.update(search_params)
                    
                    # Agregar filtro de fecha de valoración si existe
                    fecha_col = None
                    for col in ["FECHA_VALORACION", "fecha_valoracion", "fecha", "date"]:
                        if col in available_columns:
                            fecha_col = col
                            break
                    
                    if query.fecha and fecha_col:
                        params[f"{fecha_col}"] = f"eq.{query.fecha.isoformat()}"
                    
                    # Agregar filtro de fecha de vencimiento si existe
                    if query.fecha_vencimiento:
                        vencimiento_col = None
                        for col in ["VENCIMIENTO", "fecha_vencimiento", "FECHA_VENCIMIENTO", "vencimiento"]:
                            if col in available_columns:
                                vencimiento_col = col
                                break
                        
                        if vencimiento_col:
                            params[f"{vencimiento_col}"] = f"eq.{query.fecha_vencimiento.isoformat()}"
                    
                    # Agregar filtro de cupón/tasa facial si existe
                    if query.cupon is not None:
                        cupon_col = None
                        for col in ["TASA_FACIAL", "tasa_facial", "cupon", "CUPON", "TASA", "tasa"]:
                            if col in available_columns:
                                cupon_col = col
                                break
                        
                        if cupon_col:
                            # PostgREST: para rangos, usar sintaxis: col=gte.X&col=lte.Y
                            # Pero httpx maneja esto automáticamente si pasamos una lista
                            # Alternativa: usar and() en PostgREST
                            # Por ahora, filtrar después de obtener los datos (más simple)
                            # Guardar el valor para filtrar después
                            logger.info(f"Filtrando por cupón/tasa facial: {query.cupon} (rango: {query.cupon - 0.01} - {query.cupon + 0.01})")
                            # Nota: El filtrado se hará después de obtener los datos de Supabase
                    
                    # Pasar solo el nombre de la tabla, _make_request construye la URL
                    logger.info(f"Consultando {table_name} con parámetros: {params}")
                    response = supabase._make_request("GET", table_name, params=params)
                    
                    if response:
                        logger.info(f"Respuesta de Supabase recibida: {len(response) if isinstance(response, list) else 'no es lista'}")
                        # Convertir respuesta de Supabase a DataFrame y procesar
                        df = pd.DataFrame(response)
                        logger.info(f"DataFrame creado con {len(df)} filas y {len(df.columns)} columnas")
                        if not df.empty:
                            # Determinar descripción de búsqueda para el log
                            if query.isin:
                                search_desc = f"ISIN {query.isin}"
                            elif query.emisor and query.tipo_instrumento and query.emisor == query.tipo_instrumento:
                                search_desc = f"nemotécnico {query.emisor}"
                            else:
                                search_desc = "criterios especificados"
                            logger.info(f"Se encontraron {len(df)} registros en {table_name} para {search_desc}")
                            
                            # Normalizar y procesar
                            df_normalized = ingestion_service.normalize_column_names(df, provider)
                            
                            # Filtrar por cupón/tasa facial si se especificó (con tolerancia por redondeo)
                            if query.cupon is not None:
                                # Buscar columna de cupón (puede estar normalizada o no)
                                cupon_col = None
                                for col_name in ["cupon", "CUPON", "TASA_FACIAL", "tasa_facial", "Tasa Facial", "Cupón"]:
                                    if col_name in df_normalized.columns:
                                        cupon_col = col_name
                                        break
                                
                                if cupon_col:
                                    cupon_min = query.cupon - 0.01
                                    cupon_max = query.cupon + 0.01
                                    # Convertir a numérico si es necesario
                                    df_normalized[cupon_col] = pd.to_numeric(df_normalized[cupon_col], errors='coerce')
                                    mask = (df_normalized[cupon_col] >= cupon_min) & (df_normalized[cupon_col] <= cupon_max)
                                    registros_antes = len(df_normalized)
                                    df_normalized = df_normalized[mask]
                                    registros_despues = len(df_normalized)
                                    logger.info(f"Filtrado por cupón {query.cupon} (rango: {cupon_min} - {cupon_max}): {registros_antes} → {registros_despues} registros")
                                else:
                                    logger.warning(f"No se encontró columna de cupón para filtrar. Columnas disponibles: {list(df_normalized.columns)}")
                            
                            # Si no hay fecha especificada, usar la fecha más reciente de los datos
                            if not query.fecha:
                                # Intentar obtener la fecha de los datos
                                fecha_cols = ["fecha", "FECHA_VALORACION", "fecha_valoracion"]
                                fecha_valoracion = None
                                for col in fecha_cols:
                                    if col in df_normalized.columns:
                                        try:
                                            # Obtener la fecha más reciente
                                            fechas = pd.to_datetime(df_normalized[col], errors='coerce')
                                            fecha_valoracion = fechas.max().date() if not fechas.empty else None
                                            if fecha_valoracion:
                                                break
                                        except:
                                            continue
                                
                                if not fecha_valoracion:
                                    fecha_valoracion = date.today()
                            else:
                                fecha_valoracion = query.fecha
                            
                            logger.info(f"Usando fecha de valoración: {fecha_valoracion}")
                            
                            valuations = ingestion_service.process_dataframe(
                                df_normalized, provider, fecha_valoracion, "consulta_directa"
                            )
                            
                            logger.info(f"Se procesaron {len(valuations)} valoraciones de {provider.value} antes de filtrar por cupón")
                            
                            # Aplicar filtro de cupón también a los objetos Valuation (por si el filtro del DataFrame no fue suficiente)
                            if query.cupon is not None:
                                cupon_min = query.cupon - 0.01
                                cupon_max = query.cupon + 0.01
                                valuations_filtradas = [
                                    v for v in valuations 
                                    if v.cupon is not None 
                                    and cupon_min <= v.cupon <= cupon_max
                                ]
                                logger.info(f"Filtrado por cupón {query.cupon} en objetos Valuation: {len(valuations)} → {len(valuations_filtradas)}")
                                valuations = valuations_filtradas
                            
                            logger.info(f"Se procesaron {len(valuations)} valoraciones de {provider.value} después de todos los filtros")
                            all_valuations.extend(valuations)
                            
                            # Guardar en BD local para futuras consultas
                            for v in valuations:
                                existing = self.db.query(Valuation).filter(
                                    and_(
                                        Valuation.isin == v.isin,
                                        Valuation.fecha == v.fecha,
                                        Valuation.proveedor == v.proveedor
                                    )
                                ).first()
                                if not existing:
                                    self.db.add(v)
                            
                            self.db.commit()
                except Exception as e:
                    logger.warning(f"Error consultando {provider.value} en Supabase: {str(e)}")
                    continue
            
            return all_valuations
        except Exception as e:
            logger.error(f"Error en consulta directa a Supabase: {str(e)}")
            return []
    
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






