"""
Servicio de Embeddings Local para el Sistema RAG
===============================================

Este módulo implementa embeddings locales usando sentence-transformers
para evitar límites de cuota de APIs externas.
"""

from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np


class LocalEmbeddingService:
    """
    Servicio para generar embeddings usando modelos locales.
    
    Ventajas:
    - No requiere API keys
    - Sin límites de cuota
    - Funciona offline
    """
    
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """
        Inicializa el servicio de embeddings local.
        
        Args:
            model: Nombre del modelo de sentence-transformers
        """
        self.model_name = model
        
        # Cargar modelo local
        print(f"🔗 Cargando modelo local: {model}")
        self.embeddings_model = SentenceTransformer(model)
        print(f"✅ Modelo local cargado: {model}")
    
    def get_embeddings_model(self):
        """
        Retorna el modelo de embeddings para uso externo.
        
        Returns:
            Instancia del modelo de embeddings local
        """
        return self.embeddings_model
    
    @property
    def model(self):
        """
        Propiedad para compatibilidad con ChromaDB.
        
        Returns:
            Nombre del modelo
        """
        return self.model_name
    
    def embed_query(self, text: str) -> List[float]:
        """
        Genera embedding para una consulta.
        
        Args:
            text: Texto a convertir en embedding
            
        Returns:
            Lista de números flotantes (embedding)
        """
        return self.embeddings_model.encode(text).tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para múltiples documentos.
        
        Args:
            texts: Lista de textos a convertir en embeddings
            
        Returns:
            Lista de embeddings
        """
        return self.embeddings_model.encode(texts).tolist()
