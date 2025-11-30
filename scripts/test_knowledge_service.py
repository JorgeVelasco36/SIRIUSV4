#!/usr/bin/env python3
"""
Script para probar el servicio de conocimiento
"""
import sys
import os
from pathlib import Path

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Cambiar al directorio backend para cargar .env
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)

sys.path.insert(0, str(backend_dir))

from services.knowledge_service import KnowledgeService

def test_knowledge_service():
    """Prueba el servicio de conocimiento"""
    print("=== Probando Servicio de Conocimiento ===\n")
    
    try:
        knowledge_service = KnowledgeService()
        
        print(f"Chunks cargados: {len(knowledge_service.chunks)}")
        
        if len(knowledge_service.chunks) > 0:
            print(f"[OK] Documento cargado exitosamente")
            print(f"Primer chunk (página {knowledge_service.chunks[0]['page']}):")
            print(f"{knowledge_service.chunks[0]['text'][:200]}...\n")
            
            # Probar búsqueda
            test_queries = [
                "¿Qué es la TIR?",
                "¿Qué es la duración?",
                "¿Qué es el precio limpio?",
                "¿Qué es un CDT?"
            ]
            
            for query in test_queries:
                print(f"\nConsulta: {query}")
                context = knowledge_service.get_context_for_query(query)
                if context:
                    print(f"[OK] Contexto encontrado:")
                    # Mostrar solo los primeros 200 caracteres para evitar problemas de codificación
                    try:
                        preview = context[:200].encode('ascii', errors='replace').decode('ascii')
                        print(preview + "...")
                    except:
                        print("(Contexto encontrado pero no se puede mostrar debido a caracteres especiales)")
                else:
                    print("[INFO] No se encontró contexto relevante")
        else:
            print("[ADVERTENCIA] No se cargaron chunks del documento")
            print("Verifica que el PDF esté en la ruta correcta")
            
    except Exception as e:
        print(f"[ERROR] Error probando servicio de conocimiento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_knowledge_service()

