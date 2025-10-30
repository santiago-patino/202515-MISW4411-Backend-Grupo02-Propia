"""
Servicio de Retrieval para el Sistema RAG
==========================================

Este módulo implementa la funcionalidad de almacenamiento y recuperación de documentos
usando una base de datos vectorial ChromaDB.

TAREAS SEMANA 2:
- Crear vector store con ChromaDB
- Implementar similarity_search para recuperar documentos relevantes
- Opcionalmente: crear retrievers configurables

TAREAS SEMANA 3:
- Implementar reranking de documentos recuperados (método rerank_documents)
- El reranking mejora la relevancia de los documentos usando modelos cross-encoder

TUTORIALES:
- RAG paso a paso, parte 2: embeddings y base de datos vectorial
- RAG paso a paso, parte 3: recuperación y generación de respuestas
- Reranking con LangChain
"""

import os
import shutil
import time
from typing import List, Dict, Any, Tuple, Optional

from langchain.schema import Document
from langchain_chroma import Chroma
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    """
    Servicio para almacenar y recuperar documentos usando ChromaDB.
    
    IMPLEMENTACIÓN REQUERIDA (SEMANA 2):
    - __init__: Inicializar el servicio
    - create_vector_store: Crear base de datos vectorial con chunks
    - get_vector_store: Obtener un vector store existente
    - similarity_search: Buscar documentos similares a una consulta
    
    IMPLEMENTACIÓN REQUERIDA (SEMANA 3):
    - rerank_documents: Reordenar documentos por relevancia usando cross-encoder
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"): # Ejemplo con el uso de ChromaDB
        """
        Inicializa el servicio de retrieval.
        
        TODO SEMANA 2:
        - Guardar persist_directory
        - Inicializar cache de vector stores (diccionario)
        
        TODO SEMANA 3 (OPCIONAL):
        - Inicializar modelo de reranking (cross-encoder) si se desea
        - O dejar que se inicialice bajo demanda en rerank_documents()
        
        Args:
            persist_directory: Directorio donde se almacenará ChromaDB
        """
        # Guardar directorio de persistencia
        self.persist_directory = persist_directory
        
        # Cache de vector stores para evitar recargar
        self.vector_stores_cache = {}
        
        # Crear directorio si no existe
        os.makedirs(persist_directory, exist_ok=True)
        
        print(f"🗄️ RetrievalService inicializado con directorio: {persist_directory}")
    
    def create_vector_store(
        self,
        documents: List[Document],
        collection_name: str,
        force_rebuild: bool = True,
        embedding_service: EmbeddingService = None,
        batch_size: int = 90
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Crea una base de datos vectorial ChromaDB con los documentos proporcionados.
        
        TODO SEMANA 2:
        - Obtener el modelo de embeddings desde embedding_service
        - Si force_rebuild, eliminar colección anterior
        - Crear Chroma vector store con:
          * collection_name
          * embedding_function (del embedding_service)
          * persist_directory específico para la colección
        - Extraer texts, metadatas e ids de los documentos
        - Agregar documents al vector store con add_texts()
        - Guardar en cache
        - Retornar (True, embedding_stats) si éxito, (False, error_dict) si falla
        
        IMPORTANTE - RATE LIMITING:
        - Google AI Free Tier: 100 requests/minuto
        - Procesar en batches de ~90 chunks
        - Esperar 65 segundos entre batches
        - Ver documentación adicional sobre límites de cuota
        
        Args:
            documents: Lista de chunks a almacenar
            collection_name: Nombre de la colección
            force_rebuild: Si True, elimina la colección anterior
            embedding_service: Servicio de embeddings
            batch_size: Chunks por batch (default: 90 para free tier)
            
        Returns:
            Tuple[bool, Dict]: (éxito, estadísticas_o_error)
        """
        try:
            print(f"🔄 Creando vector store para colección: {collection_name}")
            print(f"📊 Documentos a procesar: {len(documents)}")
            print(f"🔧 Force rebuild: {force_rebuild}, Batch size: {batch_size}")
            
            # Validar embedding service
            if not embedding_service:
                return False, {"error": "EmbeddingService es requerido"}
            
            # Obtener modelo de embeddings
            embeddings_model = embedding_service.get_embeddings_model()
            
            # Directorio específico para esta colección
            collection_path = os.path.join(self.persist_directory, collection_name)
            
            # Si force_rebuild, eliminar colección anterior
            if force_rebuild and os.path.exists(collection_path):
                print(f"🗑️ Eliminando colección anterior: {collection_path}")
                shutil.rmtree(collection_path)
            
            # Crear vector store con ChromaDB
            print(f"🔗 Usando modelo de embeddings: {embeddings_model.model}")
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings_model,
                persist_directory=collection_path
            )
            
            # Procesar documentos en batches para respetar rate limits
            total_documents = len(documents)
            processed_documents = 0
            
            print(f"📦 Procesando {total_documents} documentos en batches de {batch_size}")
            
            for i in range(0, total_documents, batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_documents + batch_size - 1) // batch_size
                
                print(f"📦 Procesando batch {batch_num}/{total_batches} ({len(batch_docs)} documentos)")
                
                # Extraer textos y metadatos del batch
                texts = [doc.page_content for doc in batch_docs]
                metadatas = [doc.metadata for doc in batch_docs]
                ids = [f"{collection_name}_{i + j}" for j, doc in enumerate(batch_docs)]
                
                # Agregar documentos al vector store
                vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                processed_documents += len(batch_docs)
                print(f"✅ Batch {batch_num} procesado: {processed_documents}/{total_documents} documentos")
                
                # Esperar entre batches para respetar rate limits (excepto en el último batch)
                if i + batch_size < total_documents:
                    print("⏳ Esperando 65 segundos para respetar rate limits...")
                    time.sleep(65)
            
            # Persistir el vector store (método depende de la versión de ChromaDB)
            try:
                vector_store.persist()
            except AttributeError:
                # En versiones más recientes de ChromaDB, no es necesario llamar persist()
                pass
            
            # Guardar en cache
            self.vector_stores_cache[collection_name] = vector_store
            
            # Calcular estadísticas
            embedding_stats = {
                "collection_name": collection_name,
                "total_documents": total_documents,
                "total_batches": (total_documents + batch_size - 1) // batch_size,
                "batch_size": batch_size,
                "vector_store_path": collection_path,
                "embedding_model": embedding_service.model_name,
                "created_at": time.time()
            }
            
            print(f"✅ Vector store creado exitosamente: {collection_name}")
            print(f"📊 Estadísticas: {embedding_stats}")
            
            return True, embedding_stats
            
        except Exception as e:
            error_msg = f"Error creando vector store: {str(e)}"
            print(f"❌ {error_msg}")
            return False, {"error": error_msg}
    
    def get_vector_store(
        self, 
        collection_name: str, 
        embedding_service: EmbeddingService = None
    ) -> Optional[Chroma]:
        """
        Obtiene un vector store existente.
        
        TODO SEMANA 2:
        - Verificar cache primero
        - Si no está en cache, verificar si existe en disco
        - Si existe, cargar con Chroma() y guardar en cache
        - Retornar vector store o None
        
        Args:
            collection_name: Nombre de la colección
            embedding_service: Servicio de embeddings
            
        Returns:
            Instancia de Chroma o None si no existe
        """
        # Verificar cache primero
        if collection_name in self.vector_stores_cache:
            print(f"📋 Vector store encontrado en cache: {collection_name}")
            return self.vector_stores_cache[collection_name]
        
        # Verificar si existe en disco
        collection_path = os.path.join(self.persist_directory, collection_name)
        
        if not os.path.exists(collection_path):
            print(f"⚠️ Vector store no encontrado: {collection_name}")
            return None
        
        # Validar embedding service
        if not embedding_service:
            print(f"❌ EmbeddingService requerido para cargar: {collection_name}")
            return None
        
        try:
            print(f"🔄 Cargando vector store desde disco: {collection_name}")
            
            # Obtener modelo de embeddings
            embeddings_model = embedding_service.get_embeddings_model()
            
            # Cargar vector store existente
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings_model,
                persist_directory=collection_path
            )
            
            # Guardar en cache
            self.vector_stores_cache[collection_name] = vector_store
            
            print(f"✅ Vector store cargado exitosamente: {collection_name}")
            return vector_store
            
        except Exception as e:
            print(f"❌ Error cargando vector store {collection_name}: {str(e)}")
            return None
    
    def similarity_search(
        self, 
        query: str, 
        collection_name: str = "default",
        k: int = 3,
        embedding_service: EmbeddingService = None
    ) -> List[Document]:
        """
        Busca documentos similares a la consulta.
        
        TODO SEMANA 2:
        - Obtener vector_store con get_vector_store()
        - Usar vector_store.similarity_search(query, k=k)
        - Retornar lista de documentos relevantes
        
        NOTA: Este método es llamado por ask.py para recuperar contexto
        
        Args:
            query: Consulta del usuario
            collection_name: Nombre de la colección
            k: Número de documentos a recuperar
            embedding_service: Servicio de embeddings
            
        Returns:
            Lista de documentos relevantes (objetos Document)
        """
        try:
            print(f"🔍 Buscando documentos similares a: '{query[:50]}...'")
            print(f"📋 Colección: {collection_name}, k: {k}")
            
            # Obtener vector store
            vector_store = self.get_vector_store(collection_name, embedding_service)
            
            if not vector_store:
                print(f"❌ Vector store no disponible: {collection_name}")
                return []
            
            # Realizar búsqueda de similitud
            documents = vector_store.similarity_search(query, k=k)
            
            print(f"✅ Encontrados {len(documents)} documentos relevantes")
            
            # Log de documentos encontrados
            for i, doc in enumerate(documents):
                source_file = doc.metadata.get('source_file', 'unknown')
                chunk_size = len(doc.page_content)
                print(f"  📄 {i+1}. {source_file} ({chunk_size} chars)")
            
            return documents
            
        except Exception as e:
            print(f"❌ Error en similarity search: {str(e)}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Obtiene información sobre una colección.
        
        Args:
            collection_name: Nombre de la colección
            
        Returns:
            Diccionario con información de la colección
        """
        collection_path = os.path.join(self.persist_directory, collection_name)
        
        info = {
            "exists": os.path.exists(collection_path),
            "path": collection_path,
            "document_count": 0
        }
        
        if info["exists"]:
            try:
                # Intentar cargar el vector store para obtener conteo
                vector_store = self.get_vector_store(collection_name, None)
                if vector_store:
                    # Obtener conteo de documentos
                    collection = vector_store._collection
                    info["document_count"] = collection.count()
            except Exception as e:
                print(f"⚠️ Error obteniendo info de colección {collection_name}: {str(e)}")
        
        return info
    
    def rerank_documents(
        self, 
        query: str, 
        documents: List[Document], 
        top_n: int = 5
    ) -> List[Document]:
        """
        Reordena documentos recuperados usando un modelo de reranking.
        
        TODO SEMANA 3:
        - Importar un modelo cross-encoder (ej: sentence_transformers.CrossEncoder)
        - Crear pares (query, doc.page_content) para cada documento
        - Calcular scores de relevancia con el modelo
        - Ordenar documentos por score (descendente)
        - IMPORTANTE: Añadir 'rerank_score' a doc.metadata de cada documento
        - Retornar top_n documentos reordenados
        
        MODELOS SUGERIDOS (escoger uno):
        - sentence-transformers: CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        - Cohere: rerank-v3.5
        - Jina AI: jina-reranker-v1-base-en
        - Cualquier modelo open-source de reranking
        
        NOTA: Este método es llamado por ask.py después de similarity_search
        cuando el parámetro use_reranking=True
        
        Args:
            query: Consulta del usuario
            documents: Lista de documentos del similarity_search
            top_n: Número de documentos a retornar
            
        Returns:
            List[Document]: Documentos reordenados con 'rerank_score' en metadata
        """
        try:
            print(f"🔄 Aplicando reranking a {len(documents)} documentos")
            
            # Importar CrossEncoder
            from sentence_transformers import CrossEncoder
            
            # Inicializar modelo de reranking
            # Usamos un modelo ligero y eficiente
            reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
            # Crear pares (query, document_content) para scoring
            pairs = []
            for doc in documents:
                pairs.append([query, doc.page_content])
            
            print("📊 Calculando scores de relevancia...")
            
            # Calcular scores de relevancia
            scores = reranker.predict(pairs)
            
            # Crear lista de (documento, score) y ordenar por score descendente
            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Añadir rerank_score a metadata y retornar top_n
            reranked_docs = []
            for i, (doc, score) in enumerate(doc_score_pairs[:top_n]):
                # Añadir score de reranking a los metadatos
                doc.metadata['rerank_score'] = float(score)
                doc.metadata['rerank_position'] = i + 1
                reranked_docs.append(doc)
                
                print(f"  📄 {i+1}. Score: {score:.4f} - {doc.metadata.get('source_file', 'unknown')}")
            
            print(f"✅ Reranking completado: {len(reranked_docs)} documentos reordenados")
            return reranked_docs
            
        except ImportError:
            print("⚠️ sentence-transformers no está instalado. Retornando documentos sin reranking.")
            return documents[:top_n]
        except Exception as e:
            print(f"❌ Error en reranking: {str(e)}")
            print("🔄 Retornando documentos sin reranking...")
            return documents[:top_n]