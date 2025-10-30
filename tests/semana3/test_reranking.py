"""
Pruebas para el reranking de documentos - Semana 3
=================================================

Este módulo contiene las pruebas para verificar que el reranking
de documentos funciona correctamente.
"""

import pytest
from langchain.schema import Document
from app.services.retrieval_service import RetrievalService


class TestReranking:
    """Pruebas para el reranking de documentos."""
    
    def test_reranking_basic(self):
        """Prueba básica del reranking."""
        retrieval_service = RetrievalService()
        
        # Crear documentos de prueba
        documents = [
            Document(
                page_content="Este documento habla sobre convocatorias de investigación en ciencias.",
                metadata={"source_file": "doc1.pdf", "score": 0.8}
            ),
            Document(
                page_content="Información sobre financiación de proyectos de desarrollo tecnológico.",
                metadata={"source_file": "doc2.pdf", "score": 0.6}
            ),
            Document(
                page_content="Requisitos y condiciones para participar en programas de innovación.",
                metadata={"source_file": "doc3.pdf", "score": 0.9}
            )
        ]
        
        query = "¿Cuáles son los requisitos para las convocatorias de investigación?"
        
        # Aplicar reranking
        reranked_docs = retrieval_service.rerank_documents(
            query=query,
            documents=documents,
            top_n=3
        )
        
        # Verificar que se retornaron documentos
        assert len(reranked_docs) <= 3
        assert len(reranked_docs) > 0
        
        # Verificar que los documentos tienen scores de reranking
        for doc in reranked_docs:
            assert "rerank_score" in doc.metadata
            assert "rerank_position" in doc.metadata
            assert isinstance(doc.metadata["rerank_score"], float)
            assert isinstance(doc.metadata["rerank_position"], int)
    
    def test_reranking_empty_documents(self):
        """Prueba reranking con lista vacía de documentos."""
        retrieval_service = RetrievalService()
        
        reranked_docs = retrieval_service.rerank_documents(
            query="consulta de prueba",
            documents=[],
            top_n=5
        )
        
        assert len(reranked_docs) == 0
    
    def test_reranking_single_document(self):
        """Prueba reranking con un solo documento."""
        retrieval_service = RetrievalService()
        
        documents = [
            Document(
                page_content="Documento único sobre investigación.",
                metadata={"source_file": "single.pdf"}
            )
        ]
        
        query = "investigación"
        
        reranked_docs = retrieval_service.rerank_documents(
            query=query,
            documents=documents,
            top_n=1
        )
        
        assert len(reranked_docs) == 1
        assert "rerank_score" in reranked_docs[0].metadata
        assert reranked_docs[0].metadata["rerank_position"] == 1
    
    def test_reranking_top_n_limitation(self):
        """Prueba que el reranking respeta el límite top_n."""
        retrieval_service = RetrievalService()
        
        # Crear más documentos que el top_n
        documents = [
            Document(
                page_content=f"Documento {i} sobre investigación.",
                metadata={"source_file": f"doc{i}.pdf"}
            )
            for i in range(10)
        ]
        
        query = "investigación"
        
        reranked_docs = retrieval_service.rerank_documents(
            query=query,
            documents=documents,
            top_n=3
        )
        
        assert len(reranked_docs) == 3
    
    def test_reranking_fallback(self):
        """Prueba el fallback cuando sentence-transformers no está disponible."""
        retrieval_service = RetrievalService()
        
        documents = [
            Document(
                page_content="Documento de prueba.",
                metadata={"source_file": "test.pdf"}
            )
        ]
        
        query = "consulta de prueba"
        
        # Simular error de importación
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'sentence_transformers':
                raise ImportError("sentence-transformers not available")
            return original_import(name, *args, **kwargs)
        
        __builtins__['__import__'] = mock_import
        
        try:
            reranked_docs = retrieval_service.rerank_documents(
                query=query,
                documents=documents,
                top_n=1
            )
            
            # Debe retornar los documentos sin reranking
            assert len(reranked_docs) == 1
            assert "rerank_score" not in reranked_docs[0].metadata
        finally:
            __builtins__['__import__'] = original_import