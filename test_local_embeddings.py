#!/usr/bin/env python3
"""
Script de prueba para verificar que el modelo de embeddings local funciona correctamente
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("✅ Variables de entorno cargadas")

# Probar EmbeddingService local
try:
    from app.services.embedding_service_local import LocalEmbeddingService
    
    print("🔗 Probando LocalEmbeddingService...")
    embedding_service = LocalEmbeddingService(model="all-MiniLM-L6-v2")
    
    # Probar embedding de un texto simple
    print("🧪 Probando embedding de texto...")
    test_text = "Este es un texto de prueba"
    
    # Probar embedding
    embedding = embedding_service.embed_query(test_text)
    print(f"✅ Embedding generado exitosamente: {len(embedding)} dimensiones")
    
    # Probar embedding de documentos
    print("🧪 Probando embedding de documentos...")
    documents = ["Documento 1", "Documento 2"]
    doc_embeddings = embedding_service.embed_documents(documents)
    print(f"✅ Embeddings de documentos generados: {len(doc_embeddings)} embeddings")
    
    print("✅ LocalEmbeddingService funciona correctamente")
    
except Exception as e:
    print(f"❌ Error en LocalEmbeddingService: {str(e)}")
    import traceback
    traceback.print_exc()


