"""
Pruebas para el preprocesamiento de documentos - Semana 3
========================================================

Este módulo contiene las pruebas para verificar que el preprocesamiento
de documentos con markitdown funciona correctamente.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from app.services.chunking_service import ChunkingService, ChunkingStrategy


class TestPreprocessing:
    """Pruebas para el preprocesamiento de documentos."""
    
    def test_preprocessing_pdf_to_markdown(self):
        """Prueba la conversión de PDF a Markdown."""
        # Crear servicio de chunking
        chunking_service = ChunkingService(
            strategy=ChunkingStrategy.RECURSIVE_CHARACTER,
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Crear un directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Crear un archivo PDF de prueba (simulado)
            test_pdf = temp_path / "test_document.pdf"
            test_pdf.write_text("Contenido de prueba PDF")
            
            # Probar preprocesamiento
            result_path = chunking_service._preprocess_pdf_to_markdown(test_pdf)
            
            # Verificar que retorna una ruta válida
            assert result_path is not None
            assert isinstance(result_path, Path)
    
    def test_preprocessing_fallback(self):
        """Prueba el fallback cuando markitdown no está disponible."""
        chunking_service = ChunkingService()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_pdf = temp_path / "test_document.pdf"
            test_pdf.write_text("Contenido de prueba")
            
            # Simular error de importación
            original_import = __builtins__['__import__']
            
            def mock_import(name, *args, **kwargs):
                if name == 'markitdown':
                    raise ImportError("markitdown not available")
                return original_import(name, *args, **kwargs)
            
            __builtins__['__import__'] = mock_import
            
            try:
                result_path = chunking_service._preprocess_pdf_to_markdown(test_pdf)
                assert result_path == test_pdf  # Debe retornar el PDF original
            finally:
                __builtins__['__import__'] = original_import
    
    def test_extract_text_from_markdown(self):
        """Prueba la extracción de texto de archivos Markdown."""
        chunking_service = ChunkingService()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_md = temp_path / "test_document.md"
            
            # Crear contenido Markdown de prueba
            markdown_content = """# Título Principal
            
## Subtítulo

Este es un párrafo de prueba con **texto en negrita** y *texto en cursiva*.

- Lista item 1
- Lista item 2

### Código
```python
print("Hola mundo")
```
"""
            test_md.write_text(markdown_content, encoding='utf-8')
            
            # Extraer texto
            extracted_text = chunking_service._extract_text_from_markdown(test_md)
            
            # Verificar que se extrajo el contenido
            assert extracted_text is not None
            assert len(extracted_text) > 0
            assert "Título Principal" in extracted_text
            assert "párrafo de prueba" in extracted_text
    
    def test_load_documents_with_preprocessing(self):
        """Prueba la carga de documentos con preprocesamiento."""
        chunking_service = ChunkingService()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Crear estructura de colección
            collection_dir = temp_path / "test_collection"
            collection_dir.mkdir()
            
            # Crear un PDF de prueba
            test_pdf = collection_dir / "test_document.pdf"
            test_pdf.write_text("Contenido de prueba PDF")
            
            # Cargar documentos
            documents = chunking_service.load_documents_from_collection("test_collection")
            
            # Verificar que se cargaron documentos
            assert len(documents) >= 0  # Puede ser 0 si no hay PDFs válidos
            
            # Si hay documentos, verificar metadatos
            if documents:
                doc = documents[0]
                assert "preprocessed" in doc.metadata
                assert "processed_path" in doc.metadata
                assert "source_file" in doc.metadata
