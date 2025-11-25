"""
Servicio de conocimiento para integrar documentación sobre renta fija
"""
import os
import logging
from typing import List, Optional, Dict
from pathlib import Path
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)

# Intentar importar PyPDF2
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 no está instalado. El servicio de conocimiento no funcionará.")


class KnowledgeService:
    """Servicio para gestionar conocimiento sobre renta fija desde documentos PDF"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model
        self.knowledge_base_path = Path(__file__).parent.parent.parent / "Guia de Estudio - Renta Fija.pdf"
        self.chunks = []
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Carga y procesa el documento PDF de conocimiento"""
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 no está disponible. El servicio de conocimiento no funcionará.")
            return
            
        try:
            if not self.knowledge_base_path.exists():
                logger.warning(f"Documento de conocimiento no encontrado: {self.knowledge_base_path}")
                return
            
            logger.info(f"Cargando documento de conocimiento: {self.knowledge_base_path}")
            
            # Extraer texto del PDF
            with open(self.knowledge_base_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            text_content.append({
                                'page': page_num + 1,
                                'text': text.strip()
                            })
                    except Exception as e:
                        logger.warning(f"Error extrayendo página {page_num + 1}: {str(e)}")
                        continue
                
                # Dividir en chunks para búsqueda
                self.chunks = self._split_into_chunks(text_content)
                logger.info(f"Documento cargado: {len(self.chunks)} chunks procesados")
                
        except Exception as e:
            logger.error(f"Error cargando documento de conocimiento: {str(e)}")
            self.chunks = []
    
    def _split_into_chunks(self, pages: List[Dict], chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Divide el texto en chunks para búsqueda semántica"""
        chunks = []
        
        for page_data in pages:
            text = page_data['text']
            page_num = page_data['page']
            
            # Dividir por párrafos primero
            paragraphs = text.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) < chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk.strip():
                        chunks.append({
                            'text': current_chunk.strip(),
                            'page': page_num,
                            'source': 'Guia de Estudio - Renta Fija'
                        })
                    current_chunk = para + "\n\n"
            
            # Agregar el último chunk de la página
            if current_chunk.strip():
                chunks.append({
                    'text': current_chunk.strip(),
                    'page': page_num,
                    'source': 'Guia de Estudio - Renta Fija'
                })
        
        return chunks
    
    def search_relevant_context(self, query: str, max_chunks: int = 3) -> List[Dict]:
        """
        Busca contexto relevante en el documento de conocimiento
        
        Args:
            query: Consulta del usuario
            max_chunks: Número máximo de chunks a retornar
        
        Returns:
            Lista de chunks relevantes con su contexto
        """
        if not self.chunks:
            return []
        
        try:
            # Búsqueda por palabras clave mejorada (sin embeddings para evitar costos)
            query_lower = query.lower()
            scored_chunks = []
            
            for chunk in self.chunks:
                chunk_text_lower = chunk['text'].lower()
                
                # Calcular score simple basado en palabras clave
                score = 0
                keywords = query_lower.split()
                for keyword in keywords:
                    if len(keyword) > 3:  # Ignorar palabras muy cortas
                        score += chunk_text_lower.count(keyword)
                
                # Bonus si el chunk contiene términos relacionados con renta fija
                renta_fija_terms = ['tir', 'tasa', 'precio', 'duración', 'convexidad', 'valoración', 
                                   'cdt', 'tes', 'bonos', 'renta fija', 'yield', 'cupón']
                for term in renta_fija_terms:
                    if term in query_lower and term in chunk_text_lower:
                        score += 2
                
                if score > 0:
                    scored_chunks.append({
                        'chunk': chunk,
                        'score': score
                    })
            
            # Ordenar por score y retornar los mejores
            scored_chunks.sort(key=lambda x: x['score'], reverse=True)
            return [item['chunk'] for item in scored_chunks[:max_chunks]]
            
        except Exception as e:
            logger.error(f"Error buscando contexto relevante: {str(e)}")
            return []
    
    def get_context_for_query(self, query: str) -> str:
        """
        Obtiene contexto relevante del documento para una consulta
        
        Args:
            query: Consulta del usuario
        
        Returns:
            Texto de contexto formateado
        """
        relevant_chunks = self.search_relevant_context(query, max_chunks=3)
        
        if not relevant_chunks:
            return ""
        
        context_parts = []
        for chunk in relevant_chunks:
            context_parts.append(f"[Página {chunk['page']}]\n{chunk['text'][:500]}...")
        
        return "\n\n---\n\n".join(context_parts)
    
    def enhance_response_with_knowledge(self, query: str, base_response: str) -> str:
        """
        Enriquece una respuesta con conocimiento del documento
        
        Args:
            query: Consulta original del usuario
            base_response: Respuesta base generada por el sistema
        
        Returns:
            Respuesta enriquecida con contexto del documento
        """
        context = self.get_context_for_query(query)
        
        if not context:
            return base_response
        
        try:
            # Usar LLM para integrar el contexto en la respuesta
            enhancement_prompt = f"""
            Tienes una respuesta sobre renta fija y contexto adicional de una guía de estudio.
            
            Respuesta actual:
            {base_response}
            
            Contexto relevante de la guía:
            {context}
            
            Enriquece la respuesta con información relevante del contexto, pero mantén la información específica de la respuesta original.
            Si el contexto no es relevante para la consulta, solo devuelve la respuesta original.
            Responde de forma concisa y profesional.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto en renta fija colombiana. Enriqueces respuestas con conocimiento técnico cuando es relevante."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            enhanced = response.choices[0].message.content.strip()
            return enhanced if enhanced else base_response
            
        except Exception as e:
            logger.error(f"Error enriqueciendo respuesta con conocimiento: {str(e)}")
            return base_response

