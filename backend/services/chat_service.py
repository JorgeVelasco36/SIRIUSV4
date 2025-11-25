"""
Servicio de chat con procesamiento de lenguaje natural
"""
from openai import OpenAI
from typing import Dict, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from models import Provider
from services.query_service import QueryService
from services.knowledge_service import KnowledgeService
from schemas import ValuationQuery
from config import settings
import logging
import dateparser

logger = logging.getLogger(__name__)


class ChatService:
    """Servicio para procesar consultas en lenguaje natural y generar respuestas"""
    
    def __init__(self, db: Session, supabase_access_token: Optional[str] = None):
        self.db = db
        self.query_service = QueryService(db)
        self.supabase_access_token = supabase_access_token
        
        # Configurar OpenAI
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        
        # Contexto de conversación (última consulta y resultados)
        self.last_query = None
        self.last_results = None
        self.last_query_params = None
        
        # Inicializar servicio de conocimiento
        try:
            self.knowledge_service = KnowledgeService()
            logger.info("Servicio de conocimiento inicializado")
        except Exception as e:
            logger.warning(f"No se pudo inicializar el servicio de conocimiento: {str(e)}")
            self.knowledge_service = None
    
    def extract_intent(self, message: str) -> Dict:
        """
        Extrae intención y parámetros de una consulta en lenguaje natural
        
        Args:
            message: Mensaje del usuario
        
        Returns:
            Diccionario con intención y parámetros extraídos
        """
        # Obtener contexto del documento de conocimiento si está disponible
        knowledge_context = ""
        if self.knowledge_service:
            try:
                knowledge_context = self.knowledge_service.get_context_for_query(message)
                if knowledge_context:
                    knowledge_context = f"\n\nContexto relevante de la guía de renta fija:\n{knowledge_context[:500]}"
            except Exception as e:
                logger.warning(f"Error obteniendo contexto de conocimiento: {str(e)}")
        
        # Prompt para extracción de intención
        extraction_prompt = f"""
        Eres un experto en renta fija colombiana. Analiza la siguiente consulta sobre valoraciones de renta fija y extrae:
        
        1. Tipo de consulta: 
           - "mostrar" o "muestrame" o "dame" o "enseñame" → si el usuario pide mostrar resultados
           - "precio", "comparacion", "multiples_isins", "explicacion", "busqueda" → otros tipos
        2. ISIN(s): códigos ISIN mencionados (formato CO seguido de 10 caracteres alfanuméricos, ej: COB07CD0PY71)
           - IMPORTANTE: Si el usuario dice "con nemotecnico" o "nemotécnico", NO busques ISINs
           - IMPORTANTE: NO interpretes palabras como "mostrar", "muestrame", "dame", "enseñame" como ISINs o nemotécnicos
        3. Nemotécnico: código corto alfanumérico de 6-12 caracteres que NO es un ISIN (ej: CDTCLPS5V, TES123, etc.)
           - Si el usuario dice "con nemotecnico X" o "nemotécnico X", extrae X como nemotécnico
           - Si encuentras un nemotécnico, NO incluyas ISINs en el array "isins"
           - Los nemotécnicos son códigos de identificación de títulos más cortos que los ISINs
           - Ejemplos de nemotécnicos: CDTCLPS5V, TES123, BONOS2025, etc.
           - IMPORTANTE: NO interpretes palabras como "mostrar", "muestrame", "dame", "enseñame", "titulos", "títulos" como nemotécnicos
        4. Proveedor: "PIP_LATAM" o "PRECIA" o ambos o null si no se especifica
        5. Fecha: fecha específica o "hoy", "ayer", etc.
        6. Fecha de vencimiento: si menciona "vencimiento al DD/MM/YYYY" o "vencimiento al DD-MM-YYYY"
        7. Tasa facial/Cupón: si menciona "tasa facial", "cupón", "tasa del X%", "cupón del X%" → extraer el valor numérico
           - Ejemplo: "tasa facial es del 8.8501" → cupon: 8.8501
           - Ejemplo: "cupón del 9.5%" → cupon: 9.5
        8. Campos específicos solicitados: 
           - Si menciona "TIR", "tasa", "yield", "rendimiento" → incluir "tasa"
           - Si menciona "precio limpio" → incluir "precio_limpio"
           - Si menciona "precio sucio" → incluir "precio_sucio"
           - Si menciona "duración" → incluir "duracion"
           - Si menciona "convexidad" → incluir "convexidad"
           - Si no menciona campos específicos → dejar "fields" como []
        
        Consulta: "{message}"
        {knowledge_context}
        
        Responde SOLO con un JSON válido en este formato:
        {{
            "intent": "tipo_de_consulta",
            "isins": ["ISIN1", "ISIN2"] o [],
            "nemotecnico": "CDTCLPS5V" o null,
            "provider": "PIP_LATAM" o "PRECIA" o null,
            "date": "YYYY-MM-DD" o null,
            "fecha_vencimiento": "YYYY-MM-DD" o null,
            "cupon": 8.8501 o null,
            "fields": ["tasa", "precio_limpio", etc.] o [],
            "comparison": true/false
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente especializado en extraer información estructurada de consultas sobre renta fija. Responde SOLO con JSON válido."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            # Guardar mensaje original para análisis posterior
            result["_original_message"] = message
            
            # Si el LLM detectó un nemotécnico, marcar el tipo de búsqueda
            if result.get("nemotecnico") and not result.get("isins"):
                result["_nemotecnico"] = result["nemotecnico"]
                result["_search_type"] = "nemotecnico"
                logger.info(f"LLM detectó nemotécnico: {result['_nemotecnico']}")
            
            return result
        except Exception as e:
            logger.error(f"Error extrayendo intención: {str(e)}")
            # Fallback: búsqueda simple por palabras clave
            return self._fallback_extraction(message)
    
    def _fallback_extraction(self, message: str) -> Dict:
        """Extracción básica por palabras clave si falla el LLM"""
        message_upper = message.upper()
        message_lower = message.lower()
        
        result = {
            "intent": "busqueda",
            "isins": [],
            "provider": None,
            "date": None,
            "fields": [],
            "comparison": False,
            "_original_message": message
        }
        
        # Detectar proveedor
        if "PIP" in message_upper or "LATAM" in message_upper:
            result["provider"] = "PIP_LATAM"
        elif "PRECIA" in message_upper:
            result["provider"] = "PRECIA"
        
        # Detectar comparación
        if "COMPARA" in message_upper or "COMPARAR" in message_upper or "VS" in message_upper:
            result["intent"] = "comparacion"
            result["comparison"] = True
        
        # Detectar fecha
        if "HOY" in message_upper:
            result["date"] = date.today().isoformat()
        elif "AYER" in message_upper:
            from datetime import timedelta
            result["date"] = (date.today() - timedelta(days=1)).isoformat()
        
        # Detectar campos solicitados
        if any(word in message_lower for word in ["tir", "tasa", "yield", "rendimiento"]):
            result["fields"].append("tasa")
        if "precio limpio" in message_lower:
            result["fields"].append("precio_limpio")
        if "precio sucio" in message_lower:
            result["fields"].append("precio_sucio")
        if "duración" in message_lower or "duracion" in message_lower:
            result["fields"].append("duracion")
        if "convexidad" in message_lower:
            result["fields"].append("convexidad")
        
        # Verificar si el usuario menciona explícitamente "nemotecnico" o "nemotécnico"
        import re
        message_lower = message.lower()
        menciona_nemotecnico = "nemotecnico" in message_lower or "nemotécnico" in message_lower
        
        # Si menciona nemotécnico, buscar el código después de esa palabra
        nemotecnico_explicito = None
        if menciona_nemotecnico:
            # Buscar patrón: "nemotecnico X" o "nemotécnico X" donde X es el código
            nemotecnico_explicit_pattern = r'(?:nemotecnico|nemotécnico)\s+([A-Z0-9]{6,12})'
            match = re.search(nemotecnico_explicit_pattern, message_upper)
            if match:
                nemotecnico_explicito = match.group(1)
                result["_nemotecnico"] = nemotecnico_explicito
                result["nemotecnico"] = nemotecnico_explicito
                result["_search_type"] = "nemotecnico"
                result["isins"] = []  # Asegurar que no haya ISINs
                logger.info(f"Nemotécnico explícito detectado (fallback): {nemotecnico_explicito}")
                return result
        
        # Intentar extraer ISIN (formato CO seguido de 10 caracteres alfanuméricos)
        # Ejemplos: CO000123456, COB07CD0PY71, COT12345678
        # Patrón mejorado: CO seguido de 10 caracteres alfanuméricos
        isin_pattern = r'\bCO[A-Z0-9]{10}\b'
        isins = re.findall(isin_pattern, message_upper)
        if isins:
            result["isins"] = isins
            result["_search_type"] = "isin"
        else:
            # Buscar nemotécnicos o códigos cortos (ej: CDTCLPS5V)
            # Patrón para códigos alfanuméricos de 6-12 caracteres que NO empiecen con CO seguido de 10 caracteres
            # Los nemotécnicos NO son ISINs, son códigos más cortos
            nemotecnico_pattern = r'\b(?!CO[A-Z0-9]{10}\b)[A-Z0-9]{6,12}\b'
            nemotecnicos = re.findall(nemotecnico_pattern, message_upper)
            # Filtrar palabras comunes en español y términos financieros
            palabras_comunes = [
                'TIR', 'CDT', 'TES', 'PIP', 'PRECIA', 'LATAM', 'ISIN', 'VALORACION', 
                'VALORACION', 'TITULO', 'TITULOS', 'FECHA', 'VENCIMIENTO',
                'QUISIERA', 'SABER', 'CUAL', 'ES', 'DE', 'UN', 'UNA', 'EL', 'LA',
                'CON', 'AL', 'PARA', 'POR', 'SOBRE', 'ENTRE', 'DESDE', 'HASTA',
                'HOY', 'AYER', 'MAÑANA', 'COMPARA', 'COMPARAR', 'VS', 'VERSUS',
                'PRECIO', 'TASA', 'DURACION', 'CONVEXIDAD', 'RENDIMIENTO', 'YIELD',
                'NEMOTECNICO', 'NEMOTÉCNICO',  # Excluir la palabra misma
                'MOSTRAR', 'MUESTRAME', 'MUESTRA', 'DAME', 'DAMELOS', 'ENSEÑAME', 'ENSEÑA',  # Acciones
                'TITULOS', 'TÍTULOS', 'TITULO', 'TÍTULO', 'RESULTADOS', 'ESOS', 'ESAS'  # Palabras relacionadas con mostrar
            ]
            nemotecnicos_filtrados = [
                n for n in nemotecnicos 
                if n not in palabras_comunes 
                and not n.isdigit() 
                and len(n) >= 6  # Mínimo 6 caracteres para ser nemotécnico válido
                and not n.startswith('CO')  # Excluir códigos que empiecen con CO (probablemente ISINs mal formateados)
            ]
            if nemotecnicos_filtrados:
                # Guardar nemotécnico para búsqueda por emisor o tipo
                result["_nemotecnico"] = nemotecnicos_filtrados[0]
                result["_search_type"] = "nemotecnico"
                result["nemotecnico"] = nemotecnicos_filtrados[0]  # También en el campo principal
                logger.info(f"Nemotécnico detectado (fallback): {result['_nemotecnico']}")
        
        return result
    
    def parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parsea string de fecha a objeto date"""
        if not date_str:
            return None
        
        if date_str == "hoy" or date_str == "today":
            return date.today()
        
        if date_str == "ayer" or date_str == "yesterday":
            from datetime import timedelta
            return date.today() - timedelta(days=1)
        
        try:
            parsed = dateparser.parse(date_str)
            if parsed:
                return parsed.date()
        except:
            pass
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return None
    
    def build_query(self, extracted: Dict) -> ValuationQuery:
        """Construye objeto ValuationQuery desde parámetros extraídos"""
        fecha = self.parse_date(extracted.get("date"))
        
        # Determinar si es búsqueda por ISIN o nemotécnico
        isin = None
        isins = None
        emisor = None
        tipo_instrumento = None
        fecha_vencimiento = None
        cupon = None
        
        # Extraer cupón/tasa facial del mensaje si se menciona
        message_lower = extracted.get("_original_message", "").lower()
        if "cupon" in message_lower or "tasa facial" in message_lower or "tasa del" in message_lower:
            # Intentar extraer valor numérico de cupón/tasa facial
            import re
            # Patrones: "tasa facial es del 8.8501", "cupón del 9.5%", "tasa del 8.85", "tengo la tasa cupon, es del 8.8501%"
            cupon_patterns = [
                r'(?:tengo la tasa cup[oó]n|tasa cup[oó]n|cup[oó]n).*?es del (\d+\.?\d*)',
                r'(?:tasa facial|cup[oó]n).*?es del (\d+\.?\d*)',
                r'(?:tasa facial|cup[oó]n).*?(\d+\.?\d*)',
                r'tasa del (\d+\.?\d*)',
                r'cup[oó]n del (\d+\.?\d*)',
                r'(\d+\.?\d*)\s*%'
            ]
            for pattern in cupon_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    try:
                        cupon_val = float(match.group(1))
                        cupon = cupon_val
                        logger.info(f"Tasa facial/Cupón detectado: {cupon}")
                        break
                    except:
                        continue
        
        # Si el LLM extrajo cupon, usarlo
        if not cupon and extracted.get("cupon"):
            try:
                cupon = float(extracted.get("cupon"))
                logger.info(f"Tasa facial/Cupón del LLM: {cupon}")
            except:
                pass
        
        # Extraer fecha de vencimiento del mensaje si se menciona
        if "vencimiento" in message_lower or "vencen" in message_lower:
            # Intentar extraer fecha de vencimiento (formato DD/MM/YYYY o DD-MM-YYYY)
            import re
            fecha_venc_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
            fecha_match = re.search(fecha_venc_pattern, extracted.get("_original_message", ""))
            if fecha_match:
                try:
                    dia, mes, año = fecha_match.groups()
                    fecha_vencimiento = date(int(año), int(mes), int(dia))
                    logger.info(f"Fecha de vencimiento detectada: {fecha_vencimiento}")
                except:
                    pass
        
        # Si hay una consulta anterior y el mensaje actual solo agrega información (cupón, etc.), combinar filtros
        if self.last_query and not extracted.get("nemotecnico") and not extracted.get("isins"):
            # El usuario está refinando la búsqueda anterior
            logger.info("Combinando filtros con la consulta anterior")
            # Usar nemotécnico y fecha de vencimiento de la consulta anterior
            if self.last_query.emisor and self.last_query.tipo_instrumento:
                emisor = self.last_query.emisor
                tipo_instrumento = self.last_query.tipo_instrumento
            if self.last_query.fecha_vencimiento:
                fecha_vencimiento = self.last_query.fecha_vencimiento
            if self.last_query.isin:
                isin = self.last_query.isin
            # Si no se extrajo cupón del mensaje actual, usar el de la consulta anterior
            if not cupon and self.last_query.cupon is not None:
                cupon = self.last_query.cupon
                logger.info(f"Usando cupón de la consulta anterior: {cupon}")
        else:
            # Verificar si hay nemotécnico (del LLM o del fallback)
            nemotecnico_detectado = extracted.get("nemotecnico") or extracted.get("_nemotecnico")
            isins_detectados = extracted.get("isins", [])
            
            if nemotecnico_detectado and not isins_detectados:
                # Búsqueda por nemotécnico (NO por ISIN)
                nemotecnico = nemotecnico_detectado
                logger.info(f"Búsqueda por nemotécnico: {nemotecnico}")
                # El nemotécnico puede estar en el emisor o tipo de instrumento
                # Buscar en ambos campos usando LIKE
                emisor = nemotecnico
                # También buscar en tipo_instrumento por si acaso
                tipo_instrumento = nemotecnico
                # Asegurar que isin sea None para evitar búsqueda por ISIN
                isin = None
                isins = []
            elif isins_detectados:
                # Búsqueda por ISIN
                isins_list = isins_detectados
                if len(isins_list) > 1:
                    isins = isins_list
                elif len(isins_list) == 1:
                    isin = isins_list[0]
                # Asegurar que emisor y tipo_instrumento sean None
                emisor = None
                tipo_instrumento = None
            else:
                # No se detectó ni ISIN ni nemotécnico
                logger.warning("No se detectó ni ISIN ni nemotécnico en la consulta")
        
        return ValuationQuery(
            isin=isin,
            isins=isins,
            proveedor=Provider(extracted["provider"]) if extracted.get("provider") else None,
            fecha=fecha,
            fecha_inicio=None,  # Se puede mejorar con rangos
            fecha_fin=None,
            emisor=emisor,
            tipo_instrumento=tipo_instrumento,
            fecha_vencimiento=fecha_vencimiento,
            cupon=cupon
        )
    
    def format_valuation_table(self, valuations: List) -> str:
        """Formatea valoraciones como tabla de texto"""
        if not valuations:
            return "No se encontraron valoraciones."
        
        lines = []
        lines.append("| ISIN | Proveedor | Fecha | Precio Limpio | Precio Sucio | Tasa | Duración |")
        lines.append("|------|-----------|-------|---------------|--------------|------|----------|")
        
        for v in valuations:
            precio_limpio = f"{v.precio_limpio:.2f}" if v.precio_limpio else "N/A"
            precio_sucio = f"{v.precio_sucio:.2f}" if v.precio_sucio else "N/A"
            tasa = f"{v.tasa:.4f}" if v.tasa else "N/A"
            duracion = f"{v.duracion:.2f}" if v.duracion else "N/A"
            
            lines.append(
                f"| {v.isin} | {v.proveedor.value} | {v.fecha} | {precio_limpio} | "
                f"{precio_sucio} | {tasa} | {duracion} |"
            )
        
        return "\n".join(lines)
    
    def generate_response(self, message: str, user: Optional[str] = None) -> Dict:
        """
        Genera respuesta completa a una consulta
        
        Args:
            message: Mensaje del usuario
            user: Usuario que realiza la consulta (opcional)
        
        Returns:
            Diccionario con respuesta estructurada
        """
        try:
            # Detectar si es una acción de "mostrar" resultados
            message_lower = message.lower()
            es_accion_mostrar = any(palabra in message_lower for palabra in [
                "mostrar", "muestrame", "muestra", "dame", "damelos", "enseñame", "enseña",
                "muestrame esos", "muestrame las", "muestrame los", "dame esos", "dame las", "dame los"
            ])
            
            # Si es acción de mostrar y hay resultados de la consulta anterior, usarlos
            if es_accion_mostrar and self.last_results is not None:
                logger.info(f"Acción 'mostrar' detectada, usando {len(self.last_results)} resultados de la consulta anterior")
                answer = f"Se encontraron {len(self.last_results)} títulos que coinciden con tu búsqueda:\n\n"
                answer += self.format_valuation_table(self.last_results)
                recommendations = self._generate_general_recommendations(self.last_results)
                data = [self._valuation_to_dict(v) for v in self.last_results]
                
                return {
                    "answer": answer,
                    "data": data,
                    "recommendations": recommendations,
                    "metadata": {
                        "intent": "mostrar_resultados",
                        "query_params": self.last_query_params
                    }
                }
            
            # Extraer intención
            extracted = self.extract_intent(message)
            # Guardar mensaje original para análisis posterior
            extracted["_original_message"] = message
            extracted["_es_accion_mostrar"] = es_accion_mostrar
            
            # Construir query
            query = self.build_query(extracted)
            
            # Ejecutar consulta
            if extracted["intent"] == "comparacion" and query.isin:
                # Comparación entre proveedores
                comparison = self.query_service.compare_providers(query.isin, query.fecha)
                
                if "error" in comparison:
                    answer = f"No se encontraron datos para comparación del ISIN {query.isin}."
                    recommendations = [
                        "Verificar que el ISIN existe en la base de datos",
                        "Confirmar que hay valoraciones para la fecha solicitada",
                        "Revisar archivos de ingesta recientes"
                    ]
                    data = None
                else:
                    answer = self._format_comparison(comparison)
                    recommendations = self._generate_comparison_recommendations(comparison)
                    # Convertir comparación a lista para mantener consistencia con el schema
                    data = [comparison] if comparison else None
                
            elif query.isins or (query.isin and len(extracted.get("isins", [])) > 1):
                # Múltiples ISINs
                valuations = self.query_service.query_valuations(query, self.supabase_access_token)
                answer = f"Se encontraron {len(valuations)} valoraciones:\n\n"
                answer += self.format_valuation_table(valuations)
                recommendations = self._generate_general_recommendations(valuations)
                data = [self._valuation_to_dict(v) for v in valuations]
                
            else:
                # Consulta simple
                logger.info(f"Ejecutando consulta: isin={query.isin}, emisor={query.emisor}, tipo_instrumento={query.tipo_instrumento}, fecha_vencimiento={query.fecha_vencimiento}, cupon={query.cupon}")
                valuations = self.query_service.query_valuations(query, self.supabase_access_token)
                logger.info(f"Consulta completada: se encontraron {len(valuations)} valoraciones después de aplicar todos los filtros")
                
                # Guardar consulta y resultados para contexto de conversación
                self.last_query = query
                self.last_results = valuations
                self.last_query_params = {
                    "isin": query.isin,
                    "emisor": query.emisor,
                    "tipo_instrumento": query.tipo_instrumento,
                    "fecha_vencimiento": query.fecha_vencimiento.isoformat() if query.fecha_vencimiento else None,
                    "cupon": query.cupon
                }
                
                # Si es una acción de "mostrar", mostrar todos los resultados directamente
                if es_accion_mostrar and valuations:
                    answer = f"Se encontraron {len(valuations)} títulos que coinciden con tu búsqueda:\n\n"
                    answer += self.format_valuation_table(valuations)
                    recommendations = self._generate_general_recommendations(valuations)
                    data = [self._valuation_to_dict(v) for v in valuations]
                # Si hay múltiples resultados (más de 1), generar preguntas de refinamiento
                # Esto permite que SIRIUS interactúe con el usuario para acotar la búsqueda
                elif len(valuations) > 1:
                    logger.info(f"Hay {len(valuations)} resultados, generando preguntas de refinamiento...")
                    refinement_questions = self._generate_refinement_questions(valuations, query, extracted)
                    if refinement_questions:
                        answer = f"Se encontraron {len(valuations)} títulos que coinciden con tu búsqueda. Para acotar los resultados y darte la información precisa, necesito más detalles:\n\n"
                        answer += "\n".join(f"• {q}" for q in refinement_questions)
                        answer += "\n\nPor favor, proporciona alguna de estas características para ayudarte mejor."
                        recommendations = [
                            "Proporciona el ISIN específico si lo conoces",
                            "Indica el emisor o banco emisor",
                            "Especifica la fecha de vencimiento exacta",
                            "Menciona el tipo de instrumento si lo sabes",
                            "Puedes decir 'muestrame esos X titulos' para ver todos los resultados"
                        ]
                        data = None
                    else:
                        # Si no se pueden generar preguntas, mostrar resultados limitados
                        answer = f"Se encontraron {len(valuations)} valoraciones. Mostrando las primeras 5:\n\n"
                        answer += self.format_valuation_table(valuations[:5])
                        if len(valuations) > 5:
                            answer += f"\n\n💡 Para ver todos los resultados o acotar la búsqueda, proporciona más detalles como el ISIN específico, emisor o fecha de vencimiento."
                        recommendations = self._generate_general_recommendations(valuations[:5])
                        data = [self._valuation_to_dict(v) for v in valuations[:5]]
                
                elif not valuations:
                    # Determinar tipo de búsqueda para mensaje de error apropiado
                    is_busqueda_nemotecnico = (query.emisor and query.tipo_instrumento and 
                                             query.emisor == query.tipo_instrumento and not query.isin)
                    
                    if is_busqueda_nemotecnico:
                        # Búsqueda por nemotécnico
                        nemotecnico = query.emisor
                        answer = f"No se encontraron valoraciones para el nemotécnico {nemotecnico}."
                        if query.fecha_vencimiento:
                            answer += f" con vencimiento al {query.fecha_vencimiento.strftime('%d/%m/%Y')}"
                        answer += "."
                        
                        recommendations = [
                            "Verificar que el nemotécnico esté escrito correctamente",
                            "Confirmar que existe valoración para la fecha solicitada",
                            "Revisar que el proveedor seleccionado tenga datos disponibles",
                            "Intentar buscar por ISIN si lo conoces"
                        ]
                        data = None
                    elif query.isin:
                        # Búsqueda por ISIN
                        # Intentar buscar ISINs similares si no se encontró el exacto
                        similar_isins = []
                        if self.supabase_access_token:
                            try:
                                from services.supabase_service import SupabaseService
                                supabase = SupabaseService(access_token=self.supabase_access_token)
                                
                                # Buscar ISINs similares (que empiecen con los primeros caracteres)
                                prefix = query.isin[:6] if len(query.isin) >= 6 else query.isin
                                for table_name in [supabase.table_pip, supabase.table_precia]:
                                    try:
                                        available_columns = supabase._get_available_columns(table_name)
                                        isin_col = None
                                        for col in ["ISIN", "isin", "ISIN_CODIGO", "codigo_isin"]:
                                            if col in available_columns:
                                                isin_col = col
                                                break
                                        
                                        if isin_col:
                                            params = {
                                                "select": isin_col,
                                                f"{isin_col}": f"like.{prefix}%",
                                                "limit": "5"
                                            }
                                            response = supabase._make_request("GET", table_name, params=params)
                                            if response:
                                                for record in response:
                                                    similar_isin = record.get(isin_col, "")
                                                    if similar_isin and similar_isin.upper() != query.isin.upper():
                                                        similar_isins.append(similar_isin)
                                    except:
                                        continue
                            except Exception as e:
                                logger.warning(f"Error buscando ISINs similares: {str(e)}")
                        
                        answer = f"No se encontraron valoraciones para el ISIN {query.isin}."
                        if similar_isins:
                            answer += f"\n\nISINs similares encontrados: {', '.join(set(similar_isins[:5]))}"
                        
                        recommendations = [
                            "Verificar que el ISIN esté escrito correctamente",
                            "Confirmar que existe valoración para la fecha solicitada",
                            "Revisar que el proveedor seleccionado tenga datos disponibles"
                        ]
                        if similar_isins:
                            recommendations.insert(0, f"Verificar si el ISIN correcto es uno de los similares: {', '.join(set(similar_isins[:3]))}")
                        data = None
                    else:
                        # Búsqueda genérica sin ISIN ni nemotécnico
                        answer = "No se encontraron valoraciones con los criterios especificados."
                        recommendations = [
                            "Proporciona el ISIN o nemotécnico del título",
                            "Verifica los filtros aplicados (fecha, proveedor, etc.)",
                            "Confirma que existe valoración para los criterios solicitados"
                        ]
                        data = None
                else:
                    # Formatear respuesta precisa
                    answer = self._format_precise_response(valuations, extracted)
                    
                    # Enriquecer respuesta con conocimiento del documento si está disponible
                    if self.knowledge_service and message:
                        try:
                            answer = self.knowledge_service.enhance_response_with_knowledge(message, answer)
                        except Exception as e:
                            logger.warning(f"Error enriqueciendo respuesta con conocimiento: {str(e)}")
                    
                    # Agregar sugerencia para más información
                    answer += "\n\n💡 ¿Necesitas más información de este título?"
                    
                    recommendations = self._generate_single_recommendations(valuations[0])
                    # Convertir a lista para mantener consistencia con el schema
                    data = [self._valuation_to_dict(v) for v in valuations]
            
            # Detectar inconsistencias
            if query.isin:
                alerts = self.query_service.get_missing_data(query.isin, query.fecha)
                if alerts:
                    answer += "\n\n⚠️ **Alertas:**\n" + "\n".join(f"- {alert}" for alert in alerts)
            
            # Guardar en log
            from models import QueryLog
            log_entry = QueryLog(
                consulta=message,
                respuesta=answer[:500],  # Limitar tamaño
                usuario=user,
                isin_filtrado=query.isin,
                proveedor_filtrado=query.proveedor.value if query.proveedor else None,
                fecha_filtrada=query.fecha
            )
            self.db.add(log_entry)
            self.db.commit()
            
            # Asegurar que data sea siempre una lista o None
            if data is not None and not isinstance(data, list):
                data = [data]
            
            return {
                "answer": answer,
                "data": data,
                "recommendations": recommendations,
                "metadata": {
                    "intent": extracted["intent"],
                    "query_params": {
                        "isin": query.isin,
                        "provider": query.proveedor.value if query.proveedor else None,
                        "fecha": query.fecha.isoformat() if query.fecha else None
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return {
                "answer": f"Error procesando la consulta: {str(e)}",
                "data": None,
                "recommendations": [
                    "Verificar la sintaxis de la consulta",
                    "Contactar al equipo técnico si el error persiste",
                    "Revisar los logs del sistema para más detalles"
                ],
                "metadata": None
            }
    
    def _format_comparison(self, comparison: Dict) -> str:
        """Formatea respuesta de comparación"""
        lines = []
        lines.append(f"**Comparación de proveedores para ISIN {comparison['isin']}**")
        lines.append(f"Fecha: {comparison['fecha']}\n")
        
        if comparison["pip_latam"]:
            lines.append("**PIP Latam:**")
            pl = comparison["pip_latam"]
            lines.append(f"- Precio Limpio: {pl.get('precio_limpio', 'N/A')}")
            lines.append(f"- Tasa: {pl.get('tasa', 'N/A')}")
            lines.append(f"- Duración: {pl.get('duracion', 'N/A')}")
        
        if comparison["precia"]:
            lines.append("\n**Precia:**")
            pr = comparison["precia"]
            lines.append(f"- Precio Limpio: {pr.get('precio_limpio', 'N/A')}")
            lines.append(f"- Tasa: {pr.get('tasa', 'N/A')}")
            lines.append(f"- Duración: {pr.get('duracion', 'N/A')}")
        
        if comparison["diferencias"]:
            lines.append("\n**Diferencias (Precia - PIP Latam):**")
            diff = comparison["diferencias"]
            if "precio_limpio" in diff:
                lines.append(f"- Precio Limpio: {diff['precio_limpio']:.2f} puntos base")
            if "tasa" in diff:
                lines.append(f"- Tasa: {diff['tasa']:.4f}%")
        
        return "\n".join(lines)
    
    def _format_single_response(self, valuation, extracted: Dict) -> str:
        """Formatea respuesta para una sola valoración (deprecated - usar _format_precise_response)"""
        return self._format_precise_response([valuation], extracted)
    
    def _format_precise_response(self, valuations: List, extracted: Dict) -> str:
        """Formatea respuesta precisa mostrando solo los campos solicitados"""
        requested_fields = extracted.get("fields", [])
        message_lower = extracted.get("_original_message", "").lower() if "_original_message" in extracted else ""
        
        # Detectar campos solicitados del mensaje original si no están en extracted
        if not requested_fields:
            if any(word in message_lower for word in ["tir", "tasa", "yield", "rendimiento"]):
                requested_fields.append("tasa")
            if "precio limpio" in message_lower:
                requested_fields.append("precio_limpio")
            if "precio sucio" in message_lower:
                requested_fields.append("precio_sucio")
            if "duración" in message_lower or "duracion" in message_lower:
                requested_fields.append("duracion")
            if "convexidad" in message_lower:
                requested_fields.append("convexidad")
        
        # Si no se especificaron campos, mostrar solo tasa (TIR) por defecto para consultas de TIR
        if not requested_fields and any(word in message_lower for word in ["tir", "tasa", "yield", "rendimiento"]):
            requested_fields = ["tasa"]
        
        # Si hay múltiples valoraciones (diferentes proveedores), hacer comparación
        if len(valuations) > 1:
            pip_valuation = next((v for v in valuations if v.proveedor == Provider.PIP_LATAM), None)
            precia_valuation = next((v for v in valuations if v.proveedor == Provider.PRECIA), None)
            
            lines = []
            
            # Si solo se pregunta por TIR/tasa
            if requested_fields == ["tasa"] or (not requested_fields and any(word in message_lower for word in ["tir", "tasa", "yield", "rendimiento"])):
                result_parts = []
                if pip_valuation and pip_valuation.tasa:
                    result_parts.append(f"La TIR de Valoración en PIP es de {pip_valuation.tasa:.3f}%")
                if precia_valuation and precia_valuation.tasa:
                    if result_parts:
                        result_parts.append(f"y en Precia es de {precia_valuation.tasa:.3f}%.")
                    else:
                        result_parts.append(f"La TIR de Valoración en Precia es de {precia_valuation.tasa:.3f}%.")
                
                if result_parts:
                    lines.append(" ".join(result_parts))
                else:
                    lines.append("No se encontró información de TIR para este título.")
            else:
                # Mostrar campos solicitados para cada proveedor
                for valuation in valuations:
                    provider_name = "PIP" if valuation.proveedor == Provider.PIP_LATAM else "Precia"
                    provider_lines = [f"**{provider_name}:**"]
                    
                    for field in requested_fields:
                        if field == "tasa" and valuation.tasa:
                            provider_lines.append(f"- TIR: {valuation.tasa:.3f}%")
                        elif field == "precio_limpio" and valuation.precio_limpio:
                            provider_lines.append(f"- Precio Limpio: {valuation.precio_limpio:.2f}")
                        elif field == "precio_sucio" and valuation.precio_sucio:
                            provider_lines.append(f"- Precio Sucio: {valuation.precio_sucio:.2f}")
                        elif field == "duracion" and valuation.duracion:
                            provider_lines.append(f"- Duración: {valuation.duracion:.2f}")
                        elif field == "convexidad" and valuation.convexidad:
                            provider_lines.append(f"- Convexidad: {valuation.convexidad:.4f}")
                    
                    if len(provider_lines) > 1:  # Si hay al menos un campo además del título
                        lines.extend(provider_lines)
                        lines.append("")  # Línea en blanco entre proveedores
            
            return "\n".join(lines).strip()
        
        else:
            # Una sola valoración
            valuation = valuations[0]
            lines = []
            
            # Si solo se pregunta por TIR/tasa
            if requested_fields == ["tasa"] or (not requested_fields and "tasa" in message_lower):
                if valuation.tasa:
                    lines.append(f"La TIR de Valoración es de {valuation.tasa:.3f}%.")
                else:
                    lines.append("No se encontró información de TIR para este título.")
            else:
                # Mostrar solo campos solicitados
                if not requested_fields:
                    # Si no se especificaron campos, mostrar información básica
                    lines.append(f"**Valoración para ISIN {valuation.isin}**")
                    if valuation.tasa:
                        lines.append(f"TIR: {valuation.tasa:.3f}%")
                    if valuation.precio_limpio:
                        lines.append(f"Precio Limpio: {valuation.precio_limpio:.2f}")
                else:
                    lines.append(f"**Valoración para ISIN {valuation.isin}**")
                    for field in requested_fields:
                        if field == "tasa" and valuation.tasa:
                            lines.append(f"TIR: {valuation.tasa:.3f}%")
                        elif field == "precio_limpio" and valuation.precio_limpio:
                            lines.append(f"Precio Limpio: {valuation.precio_limpio:.2f}")
                        elif field == "precio_sucio" and valuation.precio_sucio:
                            lines.append(f"Precio Sucio: {valuation.precio_sucio:.2f}")
                        elif field == "duracion" and valuation.duracion:
                            lines.append(f"Duración: {valuation.duracion:.2f}")
                        elif field == "convexidad" and valuation.convexidad:
                            lines.append(f"Convexidad: {valuation.convexidad:.4f}")
            
            return "\n".join(lines).strip()
    
    def _valuation_to_dict(self, valuation) -> Dict:
        """Convierte objeto Valuation a diccionario (excluye campos irrelevantes)"""
        return {
            "isin": valuation.isin,
            "emisor": valuation.emisor,
            "tipo_instrumento": valuation.tipo_instrumento,
            "precio_limpio": valuation.precio_limpio,
            "precio_sucio": valuation.precio_sucio,
            "tasa": valuation.tasa,
            "duracion": valuation.duracion,
            # Excluidos: convexidad (no presenta información) y archivo_origen (irrelevante)
            "fecha": valuation.fecha.isoformat() if valuation.fecha else None,
            "proveedor": valuation.proveedor.value
        }
    
    def _generate_comparison_recommendations(self, comparison: Dict) -> List[str]:
        """Genera recomendaciones basadas en comparación"""
        recommendations = []
        
        if not comparison.get("pip_latam"):
            recommendations.append("Falta valoración en PIP Latam → Verificar ingesta de archivos de este proveedor")
        
        if not comparison.get("precia"):
            recommendations.append("Falta valoración en Precia → Verificar ingesta de archivos de este proveedor")
        
        if comparison.get("diferencias"):
            diff = comparison["diferencias"]
            if "precio_limpio" in diff:
                diff_pb = abs(diff["precio_limpio"]) * 100
                if diff_pb > 50:
                    recommendations.append(f"Diferencia significativa en precio ({diff_pb:.0f} pb) → Revisar curvas y metodologías de ambos proveedores")
                else:
                    recommendations.append(f"Diferencia moderada en precio ({diff_pb:.0f} pb) → Diferencia dentro de rangos normales")
        
        if len(recommendations) < 3:
            recommendations.append("Considerar validar con tercer proveedor si la diferencia es crítica para la operación")
        
        return recommendations[:3]
    
    def _generate_single_recommendations(self, valuation) -> List[str]:
        """Genera recomendaciones para una sola valoración"""
        recommendations = []
        
        if not valuation.precio_limpio:
            recommendations.append("Precio limpio faltante → Solicitar actualización al proveedor")
        
        if not valuation.tasa:
            recommendations.append("Tasa faltante → Verificar cálculo de yield en el proveedor")
        
        # Comparar con otro proveedor
        other_provider = Provider.PRECIA if valuation.proveedor == Provider.PIP_LATAM else Provider.PIP_LATAM
        other = self.query_service.get_latest_valuation(valuation.isin, other_provider)
        
        if other:
            if valuation.precio_limpio and other.precio_limpio:
                diff = abs(valuation.precio_limpio - other.precio_limpio) * 100
                if diff > 50:
                    recommendations.append(f"Diferencia significativa vs {other_provider.value} ({diff:.0f} pb) → Validar con proveedor")
        else:
            recommendations.append(f"No hay valoración en {other_provider.value} → Considerar ingesta de archivo de este proveedor")
        
        return recommendations[:3]
    
    def _generate_general_recommendations(self, valuations: List) -> List[str]:
        """Genera recomendaciones generales para múltiples valoraciones"""
        recommendations = []
        
        if len(valuations) == 0:
            recommendations.append("No se encontraron valoraciones → Verificar criterios de búsqueda")
            recommendations.append("Revisar archivos de ingesta recientes")
            recommendations.append("Confirmar que los ISINs existen en la base de datos")
        else:
            providers = set(v.proveedor for v in valuations)
            if len(providers) == 1:
                recommendations.append(f"Solo hay datos de {list(providers)[0].value} → Considerar ingesta del otro proveedor para comparación")
            
            dates = set(v.fecha for v in valuations)
            if len(dates) > 1:
                recommendations.append(f"Valoraciones de múltiples fechas → Verificar que se está usando la fecha correcta")
            
            recommendations.append(f"Se encontraron {len(valuations)} registros → Validar completitud de datos")
        
        return recommendations[:3]
    
    def _generate_refinement_questions(self, valuations: List, query: ValuationQuery, extracted: Dict) -> List[str]:
        """
        Genera preguntas de refinamiento cuando hay demasiados resultados
        
        Args:
            valuations: Lista de valoraciones encontradas
            query: Query original
            extracted: Parámetros extraídos del mensaje
        
        Returns:
            Lista de preguntas para refinar la búsqueda
        """
        questions = []
        message_lower = extracted.get("_original_message", "").lower()
        
        # Analizar qué información falta para acotar
        unique_isins = set(v.isin for v in valuations if v.isin)
        unique_emisores = set(v.emisor for v in valuations if v.emisor)
        unique_fechas_vencimiento = set(v.fecha_vencimiento for v in valuations if v.fecha_vencimiento)
        unique_tipos = set(v.tipo_instrumento for v in valuations if v.tipo_instrumento)
        
        # Detectar si es búsqueda por nemotécnico
        is_nemotecnico_search = (query.emisor and query.tipo_instrumento and 
                                query.emisor == query.tipo_instrumento and not query.isin)
        
        # Si es búsqueda por nemotécnico y hay múltiples resultados, priorizar ISIN
        if is_nemotecnico_search and len(unique_isins) > 1:
            if "isin" not in message_lower and "código" not in message_lower and "codigo" not in message_lower:
                # Mostrar algunos ISINs como opciones
                isins_sample = list(unique_isins)[:3]
                isins_str = ", ".join(str(i) for i in isins_sample if i)
                if len(unique_isins) > 3:
                    isins_str += f" u otro (hay {len(unique_isins)} títulos diferentes)"
                if isins_str:
                    questions.append(f"¿Cuál es el código ISIN del título? Por ejemplo: {isins_str}")
        
        # Si no hay ISIN en la consulta y hay múltiples ISINs (caso general)
        elif not query.isin and len(unique_isins) > 1:
            if "isin" not in message_lower and "código" not in message_lower and "codigo" not in message_lower:
                questions.append("¿Cuál es el código ISIN del título?")
        
        # Si hay múltiples fechas de vencimiento y se mencionó vencimiento
        if ("vencimiento" in message_lower or "vencen" in message_lower) and len(unique_fechas_vencimiento) > 1:
            # Verificar si se mencionó una fecha específica en el mensaje
            fecha_especifica_en_query = query.fecha_vencimiento is not None
            
            if not fecha_especifica_en_query:
                # Buscar fecha en el mensaje original
                fecha_especifica = False
                for v in valuations:
                    if v.fecha_vencimiento:
                        fecha_str = v.fecha_vencimiento.strftime("%d/%m/%Y")
                        fecha_str_alt = v.fecha_vencimiento.strftime("%d-%m-%Y")
                        if fecha_str in message_lower or fecha_str_alt in message_lower:
                            fecha_especifica = True
                            break
                
                if not fecha_especifica:
                    fechas_sample = sorted([f for f in unique_fechas_vencimiento if f])[:3]
                    if fechas_sample:
                        fechas_str = ", ".join(f.strftime("%d/%m/%Y") for f in fechas_sample)
                        questions.append(f"¿Cuál es la fecha de vencimiento exacta? Por ejemplo: {fechas_str}")
        
        # Si no hay emisor en la consulta y hay múltiples emisores
        if not query.emisor and len(unique_emisores) > 1:
            if "emisor" not in message_lower and "banco" not in message_lower:
                # Mostrar algunos emisores como opciones
                emisores_sample = list(unique_emisores)[:3]
                emisores_str = ", ".join(str(e) for e in emisores_sample if e)
                if len(unique_emisores) > 3:
                    emisores_str += f" u otro (hay {len(unique_emisores)} emisores diferentes)"
                if emisores_str:
                    questions.append(f"¿Cuál es el emisor? Por ejemplo: {emisores_str}")
        
        # Si hay múltiples tipos de instrumento
        if len(unique_tipos) > 1:
            tipos_list = [t for t in unique_tipos if t]
            if tipos_list and "tipo" not in message_lower:
                tipos_str = ", ".join(list(tipos_list)[:3])
                questions.append(f"¿Qué tipo de instrumento es? Por ejemplo: {tipos_str}")
        
        # Si no hay proveedor especificado y hay datos de ambos
        providers = set(v.proveedor for v in valuations)
        if not query.proveedor and len(providers) > 1:
            if "pip" not in message_lower and "precia" not in message_lower:
                questions.append("¿De qué proveedor necesitas la información? (PIP o Precia)")
        
        # Si aún no hay preguntas pero hay múltiples resultados, preguntar por cualquier característica distintiva
        if not questions and len(valuations) > 1:
            if len(unique_isins) > 1:
                questions.append("¿Cuál es el código ISIN del título?")
            elif len(unique_emisores) > 1:
                emisores_sample = list(unique_emisores)[:2]
                if emisores_sample:
                    questions.append(f"¿Cuál es el emisor? Por ejemplo: {', '.join(str(e) for e in emisores_sample)}")
            elif len(unique_fechas_vencimiento) > 1:
                fechas_sample = sorted([f for f in unique_fechas_vencimiento if f])[:2]
                if fechas_sample:
                    fechas_str = ", ".join(f.strftime("%d/%m/%Y") for f in fechas_sample)
                    questions.append(f"¿Cuál es la fecha de vencimiento? Por ejemplo: {fechas_str}")
        
        return questions

