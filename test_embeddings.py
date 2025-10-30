#!/usr/bin/env python3
"""
Script de prueba para verificar que el modelo de embeddings funciona correctamente
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Verificar API key
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY no encontrada")
    exit(1)

print("✅ GOOGLE_API_KEY encontrada")

# Probar EmbeddingService
try:
    from app.services.embedding_service import EmbeddingService
    
    print("🔗 Probando EmbeddingService...")
    embedding_service = EmbeddingService(model="models/embedding-001")
    
    # Probar embedding de un texto simple
    print("🧪 Probando embedding de texto...")
    test_text = "Este es un texto de prueba"
    
    # Obtener el modelo
    embeddings_model = embedding_service.get_embeddings_model()
    
    # Probar embedding
    embedding = embeddings_model.embed_query(test_text)
    print(f"✅ Embedding generado exitosamente: {len(embedding)} dimensiones")
    
    # Probar embedding de documentos
    print("🧪 Probando embedding de documentos...")
    documents = ["Documento 1", "Documento 2"]
    doc_embeddings = embeddings_model.embed_documents(documents)
    print(f"✅ Embeddings de documentos generados: {len(doc_embeddings)} embeddings")
    
    print("✅ EmbeddingService funciona correctamente")
    
except Exception as e:
    print(f"❌ Error en EmbeddingService: {str(e)}")
    import traceback
    traceback.print_exc()


