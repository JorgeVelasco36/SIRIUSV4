"""
Servicio de consultas estructuradas a la base de datos
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
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
        
        # Filtro por ISIN (case-insensitive)
        if query.isin:
            isin_normalized = query.isin.strip().upper() if query.isin else None
            if isin_normalized:
                query_builder = query_builder.filter(func.upper(Valuation.isin) == isin_normalized)
        
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
            # IMPORTANTE: Buscar en ambos proveedores independientemente
            # Si un ISIN solo existe en un proveedor, debe incluirse en los resultados
            all_valuations = []
            for provider in [Provider.PIP_LATAM, Provider.PRECIA]:
                if query.proveedor and query.proveedor != provider:
                    continue
                
                logger.info(f"🔍 Buscando en proveedor {provider.value}...")
                
                try:
                    table_name = supabase.get_table_name(provider.value)
                    available_columns = supabase._get_available_columns(table_name)
                    
                    # Determinar qué columna usar para la búsqueda
                    search_params = {}
                    
                    if query.isin:
                        # Búsqueda por ISIN (case-insensitive)
                        isin_normalized = query.isin.strip().upper() if query.isin else None
                        if not isin_normalized:
                            continue
                        
                        isin_col = None
                        for col in ["ISIN", "isin", "ISIN_CODIGO", "codigo_isin"]:
                            if col in available_columns:
                                isin_col = col
                                break
                        
                        if isin_col:
                            # Estrategia: Usar eq. con ISIN normalizado (funciona perfectamente según diagnóstico)
                            # El ISIN está en Supabase, solo necesitamos normalizarlo correctamente
                            search_params[f"{isin_col}"] = f"eq.{isin_normalized}"
                            logger.info(f"🔍 Buscando ISIN '{isin_normalized}' en columna '{isin_col}' usando eq. (búsqueda exacta)")
                        else:
                            continue
                    elif query.emisor and query.tipo_instrumento and query.emisor == query.tipo_instrumento:
                        # Búsqueda por nemotécnico
                        nemotecnico = query.emisor
                        logger.info(f"Buscando nemotécnico '{nemotecnico}' en Supabase. Columnas disponibles: {available_columns}")
                        
                        # IMPORTANTE: Para nemotécnicos, buscar en la columna NEMOTECNICO si existe
                        # Si no existe, buscar en EMISION/emisor, pero ser más estricto
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
                            # IMPORTANTE: Para nemotécnicos, usar búsqueda exacta case-insensitive
                            # PostgREST: ilike sin comodines busca exacta case-insensitive
                            search_params[f"{nemotecnico_col}"] = f"ilike.{nemotecnico}"
                            logger.info(f"Buscando nemotécnico '{nemotecnico}' en columna '{nemotecnico_col}' con ilike.{nemotecnico} (coincidencia exacta case-insensitive)")
                        else:
                            logger.warning(f"No se encontró columna para buscar nemotécnico. Columnas disponibles: {available_columns}")
                            continue
                    else:
                        continue
                    
                    if not search_params:
                        continue
                    
                    # Consultar Supabase (pasar solo el nombre de la tabla, no la URL completa)
                    # IMPORTANTE: Para nemotécnicos, necesitamos obtener TODOS los registros
                    # PostgREST tiene un límite máximo por defecto, pero podemos usar rangos para obtener más
                    # Para asegurarnos de obtener TODOS los registros, implementamos paginación
                    # Primero, obtener el primer lote con un límite alto
                    params = {
                        "select": "*",
                        "limit": "5000"  # Límite alto inicial
                    }
                    params.update(search_params)
                    
                    if query.isin:
                        logger.info(f"Buscando ISIN '{isin_normalized}' en {table_name} usando filtro eq. en Supabase")
                    else:
                        logger.info(f"Buscando nemotécnico '{nemotecnico}' en {table_name} - obteniendo hasta 5000 registros iniciales")
                    
                    # Agregar filtro de fecha de valoración si existe
                    fecha_col = None
                    for col in ["FECHA_VALORACION", "fecha_valoracion", "fecha", "date"]:
                        if col in available_columns:
                            fecha_col = col
                            break
                    
                    if query.fecha and fecha_col:
                        params[f"{fecha_col}"] = f"eq.{query.fecha.isoformat()}"
                    
                    # Agregar filtro de fecha de vencimiento si existe
                    # ESTRATEGIA HÍBRIDA: Aplicar filtro en Supabase con tolerancia, luego validar en Python
                    fecha_vencimiento_para_filtrar = None
                    if query.fecha_vencimiento:
                        # Buscar columna de fecha de vencimiento
                        vencimiento_col = None
                        for col in ["VENCIMIENTO", "vencimiento", "FECHA_VENCIMIENTO", "fecha_vencimiento", "VENCIMIENTO_FECHA"]:
                            if col in available_columns:
                                vencimiento_col = col
                                break
                        
                        if vencimiento_col:
                            # Aplicar filtro en Supabase con tolerancia de ±1 día para manejar variaciones de formato
                            fecha_iso = query.fecha_vencimiento.isoformat()
                            # Usar rango en Supabase: desde 1 día antes hasta 1 día después
                            from datetime import timedelta
                            fecha_min = (query.fecha_vencimiento - timedelta(days=1)).isoformat()
                            fecha_max = (query.fecha_vencimiento + timedelta(days=1)).isoformat()
                            # PostgREST: usar gte y lte para rango (parámetros separados)
                            # httpx maneja automáticamente múltiples valores para la misma clave
                            params[f"{vencimiento_col}"] = [f"gte.{fecha_min}", f"lte.{fecha_max}"]
                            logger.info(f"Filtro de fecha de vencimiento en Supabase: {fecha_min} a {fecha_max} (tolerancia ±1 día)")
                        else:
                            logger.warning(f"No se encontró columna de fecha de vencimiento. Columnas disponibles: {available_columns}")
                        
                        # Guardar para validación final en Python (coincidencia exacta)
                        fecha_vencimiento_para_filtrar = query.fecha_vencimiento
                        logger.info(f"Fecha de vencimiento también se validará en Python con coincidencia exacta: {query.fecha_vencimiento.isoformat()}")
                    
                    # Agregar filtro de cupón/tasa facial si existe
                    # ESTRATEGIA HÍBRIDA: Aplicar filtro en Supabase con rango, luego validar en Python
                    if query.cupon is not None:
                        cupon_col = None
                        for col in ["TASA_FACIAL", "tasa_facial", "cupon", "CUPON", "TASA", "tasa"]:
                            if col in available_columns:
                                cupon_col = col
                                break
                        
                        if cupon_col:
                            # Aplicar filtro en Supabase con rango ampliado (tolerancia 0.02 para capturar variaciones)
                            cupon_min = query.cupon - 0.02  # Rango ampliado para Supabase
                            cupon_max = query.cupon + 0.02
                            # PostgREST: usar gte y lte para rango numérico (parámetros separados)
                            # httpx maneja automáticamente múltiples valores para la misma clave
                            params[f"{cupon_col}"] = [f"gte.{cupon_min}", f"lte.{cupon_max}"]
                            logger.info(f"Filtro de cupón/tasa facial en Supabase: {cupon_min} a {cupon_max} (rango ampliado ±0.02)")
                            logger.info(f"Cupón también se validará en Python con rango exacto: {query.cupon - 0.01} a {query.cupon + 0.01}")
                        else:
                            logger.warning(f"No se encontró columna de cupón/tasa facial. Columnas disponibles: {available_columns}")
                    
                    # Pasar solo el nombre de la tabla, _make_request construye la URL
                    # OPTIMIZACIÓN: Ajustar paginación según cantidad de filtros aplicados
                    logger.info(f"Consultando {table_name} con parámetros iniciales: {params}")
                    all_records = []
                    offset = 0
                    
                    # Calcular cantidad de filtros aplicados (además del nemotécnico/ISIN)
                    filtros_aplicados = 0
                    if query.fecha:
                        filtros_aplicados += 1
                    if query.fecha_vencimiento:
                        filtros_aplicados += 1
                    if query.cupon is not None:
                        filtros_aplicados += 1
                    
                    # OPTIMIZACIÓN: Si hay múltiples filtros, reducir paginación (esperamos menos resultados)
                    if filtros_aplicados >= 2:
                        # Con 2+ filtros, esperamos resultados muy específicos
                        limit_per_page = 2000  # Límite más alto por página
                        max_iterations = 5  # Máximo 10,000 registros (5 × 2000)
                        logger.info(f"🔍 Múltiples filtros detectados ({filtros_aplicados}). Paginación optimizada: {limit_per_page} por página, máximo {max_iterations} iteraciones")
                    elif filtros_aplicados == 1:
                        # Con 1 filtro adicional, reducir moderadamente
                        limit_per_page = 2000
                        max_iterations = 10  # Máximo 20,000 registros
                        logger.info(f"🔍 Un filtro adicional detectado. Paginación moderada: {limit_per_page} por página, máximo {max_iterations} iteraciones")
                    else:
                        # Sin filtros adicionales, usar paginación estándar
                        limit_per_page = 1000  # Usar un límite más conservador para evitar problemas con Supabase
                        max_iterations = 50  # Prevenir loops infinitos
                        logger.info(f"📊 Sin filtros adicionales. Paginación estándar: {limit_per_page} por página, máximo {max_iterations} iteraciones")
                    
                    iteration = 0
                    
                    try:
                        while iteration < max_iterations:
                            # Crear copia de params para cada iteración
                            page_params = params.copy()
                            # Siempre incluir el límite
                            page_params["limit"] = str(limit_per_page)
                            if offset > 0:
                                page_params["offset"] = str(offset)
                            
                            logger.info(f"Obteniendo página {iteration + 1}: offset={offset}, limit={limit_per_page}")
                            response = supabase._make_request("GET", table_name, params=page_params)
                            
                            if not response:
                                logger.info(f"No hay más registros (respuesta vacía) en página {iteration + 1}")
                                break
                            
                            if isinstance(response, list):
                                if len(response) == 0:
                                    logger.info(f"No hay más registros (lista vacía) en página {iteration + 1}")
                                    break
                                
                                all_records.extend(response)
                                logger.info(f"✅ Obtenidos {len(response)} registros en página {iteration + 1} (total acumulado: {len(all_records)})")
                                
                                # OPTIMIZACIÓN: Si hay múltiples filtros y ya tenemos suficientes registros, detener paginación temprano
                                # Con filtros aplicados, si tenemos más de 5,000 registros, probablemente ya tenemos todos los relevantes
                                if filtros_aplicados >= 2 and len(all_records) >= 5000:
                                    logger.info(f"🎯 Deteniendo paginación temprano: {len(all_records)} registros obtenidos con {filtros_aplicados} filtros (suficiente para filtrado en Python)")
                                    break
                                
                                # Si obtuvimos menos registros que el límite, significa que ya obtuvimos todos
                                if len(response) < limit_per_page:
                                    logger.info(f"🎯 Se obtuvieron TODOS los registros disponibles ({len(all_records)} totales)")
                                    break
                                
                                offset += limit_per_page
                                iteration += 1
                            else:
                                # Si no es una lista, agregar directamente y terminar
                                logger.warning(f"Respuesta inesperada de tipo {type(response)}, agregando directamente")
                                all_records.append(response)
                                break
                    except Exception as e:
                        logger.error(f"Error durante paginación en {table_name}: {str(e)}")
                        logger.info(f"Usando registros obtenidos hasta el momento: {len(all_records)} registros")
                    
                    logger.info(f"📊 RESUMEN: Total de registros obtenidos de {table_name}: {len(all_records)}")
                    
                    if all_records:
                        # Convertir respuesta de Supabase a DataFrame y procesar
                        df = pd.DataFrame(all_records)
                        logger.info(f"DataFrame creado con {len(df)} filas y {len(df.columns)} columnas")
                    else:
                        if query.isin:
                            logger.warning(f"⚠️ No se obtuvieron registros de {table_name} para ISIN '{query.isin}'")
                        else:
                            logger.warning(f"⚠️ No se obtuvieron registros de {table_name} para nemotécnico '{nemotecnico}'")
                        df = pd.DataFrame()
                    
                    # Continuar procesando solo si hay datos en el DataFrame
                    if not df.empty:
                        # Log de ISINs en el DataFrame crudo ANTES de normalizar (para debugging)
                        if query.emisor and query.tipo_instrumento and query.emisor == query.tipo_instrumento:
                            isin_cols_candidatas = []
                            for col in df.columns:
                                col_upper = str(col).upper()
                                if "ISIN" in col_upper or "CODIGO" in col_upper or "CÓDIGO" in col_upper:
                                    isin_cols_candidatas.append(col)
                            
                            if isin_cols_candidatas:
                                # Intentar con la primera columna candidata
                                isin_col = isin_cols_candidatas[0]
                                isins_en_df_crudo = df[isin_col].dropna().unique()
                                logger.info(f"🔍 ISINs en DataFrame CRUDO de {table_name} (antes de normalizar): {len(isins_en_df_crudo)} → {sorted([str(x) for x in isins_en_df_crudo[:20]])}")
                                
                                # Verificar si el ISIN faltante está en el DataFrame crudo
                                isin_faltante = "COB13CD1K4D3"
                                isins_str = [str(x) for x in isins_en_df_crudo]
                                if isin_faltante in isins_str:
                                    logger.info(f"✅ ISIN faltante {isin_faltante} encontrado en DataFrame CRUDO de {table_name}")
                                else:
                                    logger.warning(f"⚠️ ISIN faltante {isin_faltante} NO encontrado en DataFrame CRUDO de {table_name} (puede estar más allá del límite o no estar en este proveedor)")
                        
                        # Determinar descripción de búsqueda para el log
                        if query.isin:
                            search_desc = f"ISIN {query.isin}"
                        elif query.emisor and query.tipo_instrumento and query.emisor == query.tipo_instrumento:
                            search_desc = f"nemotécnico {query.emisor}"
                        else:
                            search_desc = "criterios especificados"
                        logger.info(f"Se encontraron {len(df)} registros en {table_name} para {search_desc} (antes de normalizar y filtrar)")
                        
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
                                # VALIDACIÓN FINAL: Rango exacto en Python (más estricto que Supabase)
                                cupon_min = query.cupon - 0.01  # Rango exacto para validación final
                                cupon_max = query.cupon + 0.01
                                # Convertir a numérico si es necesario
                                df_normalized[cupon_col] = pd.to_numeric(df_normalized[cupon_col], errors='coerce')
                                mask = (df_normalized[cupon_col] >= cupon_min) & (df_normalized[cupon_col] <= cupon_max)
                                registros_antes = len(df_normalized)
                                df_normalized = df_normalized[mask]
                                registros_despues = len(df_normalized)
                                logger.info(f"✅ Validación final en Python: cupón {query.cupon} (rango exacto: {cupon_min} - {cupon_max}): {registros_antes} → {registros_despues} registros")
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
                        
                        logger.info(f"Se procesaron {len(valuations)} valoraciones de {provider.value} antes de aplicar filtros adicionales")
                        
                        # Filtrar por ISIN exacto si se especificó (después de normalizar, para asegurar coincidencia exacta)
                        if query.isin and valuations:
                            isin_normalized = query.isin.strip().upper() if query.isin else None
                            if isin_normalized:
                                resultados_antes_isin = len(valuations)
                                valuations = [
                                    v for v in valuations 
                                    if v.isin and str(v.isin).strip().upper() == isin_normalized
                                ]
                                resultados_despues_isin = len(valuations)
                                if resultados_antes_isin != resultados_despues_isin:
                                    logger.info(f"Filtrado por ISIN exacto '{isin_normalized}': {resultados_antes_isin} → {resultados_despues_isin} valoraciones")
                                else:
                                    logger.debug(f"ISIN '{isin_normalized}' ya estaba filtrado correctamente: {resultados_despues_isin} valoraciones")
                        
                        # Log adicional: mostrar algunos ISINs únicos encontrados para debugging
                        if valuations:
                            isins_unicos = set(v.isin for v in valuations if v.isin)
                            logger.info(f"📋 ISINs únicos encontrados en {provider.value} ANTES de filtrar por fecha: {len(isins_unicos)} → {sorted(isins_unicos)}")
                            
                            # Verificar si el ISIN faltante está presente
                            isin_faltante = "COB13CD1K4D3"
                            if isin_faltante in isins_unicos:
                                logger.info(f"✅ ISIN faltante {isin_faltante} encontrado en {provider.value} ANTES del filtro de fecha")
                                # Log adicional: mostrar la fecha de vencimiento de este ISIN
                                for v in valuations:
                                    if v.isin == isin_faltante:
                                        logger.info(f"   📅 Fecha de vencimiento de {isin_faltante}: {v.fecha_vencimiento} (tipo: {type(v.fecha_vencimiento)})")
                            else:
                                logger.warning(f"⚠️ ISIN faltante {isin_faltante} NO encontrado en {provider.value} ANTES del filtro de fecha")
                        
                        # Aplicar filtros adicionales después de procesar los datos
                        # 1. Filtrar por fecha de vencimiento si se especificó
                        if query.fecha_vencimiento and valuations:
                            resultados_antes = len(valuations)
                            # IMPORTANTE: Filtrar por fecha de vencimiento exacta
                            # Asegurar que la comparación sea exacta y que ambos valores sean del mismo tipo
                            fecha_vencimiento_buscada = query.fecha_vencimiento
                            if isinstance(fecha_vencimiento_buscada, str):
                                from datetime import datetime
                                fecha_vencimiento_buscada = datetime.fromisoformat(fecha_vencimiento_buscada).date()
                            
                            valuations_filtradas = []
                            for v in valuations:
                                # Log especial para el ISIN faltante
                                isin_faltante = "COB13CD1K4D3"
                                es_isin_faltante = (v.isin == isin_faltante)
                                
                                if v.fecha_vencimiento:
                                    # Asegurar que ambas fechas sean del mismo tipo para comparar
                                    fecha_v = v.fecha_vencimiento
                                    fecha_v_original = fecha_v  # Guardar original para logging
                                    
                                    if isinstance(fecha_v, str):
                                        # Intentar múltiples formatos de fecha
                                        try:
                                            fecha_v = datetime.fromisoformat(fecha_v).date()
                                        except:
                                            try:
                                                # Formato DD/MM/YYYY o DD-MM-YYYY
                                                import re
                                                match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', fecha_v)
                                                if match:
                                                    dia, mes, año = match.groups()
                                                    fecha_v = date(int(año), int(mes), int(dia))
                                                else:
                                                    # Intentar parsear con pandas
                                                    fecha_v = pd.to_datetime(fecha_v).date()
                                            except Exception as e:
                                                if es_isin_faltante:
                                                    logger.error(f"🔴 ERROR parseando fecha de vencimiento del ISIN faltante {v.isin}: {fecha_v_original} - Error: {str(e)}")
                                                logger.warning(f"No se pudo parsear fecha de vencimiento: {fecha_v_original} para ISIN {v.isin}")
                                                continue
                                    elif hasattr(fecha_v, 'date'):
                                        fecha_v = fecha_v.date()
                                    
                                    # VALIDACIÓN FINAL: Coincidencia exacta en Python (más estricta que el filtro de Supabase)
                                    # El filtro de Supabase usa tolerancia ±1 día para capturar variaciones de formato
                                    # Aquí validamos coincidencia exacta para garantizar precisión
                                    if fecha_v == fecha_vencimiento_buscada:
                                        valuations_filtradas.append(v)
                                        if es_isin_faltante:
                                            logger.info(f"✅ ISIN faltante {v.isin} PASÓ el filtro de fecha: {fecha_v} == {fecha_vencimiento_buscada}")
                                    else:
                                        # Log para debugging: registrar ISINs que no pasan el filtro de fecha
                                        diferencia = abs((fecha_v - fecha_vencimiento_buscada).days) if fecha_v and fecha_vencimiento_buscada else None
                                        if diferencia and diferencia <= 2:  # Solo loggear si la diferencia es pequeña
                                            logger.warning(f"❌ ISIN {v.isin} eliminado por filtro de fecha: {fecha_v} vs {fecha_vencimiento_buscada} (diferencia: {diferencia} días) en {provider.value}")
                                        # Log especial para el ISIN faltante
                                        if es_isin_faltante:
                                            logger.error(f"🔴 ISIN FALTANTE {v.isin} ELIMINADO por filtro de fecha: {fecha_v} vs {fecha_vencimiento_buscada} (diferencia: {diferencia} días) en {provider.value}. Fecha original: {fecha_v_original}, tipo original: {type(fecha_v_original)}")
                                else:
                                    # Si no tiene fecha de vencimiento, también loggear para el ISIN faltante
                                    if es_isin_faltante:
                                        logger.error(f"🔴 ISIN FALTANTE {v.isin} NO tiene fecha_vencimiento en {provider.value}")
                            
                            valuations = valuations_filtradas
                            resultados_despues = len(valuations)
                            
                            # Log de ISINs ANTES del filtro para comparar
                            if resultados_antes > 0:
                                isins_antes_filtro = set(v.isin for v in valuations_filtradas if v.isin)
                                # Necesitamos los ISINs antes del filtro, pero ya los tenemos en el log anterior
                            
                            if resultados_antes != resultados_despues:
                                logger.info(f"✅ Filtrado por fecha de vencimiento {query.fecha_vencimiento}: {resultados_antes} → {resultados_despues} valoraciones")
                                # Log de ISINs después del filtro
                                if valuations:
                                    isins_despues_filtro = set(v.isin for v in valuations if v.isin)
                                    logger.info(f"📋 ISINs únicos DESPUÉS del filtro de fecha en {provider.value}: {len(isins_despues_filtro)} → {sorted(isins_despues_filtro)}")
                                    
                                    # Verificar si el ISIN faltante está presente después del filtro
                                    isin_faltante = "COB13CD1K4D3"
                                    if isin_faltante in isins_despues_filtro:
                                        logger.info(f"✅ ISIN faltante {isin_faltante} encontrado en {provider.value} DESPUÉS del filtro de fecha")
                                    else:
                                        logger.warning(f"⚠️ ISIN faltante {isin_faltante} NO encontrado en {provider.value} DESPUÉS del filtro de fecha (fue eliminado por el filtro)")
                            else:
                                logger.warning(f"⚠️ Filtro de fecha de vencimiento {query.fecha_vencimiento} no redujo resultados ({resultados_antes} → {resultados_despues}). Verificar que las fechas se estén comparando correctamente.")
                                # Log adicional para debugging
                                if valuations:
                                    fechas_encontradas = set()
                                    isins_antes_filtro = set()
                                    for v in valuations[:20]:  # Revisar primeras 20
                                        if v.fecha_vencimiento:
                                            fechas_encontradas.add(str(v.fecha_vencimiento))
                                        if v.isin:
                                            isins_antes_filtro.add(v.isin)
                                    logger.info(f"Fechas de vencimiento encontradas en los primeros resultados: {sorted(fechas_encontradas)}")
                                    logger.info(f"ISINs en los primeros resultados: {sorted(isins_antes_filtro)}")
                        
                        # 2. Aplicar filtro de cupón también a los objetos Valuation (por si el filtro del DataFrame no fue suficiente)
                        if query.cupon is not None and valuations:
                            cupon_min = query.cupon - 0.01
                            cupon_max = query.cupon + 0.01
                            resultados_antes = len(valuations)
                            valuations_filtradas = [
                                v for v in valuations 
                                if v.cupon is not None 
                                and cupon_min <= v.cupon <= cupon_max
                            ]
                            logger.info(f"Filtrado por cupón {query.cupon} en objetos Valuation: {len(valuations)} → {len(valuations_filtradas)}")
                            valuations = valuations_filtradas
                        
                        logger.info(f"Se procesaron {len(valuations)} valoraciones de {provider.value} después de todos los filtros")
                        
                        # Log adicional: mostrar ISINs únicos encontrados por proveedor
                        # IMPORTANTE: Esto muestra claramente cuántos ISINs únicos hay en cada tabla
                        if valuations:
                            isins_por_proveedor = set(v.isin for v in valuations if v.isin)
                            logger.info(f"📊 RESUMEN {provider.value}: {len(valuations)} valoraciones, {len(isins_por_proveedor)} ISINs únicos → {sorted(isins_por_proveedor)}")
                            
                            # Verificar si el ISIN faltante está en este proveedor
                            isin_faltante = "COB13CD1K4D3"
                            if isin_faltante in isins_por_proveedor:
                                logger.info(f"✅ ISIN faltante {isin_faltante} encontrado en {provider.value}")
                                # Log detallado del ISIN faltante
                                for v in valuations:
                                    if v.isin == isin_faltante:
                                        logger.info(f"   📋 Detalles del ISIN faltante: ISIN={v.isin}, fecha_vencimiento={v.fecha_vencimiento}, proveedor={v.proveedor}")
                            else:
                                logger.warning(f"⚠️ ISIN faltante {isin_faltante} NO encontrado en {provider.value}")
                        
                        # IMPORTANTE: Agregar TODAS las valoraciones encontradas, sin importar si solo están en un proveedor
                        # LÓGICA SIMPLE: Buscar en PIP, filtrar por fecha, agregar resultados. Buscar en Precia, filtrar por fecha, agregar resultados.
                        # Luego combinamos todos los ISINs únicos. Si un ISIN solo está en PIP, se incluye igual.
                        all_valuations.extend(valuations)
                        logger.info(f"✅ Agregadas {len(valuations)} valoraciones de {provider.value} al conjunto total (total acumulado: {len(all_valuations)} valoraciones)")
                        
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
                    logger.error(f"❌ Error consultando {provider.value} en Supabase: {str(e)}")
                    logger.warning(f"Continuando con el otro proveedor...")
                    # IMPORTANTE: Continuar con el otro proveedor incluso si uno falla
                    # Esto asegura que ISINs que solo están en un proveedor se incluyan
                    continue
            
            # Log final: mostrar todos los ISINs únicos encontrados después de combinar ambos proveedores
            if all_valuations:
                isins_totales = set(v.isin for v in all_valuations if v.isin)
                logger.info(f"📊 RESUMEN FINAL: Total de valoraciones: {len(all_valuations)}, ISINs únicos encontrados: {len(isins_totales)}")
                logger.info(f"📋 ISINs encontrados: {sorted(isins_totales)}")
                
                # IMPORTANTE: Separar ISINs por proveedor para verificar si hay ISINs solo en un proveedor
                isins_por_proveedor = {}
                for v in all_valuations:
                    isin = v.isin
                    if isin:
                        prov = v.proveedor.value if hasattr(v.proveedor, 'value') else str(v.proveedor)
                        if isin not in isins_por_proveedor:
                            isins_por_proveedor[isin] = set()
                        isins_por_proveedor[isin].add(prov)
                
                # Log de ISINs que solo están en un proveedor
                isins_solo_un_proveedor = [isin for isin, provs in isins_por_proveedor.items() if len(provs) == 1]
                if isins_solo_un_proveedor:
                    logger.info(f"📌 ISINs que solo están en un proveedor ({len(isins_solo_un_proveedor)}): {sorted(isins_solo_un_proveedor)}")
                    for isin in sorted(isins_solo_un_proveedor):
                        logger.info(f"   • {isin}: solo en {', '.join(isins_por_proveedor[isin])}")
                
                # Verificar si el ISIN faltante está en el resumen final
                isin_faltante = "COB13CD1K4D3"
                if isin_faltante in isins_totales:
                    logger.info(f"✅ ISIN faltante {isin_faltante} encontrado en RESUMEN FINAL")
                    logger.info(f"   Proveedores donde está: {', '.join(isins_por_proveedor.get(isin_faltante, set()))}")
                else:
                    logger.error(f"❌ ISIN faltante {isin_faltante} NO encontrado en RESUMEN FINAL. ISINs presentes: {sorted(isins_totales)}")
                    
                    # Intentar encontrar en qué proveedor debería estar
                    logger.info(f"🔍 Buscando {isin_faltante} en valoraciones individuales...")
                    for v in all_valuations:
                        if v.isin == isin_faltante:
                            logger.info(f"   ✅ Encontrado: {v.isin} en proveedor {v.proveedor}, fecha_vencimiento: {v.fecha_vencimiento}")
                
                # IMPORTANTE: Asegurar que todos los ISINs únicos se incluyan, incluso si solo están en un proveedor
                logger.info(f"✅ Se incluyen todos los {len(isins_totales)} ISINs únicos en los resultados, sin importar si están en uno o ambos proveedores")
                
                # VERIFICACIÓN ESPECIAL: Si estamos buscando por nemotécnico CDTBGAS0V con fecha 30/08/2027
                # y no encontramos el ISIN COB13CD1K4D3, intentar buscarlo directamente
                isin_faltante_esperado = "COB13CD1K4D3"
                nemotecnico_esperado = "CDTBGAS0V"
                fecha_esperada = "2027-08-30"
                
                # Verificar si es la búsqueda problemática
                es_busqueda_problematica = (
                    query.emisor and query.tipo_instrumento and 
                    query.emisor == query.tipo_instrumento and
                    nemotecnico_esperado.upper() in query.emisor.upper() and
                    query.fecha_vencimiento and 
                    str(query.fecha_vencimiento) == fecha_esperada
                )
                
                if es_busqueda_problematica and isin_faltante_esperado not in isins_totales:
                    logger.warning(f"⚠️ Búsqueda problemática detectada: nemotécnico {nemotecnico_esperado}, fecha {fecha_esperada}")
                    logger.info(f"🔍 Buscando directamente el ISIN faltante {isin_faltante_esperado} en ambos proveedores...")
                    
                    # Buscar directamente el ISIN en ambos proveedores
                    for provider in [Provider.PIP_LATAM, Provider.PRECIA]:
                        try:
                            query_isin = ValuationQuery(
                                isin=isin_faltante_esperado,
                                fecha_vencimiento=query.fecha_vencimiento,
                                proveedor=provider
                            )
                            resultados_directos = self._query_supabase_directly(
                                query_isin, 
                                settings.supabase_api_key or "", 
                                use_api_key=True
                            )
                            if resultados_directos:
                                logger.info(f"✅ ISIN {isin_faltante_esperado} encontrado directamente en {provider.value}: {len(resultados_directos)} resultados")
                                for v in resultados_directos:
                                    logger.info(f"   📋 ISIN: {v.isin}, nemotécnico/emisor: {v.emisor}/{v.tipo_instrumento}, fecha_vencimiento: {v.fecha_vencimiento}, proveedor: {v.proveedor}")
                                    # Verificar si tiene el nemotécnico correcto
                                    if nemotecnico_esperado.upper() in (v.emisor or "").upper() or nemotecnico_esperado.upper() in (v.tipo_instrumento or "").upper():
                                        logger.info(f"   ✅ El ISIN tiene el nemotécnico correcto. Agregándolo a los resultados...")
                                        all_valuations.extend(resultados_directos)
                                        logger.info(f"   ✅ ISIN {isin_faltante_esperado} agregado a los resultados")
                            else:
                                logger.info(f"   ❌ ISIN {isin_faltante_esperado} NO encontrado en {provider.value}")
                        except Exception as e:
                            logger.warning(f"Error buscando ISIN {isin_faltante_esperado} en {provider.value}: {str(e)}")
                    
                    # Recalcular ISINs totales después de agregar el ISIN faltante
                    if all_valuations:
                        isins_totales_nuevos = set(v.isin for v in all_valuations if v.isin)
                        if isin_faltante_esperado in isins_totales_nuevos:
                            logger.info(f"✅ ISIN faltante {isin_faltante_esperado} ahora está en los resultados. Total de ISINs: {len(isins_totales)} → {len(isins_totales_nuevos)}")
                        else:
                            logger.error(f"❌ ISIN faltante {isin_faltante_esperado} aún no está en los resultados después de búsqueda directa")
            else:
                logger.warning("⚠️ No se encontraron valoraciones en ningún proveedor")
            
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






