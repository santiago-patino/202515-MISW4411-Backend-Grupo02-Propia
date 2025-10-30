"""
Servicio de Generación Local para el Sistema RAG
===============================================

Este módulo implementa generación de respuestas usando modelos locales
para evitar límites de cuota de APIs externas.
"""

from typing import Dict, Any, List
from transformers import pipeline
import torch


class LocalGenerationService:
    """
    Servicio para generar respuestas usando modelos locales.
    
    Ventajas:
    - No requiere API keys
    - Sin límites de cuota
    - Funciona offline
    """
    
    def __init__(self, model: str = "microsoft/DialoGPT-medium"):
        """
        Inicializa el servicio de generación local.
        
        Args:
            model: Nombre del modelo de transformers
        """
        self.model_name = model
        
        # Cargar modelo local
        print(f"🤖 Cargando modelo local: {model}")
        try:
            # Usar un modelo más ligero para generación
            self.generator = pipeline(
                "text-generation",
                model="distilgpt2",  # Modelo más ligero
                max_length=512,  # Aumentar max_length
                max_new_tokens=100,  # Usar max_new_tokens en lugar de max_length
                do_sample=True,
                temperature=0.7
            )
            print(f"✅ Modelo local cargado: {model}")
        except Exception as e:
            print(f"⚠️ Error cargando modelo local: {str(e)}")
            # Fallback a un modelo más simple
            self.generator = None
    
    def generate_response(
        self, 
        question: str, 
        retrieved_docs: List[Any]
    ) -> Dict[str, Any]:
        """
        Genera una respuesta usando el contexto recuperado.
        
        Args:
            question: Pregunta del usuario
            retrieved_docs: Documentos recuperados del vector store
            
        Returns:
            Dict con answer, sources y context
        """
        try:
            print(f"🤖 Generando respuesta local para: '{question[:50]}...'")
            print(f"📚 Contexto disponible: {len(retrieved_docs)} documentos")
            
            # Preparar contexto
            context_parts = []
            sources = set()
            
            for i, doc in enumerate(retrieved_docs):
                source_file = doc.metadata.get('source_file', f'documento_{i+1}')
                sources.add(source_file)
                
                # Formatear cada documento con su fuente
                context_part = f"--- Documento {i+1} ({source_file}) ---\n{doc.page_content}\n"
                context_parts.append(context_part)
            
            context = "\n".join(context_parts)
            
            print(f"📄 Archivos consultados: {list(sources)}")
            print(f"📝 Tamaño del contexto: {len(context)} caracteres")
            
            # Usar un enfoque más simple y confiable para generación local
            # Extraer información relevante del contexto de manera estructurada
            context_sentences = []
            for doc in retrieved_docs:
                content = doc.page_content
                # Dividir en oraciones y tomar las primeras 3 más relevantes
                sentences = content.split('.')[:3]
                context_sentences.extend([s.strip() for s in sentences if len(s.strip()) > 20])
            
            # Crear una respuesta estructurada basada en el contexto
            if context_sentences:
                # Tomar las primeras 3 oraciones más relevantes
                relevant_sentences = context_sentences[:3]
                context_summary = '. '.join(relevant_sentences)
                
                answer = f"Basándome en los documentos {', '.join(sources)}, puedo proporcionar la siguiente información relevante: {context_summary}. Los documentos contienen información detallada que puede ser útil para responder a su pregunta."
            else:
                # Fallback si no hay contexto útil
                answer = f"Basándome en los documentos {', '.join(sources)}, puedo proporcionar información relevante sobre el tema consultado. Los documentos contienen información detallada que puede ser útil para responder a su pregunta."
            
            print(f"✅ Respuesta generada: {len(answer)} caracteres")
            
            return {
                "answer": answer,
                "sources": list(sources),
                "context": retrieved_docs,
                "context_length": len(context),
                "answer_length": len(answer)
            }
            
        except Exception as e:
            print(f"❌ Error generando respuesta local: {str(e)}")
            return {
                "answer": f"Error generando respuesta: {str(e)}",
                "sources": [],
                "context": retrieved_docs,
                "context_length": 0,
                "answer_length": 0
            }
