"""
Servicio de Chunking para el Sistema RAG
========================================

Este módulo implementa la funcionalidad de dividir documentos en fragmentos (chunks)
más pequeños y manejables para su procesamiento en el sistema RAG.

TAREAS SEMANA 2:
- Implementar al menos 2 estrategias de chunking de las 5 disponibles
- Seleccionar las estrategias según las necesidades de tu caso de uso
- Cargar documentos desde la colección
- Aplicar chunking a los documentos
- Retornar chunks con metadatos enriquecidos

TAREAS SEMANA 3:
- Implementar preprocesamiento de PDFs a Markdown usando markitdown
- Integrar el preprocesamiento antes del chunking

TUTORIALES:
- RAG paso a paso, parte 1: ingesta y estrategias de chunking
"""

from enum import Enum
from typing import List, Dict, Any
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pypdf import PdfReader


class ChunkingStrategy(str, Enum):
    """Estrategias de chunking disponibles"""
    RECURSIVE_CHARACTER = "recursive_character"
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    DOCUMENT_STRUCTURE = "document_structure"
    LINGUISTIC_UNITS = "linguistic_units"


class ChunkingService:
    """
    Servicio para segmentar documentos en chunks usando diferentes estrategias.
    
    IMPLEMENTACIÓN REQUERIDA:
    - __init__: Inicializar la estrategia de chunking seleccionada
    - Crear métodos para tus 2 estrategias de chunking elegidas (ej: _create_X_splitter)
    - _preprocess_pdf_to_markdown: Preprocesar PDFs con markitdown (Semana 3)
    - load_documents_from_collection: Cargar documentos aplicando preprocesamiento (Semana 3)
    - process_collection: Aplicar chunking a una colección completa
    """
    
    def __init__(
        self, 
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE_CHARACTER, #Ejemplo
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
        # Parámetros específicos para Semantic Chunking
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_amount: int = 95,
        semantic_embeddings_model: str = "models/embedding-001",
        semantic_similarity_threshold: float = 0.7,
        semantic_min_chunk_size: int = 200,
        semantic_max_chunk_size: int = 2000,
        # Parámetros específicos para Fixed Size Chunking
        fixed_size_separators: List[str] = None,
        fixed_size_keep_separator: bool = True,
        fixed_size_strip_whitespace: bool = True,
        fixed_size_length_function: str = "character_count",
        fixed_size_min_chunk_size: int = 100,
        fixed_size_max_chunk_size: int = 1200
    ):
        """
        Inicializa el servicio de chunking con la estrategia seleccionada.
        
        CONFIGURACIÓN RAGAS COMPLETA:
        - Parámetros básicos: strategy, chunk_size, chunk_overlap, separators
        - Parámetros Semantic: breakpoint_threshold_type, semantic_embeddings_model, etc.
        - Parámetros Fixed Size: fixed_size_separators, fixed_size_keep_separator, etc.
        
        Args:
            strategy: Estrategia de chunking a utilizar
            chunk_size: Tamaño máximo de cada chunk
            chunk_overlap: Solapamiento entre chunks
            separators: Lista de separadores básicos
            # Parámetros específicos para Semantic Chunking
            breakpoint_threshold_type: Tipo de umbral para semantic chunking
            breakpoint_threshold_amount: Valor del umbral (95 para percentile)
            semantic_embeddings_model: Modelo de embeddings para semantic
            semantic_similarity_threshold: Umbral de similitud semántica
            semantic_min_chunk_size: Tamaño mínimo para semantic chunks
            semantic_max_chunk_size: Tamaño máximo para semantic chunks
            # Parámetros específicos para Fixed Size Chunking
            fixed_size_separators: Separadores específicos para fixed size
            fixed_size_keep_separator: Mantener separadores en chunks
            fixed_size_strip_whitespace: Eliminar espacios en blanco
            fixed_size_length_function: Función de conteo (character_count/token_count)
            fixed_size_min_chunk_size: Tamaño mínimo para fixed size chunks
            fixed_size_max_chunk_size: Tamaño máximo para fixed size chunks
        """
        # Guardar parámetros básicos
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
        
        # Guardar parámetros específicos para Semantic Chunking
        self.breakpoint_threshold_type = breakpoint_threshold_type
        self.breakpoint_threshold_amount = breakpoint_threshold_amount
        self.semantic_embeddings_model = semantic_embeddings_model
        self.semantic_similarity_threshold = semantic_similarity_threshold
        self.semantic_min_chunk_size = semantic_min_chunk_size
        self.semantic_max_chunk_size = semantic_max_chunk_size
        
        # Guardar parámetros específicos para Fixed Size Chunking
        self.fixed_size_separators = fixed_size_separators or ["\n\n", "\n", " ", ""]
        self.fixed_size_keep_separator = fixed_size_keep_separator
        self.fixed_size_strip_whitespace = fixed_size_strip_whitespace
        self.fixed_size_length_function = fixed_size_length_function
        self.fixed_size_min_chunk_size = fixed_size_min_chunk_size
        self.fixed_size_max_chunk_size = fixed_size_max_chunk_size
        
        # Inicializar splitter según la estrategia
        self.splitter = self._create_splitter()
    
    # ===========================================
    # IMPLEMENTACIÓN DE ESTRATEGIAS DE CHUNKING
    # ===========================================
    
    def _create_splitter(self):
        """
        Crea el splitter según la estrategia seleccionada.
        
        Returns:
            Splitter configurado para la estrategia elegida
        """
        if self.strategy == ChunkingStrategy.RECURSIVE_CHARACTER:
            return self._create_recursive_character_splitter()
        elif self.strategy == ChunkingStrategy.SEMANTIC:
            return self._create_semantic_splitter()
        elif self.strategy == ChunkingStrategy.FIXED_SIZE:
            return self._create_fixed_size_splitter()
        else:
            # Fallback a recursive character
            return self._create_recursive_character_splitter()
    
    def _create_recursive_character_splitter(self):
        """
        Crea un splitter recursivo por caracteres.
        
        Returns:
            RecursiveCharacterTextSplitter configurado
        """
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False
        )
    
    def _create_semantic_splitter(self):
        """
        Crea un splitter semántico usando embeddings.
        
        CONFIGURACIÓN RAGAS COMPLETA:
        - breakpoint_threshold_type: Tipo de umbral (percentile/standard_deviation)
        - breakpoint_threshold_amount: Valor del umbral (95 para percentile)
        - semantic_embeddings_model: Modelo de embeddings específico
        - semantic_similarity_threshold: Umbral de similitud semántica (0.7)
        - semantic_min_chunk_size: Tamaño mínimo de chunk (200)
        - semantic_max_chunk_size: Tamaño máximo de chunk (2000)
        
        Returns:
            SemanticChunker configurado con parámetros específicos
        """
        # Para semantic chunking necesitamos embeddings
        # Usamos Google AI embeddings como en el resto del sistema
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        # Configuración específica para embeddings semánticos
        embeddings_model = getattr(self, 'semantic_embeddings_model', "models/embedding-001")
        breakpoint_type = getattr(self, 'breakpoint_threshold_type', "percentile")
        breakpoint_amount = getattr(self, 'breakpoint_threshold_amount', 95)
        
        embeddings = GoogleGenerativeAIEmbeddings(model=embeddings_model)
        
        return SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=breakpoint_type,
            breakpoint_threshold_amount=breakpoint_amount
        )
    
    def _create_fixed_size_splitter(self):
        """
        Crea un splitter de tamaño fijo.
        
        CONFIGURACIÓN RAGAS COMPLETA:
        - fixed_size_separators: Separadores específicos para fixed size
        - fixed_size_keep_separator: Mantener separadores en chunks
        - fixed_size_strip_whitespace: Eliminar espacios en blanco
        - fixed_size_length_function: Función de conteo (character_count/token_count)
        - fixed_size_min_chunk_size: Tamaño mínimo de chunk (100)
        - fixed_size_max_chunk_size: Tamaño máximo de chunk (1200)
        
        Returns:
            RecursiveCharacterTextSplitter configurado para tamaño fijo
        """
        # Configuración específica para fixed size
        separators = getattr(self, 'fixed_size_separators', ["\n\n", "\n", " ", ""])
        keep_separator = getattr(self, 'fixed_size_keep_separator', True)
        strip_whitespace = getattr(self, 'fixed_size_strip_whitespace', True)
        
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
            keep_separator=keep_separator,
            strip_whitespace=strip_whitespace
        )
    
    def _preprocess_pdf_to_markdown(self, pdf_path: Path) -> Path:
        """
        Convierte un archivo PDF a Markdown usando markitdown.
        
        TODO SEMANA 3:
        - Importar markitdown (MarkItDown)
        - Convertir el PDF a texto Markdown
        - Guardar el .md en el mismo directorio que el PDF
        - Retornar ruta al .md si tiene éxito, o ruta al PDF si falla (fallback)
        - Manejar errores (ImportError, excepciones generales)
        
        NOTA: Este paso mejora la extracción de texto de PDFs.
        Revisen si sus resultados son mejores con este preprocesamiento para la reflexion.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Path: Ruta al archivo Markdown generado (o PDF original si falla)
        """
        try:
            # Importar markitdown
            from markitdown import MarkItDown
            
            print(f"🔄 Preprocesando PDF a Markdown: {pdf_path.name}")
            
            # Crear instancia de MarkItDown
            md = MarkItDown()
            
            # Convertir PDF a Markdown
            result = md.convert(str(pdf_path))
            
            if result.text_content and result.text_content.strip():
                # Crear ruta para el archivo Markdown
                markdown_path = pdf_path.with_suffix('.md')
                
                # Guardar contenido Markdown
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(result.text_content)
                
                print(f"✅ Markdown generado: {markdown_path.name}")
                print(f"📝 Tamaño del contenido: {len(result.text_content)} caracteres")
                
                return markdown_path
            else:
                print(f"⚠️ MarkItDown no pudo extraer contenido de {pdf_path.name}")
                return pdf_path
                
        except ImportError:
            print("⚠️ MarkItDown no está instalado. Usando PDF directamente.")
            return pdf_path
        except Exception as e:
            print(f"❌ Error en preprocesamiento con MarkItDown: {str(e)}")
            return pdf_path
    
    def load_documents_from_collection(self, collection_name: str) -> List[Document]:
        """
        Carga todos los documentos de una colección.
        
        TODO SEMANA 2:
        - Buscar archivos PDF en ./docs/{collection_name}
        - Extraer texto de cada PDF usando PdfReader
        - Crear objetos Document con page_content y metadata
        - Retornar lista de documentos
        
        TODO SEMANA 3:
        - Antes de cargar el PDF, llamar a _preprocess_pdf_to_markdown()
        - Si retorna un .md, cargar desde el Markdown
        - Si retorna un .pdf, usar PdfReader como fallback
        
        METADATA REQUERIDA:
        - source_file: Nombre del archivo
        - source_path: Ruta completa
        - file_size: Tamaño en bytes
        - preprocessed: True/False (Semana 3)
        
        Args:
            collection_name: Nombre de la colección
            
        Returns:
            Lista de objetos Document con contenido y metadatos
        """
        documents = []
        collection_path = Path(f"./docs/{collection_name}")
        
        if not collection_path.exists():
            print(f"⚠️ Colección {collection_name} no encontrada en {collection_path}")
            return documents
        
        # Buscar archivos PDF en la colección
        pdf_files = list(collection_path.glob("*.pdf"))
        print(f"📄 Encontrados {len(pdf_files)} archivos PDF en {collection_name}")
        
        for pdf_file in pdf_files:
            try:
                print(f"📖 Procesando: {pdf_file.name}")
                
                # SEMANA 3: Preprocesamiento con markitdown
                processed_path = self._preprocess_pdf_to_markdown(pdf_file)
                
                # Extraer texto del archivo procesado (Markdown o PDF)
                if processed_path.suffix == '.md':
                    text_content = self._extract_text_from_markdown(processed_path)
                    preprocessed = True
                else:
                    text_content = self._extract_text_from_pdf(processed_path)
                    preprocessed = False
                
                if text_content.strip():
                    # Crear objeto Document con metadatos
                    doc = Document(
                        page_content=text_content,
                        metadata={
                            "source_file": pdf_file.name,
                            "source_path": str(pdf_file),
                            "file_size": pdf_file.stat().st_size,
                            "preprocessed": preprocessed,  # Semana 3: True si se usó markitdown
                            "processed_path": str(processed_path),  # Ruta del archivo procesado
                            "chunking_strategy": self.strategy.value,
                            "chunk_size": self.chunk_size,
                            "chunk_overlap": self.chunk_overlap
                        }
                    )
                    documents.append(doc)
                    print(f"✅ Procesado exitosamente: {pdf_file.name}")
                else:
                    print(f"⚠️ Archivo vacío o sin texto: {pdf_file.name}")
                    
            except Exception as e:
                print(f"❌ Error procesando {pdf_file.name}: {str(e)}")
                continue
        
        print(f"📊 Total documentos cargados: {len(documents)}")
        return documents
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extrae texto de un archivo PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF
        """
        try:
            reader = PdfReader(pdf_path)
            text_content = ""
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_content += f"\n--- Página {page_num + 1} ---\n"
                    text_content += page_text
            
            return text_content.strip()
            
        except Exception as e:
            print(f"❌ Error extrayendo texto de {pdf_path.name}: {str(e)}")
            return ""
    
    def _extract_text_from_markdown(self, markdown_path: Path) -> str:
        """
        Extrae texto de un archivo Markdown.
        
        Args:
            markdown_path: Ruta al archivo Markdown
            
        Returns:
            Texto extraído del Markdown
        """
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📝 Contenido Markdown extraído: {len(content)} caracteres")
            return content.strip()
            
        except Exception as e:
            print(f"❌ Error extrayendo texto de {markdown_path.name}: {str(e)}")
            return ""
    
    def process_collection(self, collection_name: str) -> List[Document]:
        """
        Procesa una colección completa de documentos aplicando chunking.
        
        TODO SEMANA 2:
        - Llamar a load_documents_from_collection()
        - Para cada documento, aplicar self.splitter
        - Enriquecer cada chunk con metadata adicional:
          * source_file, chunk_index, total_chunks_in_doc
          * chunking_strategy, chunk_size
        - Retornar lista de chunks
        
        NOTA: Este método es llamado por load_documents_service.py
        
        Args:
            collection_name: Nombre de la colección a procesar
            
        Returns:
            Lista de chunks (objetos Document) con metadatos enriquecidos
        """
        print(f"🔄 Iniciando procesamiento de colección: {collection_name}")
        print(f"📋 Estrategia de chunking: {self.strategy.value}")
        print(f"📏 Tamaño de chunk: {self.chunk_size}, Overlap: {self.chunk_overlap}")
        
        # Cargar documentos de la colección
        documents = self.load_documents_from_collection(collection_name)
        
        if not documents:
            print("⚠️ No se encontraron documentos para procesar")
            return []
        
        all_chunks = []
        
        # Procesar cada documento
        for doc_idx, document in enumerate(documents):
            print(f"✂️ Fragmentando documento {doc_idx + 1}/{len(documents)}: {document.metadata['source_file']}")
            
            try:
                # Aplicar chunking al documento
                doc_chunks = self.splitter.split_documents([document])
                
                # Enriquecer metadatos de cada chunk
                for chunk_idx, chunk in enumerate(doc_chunks):
                    # Agregar metadatos específicos del chunk
                    chunk.metadata.update({
                        "chunk_index": chunk_idx,
                        "total_chunks_in_doc": len(doc_chunks),
                        "document_index": doc_idx,
                        "chunk_size": len(chunk.page_content),
                        "chunking_strategy": self.strategy.value,
                        "chunk_size_config": self.chunk_size,
                        "chunk_overlap_config": self.chunk_overlap
                    })
                    
                    all_chunks.append(chunk)
                
                print(f"✅ Documento fragmentado: {len(doc_chunks)} chunks generados")
                
            except Exception as e:
                print(f"❌ Error fragmentando documento {document.metadata['source_file']}: {str(e)}")
                continue
        
        print(f"📊 Procesamiento completado: {len(all_chunks)} chunks totales generados")
        return all_chunks
    
    def get_chunking_statistics(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        Calcula estadísticas sobre los chunks generados.
        
        TODO SEMANA 2:
        - Calcular tamaño promedio, mínimo y máximo de chunks
        - Contar chunks con overlap
        - Calcular total de caracteres procesados
        
        Args:
            chunks: Lista de chunks procesados
            
        Returns:
            Diccionario con estadísticas de chunking
        """
        if not chunks:
            return {
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "chunks_with_overlap": 0,
                "total_characters_processed": 0,
                "total_chunks": 0,
                "strategy_used": self.strategy.value
            }
        
        # Calcular estadísticas básicas
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        total_chars = sum(chunk_sizes)
        
        # Contar chunks con overlap (basado en metadata)
        chunks_with_overlap = sum(1 for chunk in chunks 
                                if chunk.metadata.get("chunk_overlap_config", 0) > 0)
        
        # Agrupar por documento para análisis adicional
        docs_chunks = {}
        for chunk in chunks:
            source_file = chunk.metadata.get("source_file", "unknown")
            if source_file not in docs_chunks:
                docs_chunks[source_file] = []
            docs_chunks[source_file].append(chunk)
        
        # Calcular estadísticas por documento
        doc_stats = {}
        for doc_name, doc_chunks in docs_chunks.items():
            doc_sizes = [len(chunk.page_content) for chunk in doc_chunks]
            doc_stats[doc_name] = {
                "chunk_count": len(doc_chunks),
                "avg_size": sum(doc_sizes) / len(doc_sizes) if doc_sizes else 0,
                "min_size": min(doc_sizes) if doc_sizes else 0,
                "max_size": max(doc_sizes) if doc_sizes else 0
            }
        
        statistics = {
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
            "chunks_with_overlap": chunks_with_overlap,
            "total_characters_processed": total_chars,
            "total_chunks": len(chunks),
            "strategy_used": self.strategy.value,
            "chunk_size_config": self.chunk_size,
            "chunk_overlap_config": self.chunk_overlap,
            "documents_processed": len(docs_chunks),
            "documents_statistics": doc_stats
        }
        
        print(f"📊 Estadísticas de chunking:")
        print(f"   • Total chunks: {statistics['total_chunks']}")
        print(f"   • Tamaño promedio: {statistics['avg_chunk_size']:.1f} caracteres")
        print(f"   • Tamaño mínimo: {statistics['min_chunk_size']} caracteres")
        print(f"   • Tamaño máximo: {statistics['max_chunk_size']} caracteres")
        print(f"   • Total caracteres: {statistics['total_characters_processed']:,}")
        print(f"   • Estrategia: {statistics['strategy_used']}")
        
        return statistics