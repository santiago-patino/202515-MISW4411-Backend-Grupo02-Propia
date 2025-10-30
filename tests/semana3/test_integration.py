"""
Pruebas de integración para Semana 3
====================================

Este módulo contiene las pruebas de integración para verificar que
todas las funcionalidades de la Semana 3 trabajan juntas correctamente.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from langchain.schema import Document
from app.services.chunking_service import ChunkingService, ChunkingStrategy
from app.services.retrieval_service import RetrievalService
from app.services.generation_service import GenerationService
from app.services.embedding_service import EmbeddingService


class TestSemana3Integration:
    """Pruebas de integración para todas las funcionalidades de Semana 3."""
    
    def test_full_pipeline_with_preprocessing(self):
        """Prueba el pipeline completo con preprocesamiento."""
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Crear estructura de colección
            collection_dir = temp_path / "test_collection"
            collection_dir.mkdir()
            
            # Crear un PDF de prueba
            test_pdf = collection_dir / "test_document.pdf"
            test_pdf.write_text("Contenido de prueba para convocatorias de investigación.")
            
            # Inicializar servicios
            chunking_service = ChunkingService(
                strategy=ChunkingStrategy.RECURSIVE_CHARACTER,
                chunk_size=500,
                chunk_overlap=100
            )
            
            # Procesar colección
            chunks = chunking_service.process_collection("test_collection")
            
            # Verificar que se generaron chunks
            assert len(chunks) > 0
            
            # Verificar metadatos de preprocesamiento
            for chunk in chunks:
                assert "preprocessed" in chunk.metadata
                assert "processed_path" in chunk.metadata
    
    def test_reranking_integration(self):
        """Prueba la integración del reranking."""
        retrieval_service = RetrievalService()
        
        # Crear documentos de prueba
        documents = [
            Document(
                page_content="Documento sobre convocatorias de investigación en ciencias exactas.",
                metadata={"source_file": "doc1.pdf", "chunk_index": 0}
            ),
            Document(
                page_content="Información sobre financiación de proyectos de desarrollo tecnológico.",
                metadata={"source_file": "doc2.pdf", "chunk_index": 1}
            ),
            Document(
                page_content="Requisitos y condiciones para participar en programas de innovación.",
                metadata={"source_file": "doc3.pdf", "chunk_index": 2}
            )
        ]
        
        query = "¿Cuáles son los requisitos para las convocatorias de investigación?"
        
        # Aplicar reranking
        reranked_docs = retrieval_service.rerank_documents(
            query=query,
            documents=documents,
            top_n=2
        )
        
        # Verificar resultados
        assert len(reranked_docs) == 2
        assert all("rerank_score" in doc.metadata for doc in reranked_docs)
        assert all("rerank_position" in doc.metadata for doc in reranked_docs)
    
    def test_query_rewriting_integration(self):
        """Prueba la integración de query rewriting."""
        generation_service = GenerationService(use_local=True)
        
        # Probar diferentes tipos de consultas
        test_queries = [
            "convocatoria",
            "proyecto investigación",
            "financiación desarrollo",
            "requisitos participación"
        ]
        
        for query in test_queries:
            rewritten = generation_service.rewrite_query(query)
            assert rewritten is not None
            assert isinstance(rewritten, str)
            assert len(rewritten) > 0
    
    def test_end_to_end_pipeline(self):
        """Prueba el pipeline completo de extremo a extremo."""
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Crear estructura de colección
            collection_dir = temp_path / "test_collection"
            collection_dir.mkdir()
            
            # Crear un PDF de prueba
            test_pdf = collection_dir / "test_document.pdf"
            test_pdf.write_text("""
            CONVOCATORIA 970 PARA LA CONFORMACIÓN DE UN LISTADO DE PROYECTOS DE I+D+I
            
            La presente convocatoria tiene como objetivo seleccionar proyectos de investigación
            y desarrollo tecnológico en las áreas de ciencias exactas, naturales y sociales.
            
            REQUISITOS:
            - Ser investigador principal con título de doctorado
            - Tener experiencia mínima de 5 años en investigación
            - Presentar propuesta de investigación original
            """)
            
            # Inicializar servicios
            chunking_service = ChunkingService(
                strategy=ChunkingStrategy.RECURSIVE_CHARACTER,
                chunk_size=300,
                chunk_overlap=50
            )
            
            retrieval_service = RetrievalService()
            generation_service = GenerationService(use_local=True)
            
            # 1. Procesar colección
            chunks = chunking_service.process_collection("test_collection")
            assert len(chunks) > 0
            
            # 2. Simular búsqueda de similitud
            query = "¿Cuáles son los requisitos para participar?"
            retrieved_docs = chunks[:3]  # Simular top 3 documentos
            
            # 3. Aplicar reranking
            reranked_docs = retrieval_service.rerank_documents(
                query=query,
                documents=retrieved_docs,
                top_n=2
            )
            assert len(reranked_docs) == 2
            
            # 4. Generar respuesta
            response = generation_service.generate_response(
                question=query,
                retrieved_docs=reranked_docs
            )
            
            # Verificar respuesta
            assert "answer" in response
            assert "sources" in response
            assert len(response["answer"]) > 0
    
    def test_error_handling_integration(self):
        """Prueba el manejo de errores en el pipeline completo."""
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Crear estructura de colección vacía
            collection_dir = temp_path / "empty_collection"
            collection_dir.mkdir()
            
            # Inicializar servicios
            chunking_service = ChunkingService()
            retrieval_service = RetrievalService()
            generation_service = GenerationService(use_local=True)
            
            # Probar con colección vacía
            chunks = chunking_service.process_collection("empty_collection")
            assert len(chunks) == 0
            
            # Probar reranking con documentos vacíos
            reranked_docs = retrieval_service.rerank_documents(
                query="consulta de prueba",
                documents=[],
                top_n=5
            )
            assert len(reranked_docs) == 0
            
            # Probar generación con documentos vacíos
            response = generation_service.generate_response(
                question="consulta de prueba",
                retrieved_docs=[]
            )
            assert "answer" in response
            assert len(response["answer"]) > 0  # Debe generar respuesta de "no hay información"
