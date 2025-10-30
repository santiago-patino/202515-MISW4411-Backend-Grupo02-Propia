#!/usr/bin/env python3
"""
Script de prueba para el sistema RAG con embeddings locales
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("✅ Variables de entorno cargadas")

# Probar el sistema RAG completo con embeddings locales
try:
    from app.services.embedding_service import EmbeddingService
    from app.services.chunking_service import ChunkingService, ChunkingStrategy
    from app.services.retrieval_service import RetrievalService
    from app.services.generation_service import GenerationService
    
    print("🔗 Inicializando servicios con embeddings locales...")
    
    # Usar embeddings locales
    embedding_service = EmbeddingService(use_local=True)
    
    # Inicializar otros servicios
    chunking_service = ChunkingService(
        strategy=ChunkingStrategy.RECURSIVE_CHARACTER,
        chunk_size=1000,
        chunk_overlap=200
    )
    
    retrieval_service = RetrievalService()
    generation_service = GenerationService()
    
    print("✅ Todos los servicios inicializados correctamente")
    
    # Probar chunking
    print("🧪 Probando chunking...")
    chunks = chunking_service.process_collection("test_collection")
    print(f"✅ Chunking completado: {len(chunks)} chunks generados")
    
    if chunks:
        # Probar creación de vector store
        print("🧪 Probando creación de vector store...")
        success, stats = retrieval_service.create_vector_store(
            documents=chunks,
            collection_name="test_collection_local",
            force_rebuild=True,
            embedding_service=embedding_service,
            batch_size=10  # Batch pequeño para prueba
        )
        
        if success:
            print("✅ Vector store creado exitosamente")
            print(f"📊 Estadísticas: {stats}")
            
            # Probar búsqueda
            print("🧪 Probando búsqueda semántica...")
            retrieved_docs = retrieval_service.similarity_search(
                query="¿De qué trata el documento?",
                collection_name="test_collection_local",
                k=3,
                embedding_service=embedding_service
            )
            
            print(f"✅ Búsqueda completada: {len(retrieved_docs)} documentos encontrados")
            
            if retrieved_docs:
                # Probar generación de respuesta
                print("🧪 Probando generación de respuesta...")
                result = generation_service.generate_response(
                    question="¿De qué trata el documento?",
                    retrieved_docs=retrieved_docs
                )
                
                print("✅ Respuesta generada:")
                print(f"📝 Respuesta: {result['answer']}")
                print(f"📄 Fuentes: {result['sources']}")
                
        else:
            print(f"❌ Error creando vector store: {stats}")
    
    print("🎉 Sistema RAG con embeddings locales funciona correctamente!")
    
except Exception as e:
    print(f"❌ Error en el sistema RAG: {str(e)}")
    import traceback
    traceback.print_exc()


