"""
Servicio de Embeddings para el Sistema RAG
==========================================

Este módulo implementa la funcionalidad de inicializar y proveer modelos de embeddings
para el almacenamiento y búsqueda semántica en el sistema RAG.

TAREAS SEMANA 2:
- Inicializar GoogleGenerativeAIEmbeddings con el modelo especificado
- Proveer el modelo para uso en RetrievalService (ChromaDB)
- Opcionalmente: implementar método para generar embeddings explícitamente (Uso de otra base de datos vectorial)

TUTORIAL:
- RAG paso a paso, parte 2: embeddings y base de datos vectorial
"""

from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.services.embedding_service_local import LocalEmbeddingService


class EmbeddingService:
    """
    Servicio para generar embeddings usando Google Generative AI.
    
    IMPLEMENTACIÓN REQUERIDA:
    - __init__: Inicializar el modelo de embeddings
    - get_embeddings_model: Retornar el modelo para uso externo
    """
    
    def __init__(self, model: str = "models/embedding-001", use_local: bool = False):
        """
        Inicializa el servicio de embeddings con el modelo de Google AI o local.
        
        TODO SEMANA 2:
        - Guardar model en self.model_name
        - Inicializar self.embeddings_model con Google AI o local
        
        NOTA: ChromaDB usará este modelo para generar embeddings automáticamente
        
        Args:
            model: Nombre del modelo de embeddings (ej: "models/embedding-001")
            use_local: Si True, usa modelo local en lugar de Google AI
        """
        # Guardar configuración del modelo
        self.model_name = model
        self.use_local = use_local
        
        if use_local:
            # Usar modelo local directamente
            print(f"🔗 Usando modelo local: all-MiniLM-L6-v2")
            self.embeddings_model = LocalEmbeddingService(model="all-MiniLM-L6-v2")
        else:
            try:
                # Intentar usar Google AI primero
                print(f"🔗 Intentando usar Google AI: {model}")
                self.embeddings_model = GoogleGenerativeAIEmbeddings(
                    model=model,
                    task_type="retrieval_document"  # Optimizado para documentos
                )
                
                # Probar con un embedding simple para verificar cuota
                print("🧪 Probando cuota de Google AI...")
                test_embedding = self.embeddings_model.embed_query("test")
                print(f"✅ Google AI funcionando: {len(test_embedding)} dimensiones")
                
            except Exception as e:
                error_msg = str(e)
                if "quota" in error_msg.lower() or "429" in error_msg:
                    print(f"⚠️ Cuota de Google AI excedida: {error_msg}")
                    print("🔄 Cambiando automáticamente a modelo local...")
                else:
                    print(f"⚠️ Error con Google AI: {error_msg}")
                    print("🔄 Cambiando a modelo local...")
                
                self.embeddings_model = LocalEmbeddingService(model="all-MiniLM-L6-v2")
                self.use_local = True
        
        print(f"🔗 EmbeddingService inicializado con modelo: {model}")
    
    def get_embeddings_model(self) -> GoogleGenerativeAIEmbeddings:
        """
        Retorna el modelo de embeddings para uso externo.
        
        TODO SEMANA 2:
        - Retornar self.embeddings_model
        
        NOTA: Este método es llamado por RetrievalService para crear el vector store
        
        Returns:
            Instancia del modelo de embeddings
        """
        return self.embeddings_model