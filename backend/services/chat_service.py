"""
Servicio de chat con procesamiento de lenguaje natural
"""
from openai import OpenAI
from typing import Dict, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from models import Provider
from services.query_service import QueryService
from schemas import ValuationQuery
from config import settings
import logging
import dateparser

logger = logging.getLogger(__name__)


class ChatService:
    """Servicio para procesar consultas en lenguaje natural y generar respuestas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.query_service = QueryService(db)
        
        # Configurar OpenAI
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
    
    def extract_intent(self, message: str) -> Dict:
        """
        Extrae intención y parámetros de una consulta en lenguaje natural
        
        Args:
            message: Mensaje del usuario
        
        Returns:
            Diccionario con intención y parámetros extraídos
        """
        # Prompt para extracción de intención
        extraction_prompt = f"""
        Analiza la siguiente consulta sobre valoraciones de renta fija colombiana y extrae:
        
        1. Tipo de consulta: "precio", "comparacion", "multiples_isins", "explicacion", "busqueda"
        2. ISIN(s): códigos ISIN mencionados
        3. Proveedor: "PIP_LATAM" o "PRECIA" o ambos
        4. Fecha: fecha específica o "hoy", "ayer", etc.
        5. Campos solicitados: precio_limpio, precio_sucio, tasa, duracion, convexidad, etc.
        
        Consulta: "{message}"
        
        Responde SOLO con un JSON válido en este formato:
        {{
            "intent": "tipo_de_consulta",
            "isins": ["ISIN1", "ISIN2"],
            "provider": "PIP_LATAM" o "PRECIA" o null,
            "date": "YYYY-MM-DD" o null,
            "fields": ["campo1", "campo2"],
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
            return result
        except Exception as e:
            logger.error(f"Error extrayendo intención: {str(e)}")
            # Fallback: búsqueda simple por palabras clave
            return self._fallback_extraction(message)
    
    def _fallback_extraction(self, message: str) -> Dict:
        """Extracción básica por palabras clave si falla el LLM"""
        message_upper = message.upper()
        
        result = {
            "intent": "busqueda",
            "isins": [],
            "provider": None,
            "date": None,
            "fields": [],
            "comparison": False
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
        
        # Intentar extraer ISIN (formato CO000123456)
        import re
        isin_pattern = r'CO\d{9}'
        isins = re.findall(isin_pattern, message_upper)
        if isins:
            result["isins"] = isins
        
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
        
        return ValuationQuery(
            isin=extracted.get("isins", [None])[0] if extracted.get("isins") else None,
            isins=extracted.get("isins") if len(extracted.get("isins", [])) > 1 else None,
            proveedor=Provider(extracted["provider"]) if extracted.get("provider") else None,
            fecha=fecha,
            fecha_inicio=None,  # Se puede mejorar con rangos
            fecha_fin=None
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
            # Extraer intención
            extracted = self.extract_intent(message)
            
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
                else:
                    answer = self._format_comparison(comparison)
                    recommendations = self._generate_comparison_recommendations(comparison)
                
                data = comparison
                
            elif query.isins or (query.isin and len(extracted.get("isins", [])) > 1):
                # Múltiples ISINs
                valuations = self.query_service.query_valuations(query)
                answer = f"Se encontraron {len(valuations)} valoraciones:\n\n"
                answer += self.format_valuation_table(valuations)
                recommendations = self._generate_general_recommendations(valuations)
                data = [self._valuation_to_dict(v) for v in valuations]
                
            else:
                # Consulta simple
                valuations = self.query_service.query_valuations(query)
                
                if not valuations:
                    answer = f"No se encontraron valoraciones con los criterios especificados."
                    recommendations = [
                        "Verificar el ISIN proporcionado",
                        "Confirmar que existe valoración para la fecha solicitada",
                        "Revisar que el proveedor seleccionado tenga datos disponibles"
                    ]
                    data = None
                else:
                    answer = self._format_single_response(valuations[0], extracted)
                    recommendations = self._generate_single_recommendations(valuations[0])
                    data = self._valuation_to_dict(valuations[0])
            
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
        """Formatea respuesta para una sola valoración"""
        lines = []
        lines.append(f"**Valoración para ISIN {valuation.isin}**")
        lines.append(f"Proveedor: {valuation.proveedor.value}")
        lines.append(f"Fecha: {valuation.fecha}\n")
        
        if valuation.precio_limpio:
            lines.append(f"Precio Limpio: {valuation.precio_limpio:.2f}")
        if valuation.precio_sucio:
            lines.append(f"Precio Sucio: {valuation.precio_sucio:.2f}")
        if valuation.tasa:
            lines.append(f"Tasa: {valuation.tasa:.4f}%")
        if valuation.duracion:
            lines.append(f"Duración: {valuation.duracion:.2f}")
        if valuation.convexidad:
            lines.append(f"Convexidad: {valuation.convexidad:.4f}")
        
        if valuation.archivo_origen:
            lines.append(f"\nArchivo origen: {valuation.archivo_origen}")
        
        return "\n".join(lines)
    
    def _valuation_to_dict(self, valuation) -> Dict:
        """Convierte objeto Valuation a diccionario"""
        return {
            "isin": valuation.isin,
            "emisor": valuation.emisor,
            "tipo_instrumento": valuation.tipo_instrumento,
            "precio_limpio": valuation.precio_limpio,
            "precio_sucio": valuation.precio_sucio,
            "tasa": valuation.tasa,
            "duracion": valuation.duracion,
            "convexidad": valuation.convexidad,
            "fecha": valuation.fecha.isoformat() if valuation.fecha else None,
            "proveedor": valuation.proveedor.value,
            "archivo_origen": valuation.archivo_origen
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

