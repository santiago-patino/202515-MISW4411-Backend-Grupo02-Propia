#!/usr/bin/env python3
"""
Script de prueba para el sistema RAG con fallback automático
============================================================

Este script prueba que el sistema RAG funcione automáticamente
usando Google AI cuando esté disponible, y cambiando a modelos
locales cuando la cuota esté excedida.
"""

import os
from dotenv import load_dotenv
from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import ChunkingService, ChunkingStrategy
from app.services.retrieval_service import RetrievalService
from app.services.generation_service import GenerationService
from langchain.schema import Document

def main():
    print("🧪 Probando sistema RAG con fallback automático...")
    
    # Cargar variables de entorno
    load_dotenv()
    print("✅ Variables de entorno cargadas")
    
    # 1. Probar EmbeddingService con fallback automático
    print("\n🔗 Probando EmbeddingService con fallback automático...")
    try:
        embedding_service = EmbeddingService()  # Sin use_local=True para probar fallback
        embeddings_model = embedding_service.get_embeddings_model()
        print(f"✅ EmbeddingService: {embeddings_model.model}")
        
        # Probar embedding
        test_embedding = embeddings_model.embed_query("Texto de prueba")
        print(f"✅ Embedding generado: {len(test_embedding)} dimensiones")
        
    except Exception as e:
        print(f"❌ Error en EmbeddingService: {e}")
        return
    
    # 2. Probar GenerationService con fallback automático
    print("\n🤖 Probando GenerationService con fallback automático...")
    try:
        generation_service = GenerationService()  # Sin use_local=True para probar fallback
        print(f"✅ GenerationService inicializado")
        
    except Exception as e:
        print(f"❌ Error en GenerationService: {e}")
        return
    
    # 3. Probar pipeline completo
    print("\n🔄 Probando pipeline RAG completo...")
    try:
        # Inicializar servicios
        chunking_service = ChunkingService(
            strategy=ChunkingStrategy.RECURSIVE_CHARACTER,
            chunk_size=1000,
            chunk_overlap=200
        )
        retrieval_service = RetrievalService()
        
        # Procesar documentos
        print("📄 Procesando documentos...")
        chunks = chunking_service.process_collection("test_collection")
        print(f"✅ Chunks generados: {len(chunks)}")
        
        # Crear vector store
        print("🗄️ Creando vector store...")
        success, stats = retrieval_service.create_vector_store(
            documents=chunks,
            collection_name="test_auto_fallback",
            force_rebuild=True,
            embedding_service=embedding_service,
            batch_size=10
        )
        
        if success:
            print(f"✅ Vector store creado: {stats['collection_name']}")
            
            # Búsqueda semántica
            print("🔍 Realizando búsqueda semántica...")
            query = "¿De qué trata el documento?"
            retrieved_docs = retrieval_service.similarity_search(
                query=query,
                collection_name="test_auto_fallback",
                k=3,
                embedding_service=embedding_service
            )
            print(f"✅ Documentos encontrados: {len(retrieved_docs)}")
            
            # Generar respuesta
            print("🤖 Generando respuesta...")
            response = generation_service.generate_response(
                question=query,
                retrieved_docs=retrieved_docs
            )
            
            print(f"✅ Respuesta generada: {len(response['answer'])} caracteres")
            print(f"📄 Fuentes: {response['sources']}")
            print(f"📝 Respuesta: {response['answer'][:200]}...")
            
            print("\n🎉 ¡Sistema RAG con fallback automático funciona correctamente!")
            
        else:
            print("❌ Error creando vector store")
            
    except Exception as e:
        print(f"❌ Error en pipeline RAG: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


