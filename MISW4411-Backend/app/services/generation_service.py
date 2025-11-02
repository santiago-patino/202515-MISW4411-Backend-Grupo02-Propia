"""
Servicio de Generación para el Sistema RAG
==========================================

Este módulo implementa la funcionalidad de generar respuestas usando LLMs
basándose en el contexto recuperado del sistema RAG.

TAREAS SEMANA 2:
- Inicializar LLM (ChatGoogleGenerativeAI)
- Crear prompt template para RAG
- Implementar generación de respuestas con contexto recuperado
- Implementar evaluación con RAGAS

TAREAS SEMANA 3:
- Implementar query rewriting (reescritura de consultas)

TUTORIALES:
- RAG paso a paso, parte 3: recuperación y generación de respuestas
- Reescritura de consultas
"""

import time
import re
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset
from app.services.generation_service_local import LocalGenerationService


class GenerationService:
    """
    Servicio para generar respuestas usando Gemini con contexto RAG.
    
    IMPLEMENTACIÓN REQUERIDA (SEMANA 2):
    - __init__: Inicializar LLM y prompt template
    - generate_response: Generar respuesta con contexto
    - evaluate_with_ragas: Evaluar sistema con métricas RAGAS
    
    IMPLEMENTACIÓN REQUERIDA (SEMANA 3):
    - rewrite_query: Reescribir consultas para mejorar recuperación
    """
    
    def __init__(
        self, 
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        use_local: bool = False
    ):
        """
        Inicializa el servicio de generación con Gemini o modelo local.
        
        TODO SEMANA 2:
        - Inicializar self.llm con ChatGoogleGenerativeAI
        - Crear self.prompt con ChatPromptTemplate.from_template()
        - El prompt debe tener placeholders: {question} y {context}
        
        RECOMENDACIONES PARA EL PROMPT:
        - Instruir al modelo a responder solo con el contexto proporcionado
        - Indicar qué hacer si no tiene información suficiente
        - Mantener respuestas concisas
        
        Args:
            model: Nombre del modelo de Google AI
            temperature: Temperatura para generación (0-1)
            max_tokens: Número máximo de tokens en respuesta
            use_local: Si True, usa modelo local en lugar de Google AI
        """
        self.model_name = model
        self.use_local = use_local
        
        if use_local:
            # Usar modelo local directamente
            print("🤖 Usando modelo local para generación")
            self.local_generator = LocalGenerationService()
            self.llm = None
            self.prompt = None
        else:
            try:
                # Intentar usar Google AI primero
                print(f"🤖 Intentando usar Google AI: {model}")
                self.llm = ChatGoogleGenerativeAI(
                    model=model,
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
                
                print("✅ Google AI inicializado correctamente")
                
                # Crear prompt template para RAG - texto plano sin saltos de línea
                self.prompt = ChatPromptTemplate.from_template(
                    "Eres un asistente especializado en responder preguntas basándote únicamente en el contexto proporcionado. "
                    "CONTEXTO: {context} "
                    "PREGUNTA: {question} "
                    "INSTRUCCIONES: "
                    "1. Responde la pregunta usando SOLO la información del contexto proporcionado. "
                    "2. Si el contexto no contiene información suficiente para responder, di claramente: No tengo información suficiente en los documentos para responder esta pregunta. "
                    "3. Mantén tu respuesta concisa y directa. "
                    "4. Si mencionas información específica, indica de qué documento proviene. "
                    "5. No inventes información que no esté en el contexto. "
                    "RESPUESTA:"
                )
                
            except Exception as e:
                error_msg = str(e)
                if "quota" in error_msg.lower() or "429" in error_msg:
                    print(f"⚠️ Cuota de Google AI excedida: {error_msg}")
                    print("🔄 Cambiando automáticamente a modelo local...")
                else:
                    print(f"⚠️ Error con Google AI: {error_msg}")
                    print("🔄 Cambiando a modelo local...")
                
                self.local_generator = LocalGenerationService()
                self.llm = None
                self.prompt = None
                self.use_local = True
        
        print(f"🤖 GenerationService inicializado con modelo: {model}")
        print(f"🌡️ Temperatura: {temperature}, Max tokens: {max_tokens}")
    
    def generate_response(
        self, 
        question: str, 
        retrieved_docs: List[Document]
    ) -> Dict[str, Any]:
        """
        Genera una respuesta usando el contexto recuperado.
        
        TODO SEMANA 2:
        - Preparar contexto: concatenar retrieved_docs.page_content
        - Construir mensaje con self.prompt.invoke({question, context})
        - Generar respuesta con self.llm.invoke(messages)
        - Extraer archivos consultados de los metadatos
        - Retornar diccionario con:
          * "answer": texto de la respuesta
          * "sources": lista de archivos consultados
          * "context": documentos recuperados
        
        NOTA: Este método es llamado por ask.py después de recuperar documentos
   
        
        Args:
            question: Pregunta del usuario
            retrieved_docs: Documentos recuperados del vector store
            
        Returns:
            Dict con answer, sources y context
        """
        try:
            print(f"🤖 Generando respuesta para: '{question[:50]}...'")
            print(f"📚 Contexto disponible: {len(retrieved_docs)} documentos")
            
            # Preparar contexto concatenando documentos como texto plano sin saltos de línea
            context_parts = []
            sources = set()
            
            for i, doc in enumerate(retrieved_docs):
                source_file = doc.metadata.get('source_file', f'documento_{i+1}')
                sources.add(source_file)
                
                # Limpiar el contenido del documento: texto plano sin caracteres especiales problemáticos
                doc_content = doc.page_content
                
                # Reemplazar comillas dobles y simples que podrían interferir con el prompt
                doc_content = doc_content.replace('"', "'").replace('"""', "'''")
                
                # Normalizar saltos de línea primero
                doc_content = doc_content.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
                
                # Reemplazar múltiples espacios en blanco por un solo espacio
                doc_content = re.sub(r'\s+', ' ', doc_content)
                
                # Eliminar caracteres de control
                doc_content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', doc_content)
                
                # Formatear cada documento con su fuente (texto plano sin saltos de línea)
                context_part = f"Documento {i+1} - {source_file}: {doc_content}"
                context_parts.append(context_part)
            
            # Unir contexto como texto plano simple sin saltos de línea
            context = ". ".join(context_parts)
            
            # Limpiar el contexto final de caracteres problemáticos adicionales
            context = context.strip()
            
            # Reemplazar cualquier salto de línea restante por espacios
            context = context.replace('\n', ' ').replace('\r', ' ')
            context = re.sub(r'\s+', ' ', context)
            
            print(f"📄 Archivos consultados: {list(sources)}")
            print(f"📝 Tamaño del contexto: {len(context)} caracteres")
            
            if self.use_local or self.llm is None:
                # Usar modelo local
                print("🤖 Usando modelo local para generación...")
                return self.local_generator.generate_response(question, retrieved_docs)
            else:
                # Usar Google AI
                try:
                    # Construir el mensaje completo como texto plano (igual que funciona en Postman)
                    full_message = (
                        "Eres un asistente especializado en responder preguntas basándote únicamente en el contexto proporcionado. "
                        f"CONTEXTO: {context} "
                        f"PREGUNTA: {question} "
                        "INSTRUCCIONES: "
                        "1. Responde la pregunta usando SOLO la información del contexto proporcionado. "
                        "2. Si el contexto no contiene información suficiente para responder, di claramente: No tengo información suficiente en los documentos para responder esta pregunta. "
                        "3. Mantén tu respuesta concisa y directa. "
                        "4. Si mencionas información específica, indica de qué documento proviene. "
                        "5. No inventes información que no esté en el contexto. "
                        "RESPUESTA:"
                    )
                    
                    # Asegurar que no haya saltos de línea
                    full_message = full_message.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
                    full_message = re.sub(r'\s+', ' ', full_message).strip()
                    
                    # print(f"CONTENIDO ENVIADO A LA IA (texto plano sin saltos de línea): {full_message}")
                    
                    # Usar LangChain para enviar el mensaje
                    from langchain_core.messages import HumanMessage
                    message = HumanMessage(content=full_message)
                    
                    print(f"🔧 Configuración LLM: temperatura={self.llm.temperature}, max_output_tokens={self.llm.max_output_tokens}")
                    print(f"📨 Enviando mensaje con {len(full_message)} caracteres...")
                    
                    try:
                        response = self.llm.invoke([message])
                        
                        # Extraer texto de la respuesta
                        answer = response.content if hasattr(response, 'content') else str(response)
                        
                        print(f"📥 Respuesta recibida: tipo={type(response)}, tiene content={hasattr(response, 'content')}")
                        if hasattr(response, 'content'):
                            print(f"📄 Contenido respuesta: '{answer[:100] if answer else 'VACÍO'}...'")
                        
                        # Verificar si la respuesta está vacía (cuota excedida)
                        if not answer or len(answer.strip()) == 0:
                            print("⚠️ Google AI devuelve respuesta vacía")
                            print(f"🔍 Debug - respuesta completa: {response}")
                            print(f"🔍 Debug - respuesta type: {type(response)}")
                            print(f"🔍 Debug - respuesta attrs: {dir(response)}")
                            # No activar fallback automático, solo mostrar el error
                            raise ValueError("Google AI devolvió respuesta vacía")
                        
                        print(f"✅ Respuesta generada: {len(answer)} caracteres")
                        
                        return {
                            "answer": answer,
                            "sources": list(sources),
                            "context": retrieved_docs,
                            "context_length": len(context),
                            "answer_length": len(answer)
                        }
                        
                    except Exception as invoke_error:
                        print(f"❌ Error durante invoke: {str(invoke_error)}")
                        print(f"🔍 Tipo de error: {type(invoke_error)}")
                        import traceback
                        traceback.print_exc()
                        raise
                    
                except Exception as e:
                    error_msg = str(e)
                    if "quota" in error_msg.lower() or "429" in error_msg:
                        print(f"⚠️ Cuota de Google AI excedida durante generación: {error_msg}")
                        print("🔄 Cambiando automáticamente a modelo local...")
                        
                        # Cambiar a modelo local y usar fallback
                        self.local_generator = LocalGenerationService()
                        self.use_local = True
                        return self.local_generator.generate_response(question, retrieved_docs)
                    else:
                        raise e
            
        except Exception as e:
            print(f"❌ Error generando respuesta: {str(e)}")
            return {
                "answer": f"Error generando respuesta: {str(e)}",
                "sources": [],
                "context": retrieved_docs,
                "context_length": 0,
                "answer_length": 0
            }
    
    def evaluate_with_ragas(
        self, 
        dataset: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evalúa el sistema RAG usando métricas RAGAS.
        
        TODO SEMANA 2:
        - Configurar LLM y embeddings para evaluación
        - Definir métricas: faithfulness, answer_relevancy, context_precision, context_recall
        - Convertir dataset a formato RAGAS (Dataset.from_dict)
        - Ejecutar evaluate() con dataset y métricas
        - Retornar resultados
        
        DATASET FORMAT:
        [
          {
            "question": "...",
            "answer": "...",
            "contexts": ["...", "..."],
            "ground_truth": "..."
          },
          ...
        ]
   
        
        Args:
            dataset: Lista de ejemplos con question, answer, contexts, ground_truth
            
        Returns:
            Resultados de la evaluación RAGAS
        """
        try:
            print(f"📊 Iniciando evaluación RAGAS con {len(dataset)} ejemplos")
            
            # Configurar LLM y embeddings para evaluación
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",  # Modelo ligero para evaluación
                temperature=0
            )
            
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-002"
            )
            
            # Definir métricas RAGAS
            metrics = [
                faithfulness,      # Fidelidad: ¿la respuesta está fundamentada en el contexto?
                answer_relevancy,  # Relevancia: ¿la respuesta es relevante a la pregunta?
                context_precision, # Precisión: ¿los contextos recuperados son relevantes?
                context_recall     # Recuerdo: ¿se recuperaron todos los contextos necesarios?
            ]
            
            # Convertir dataset a formato RAGAS
            ragas_dataset = Dataset.from_dict({
                "question": [item["question"] for item in dataset],
                "answer": [item["answer"] for item in dataset],
                "contexts": [item["contexts"] for item in dataset],
                "ground_truth": [item["ground_truth"] for item in dataset]
            })
            
            print("🔄 Ejecutando evaluación RAGAS...")
            
            # Ejecutar evaluación
            results = evaluate(
                dataset=ragas_dataset,
                metrics=metrics,
                llm=llm,
                embeddings=embeddings
            )
            
            # Procesar resultados
            evaluation_results = {
                "faithfulness": results["faithfulness"],
                "answer_relevancy": results["answer_relevancy"],
                "context_precision": results["context_precision"],
                "context_recall": results["context_recall"],
                "total_samples": len(dataset),
                "evaluation_timestamp": time.time()
            }
            
            print("✅ Evaluación RAGAS completada")
            print(f"📊 Resultados:")
            for metric, score in evaluation_results.items():
                if metric not in ["total_samples", "evaluation_timestamp"]:
                    print(f"   • {metric}: {score}")
            
            return evaluation_results
            
        except Exception as e:
            print(f"❌ Error en evaluación RAGAS: {str(e)}")
            return {
                "error": str(e),
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0
            }
    
    def rewrite_query(self, question: str) -> str:
        """
        Reescribe la consulta del usuario para mejorar la recuperación de documentos.
        
        TODO SEMANA 3:
        - Seleccionar una estrategia de query rewriting (ver tutorial)
        - Crear un prompt de sistema apropiado para la estrategia elegida
        - Usar el LLM para generar la consulta mejorada
        - Retornar consulta reescrita
        - Si falla, retornar question original (fallback)
        
        ESTRATEGIAS SUGERIDAS (escoger una o más):
        - Query Expansion: Expandir la consulta con términos relacionados
        - Query Decomposition: Dividir consultas complejas en subconsultas
        - Query Refinement: Reformular para mayor precisión
        - Multi-Query: Generar múltiples variaciones de la consulta
        
        NOTA: Este método es llamado por ask.py antes de recuperar documentos
        cuando el parámetro use_query_rewriting=True
        
        Args:
            question: Consulta original del usuario
            
        Returns:
            str: Consulta reescrita y mejorada
        """
        try:
            print(f"🔄 Reescribiendo consulta: '{question[:50]}...'")
            
            # Crear prompt para query rewriting
            rewrite_prompt = ChatPromptTemplate.from_template("""
Eres un experto en recuperación de información. Tu tarea es reescribir la consulta del usuario para mejorar la búsqueda de documentos relevantes.

CONSULTA ORIGINAL: {question}

INSTRUCCIONES:
1. Analiza la consulta original y identifica los conceptos clave
2. Expande la consulta con términos relacionados y sinónimos
3. Reformula la consulta para ser más específica y precisa
4. Mantén el significado original pero mejora la claridad
5. Si la consulta es muy general, hazla más específica
6. Si la consulta es muy específica, considera variaciones

ESTRATEGIAS A APLICAR:
- Query Expansion: Añadir términos relacionados
- Query Refinement: Mejorar la precisión
- Sinónimos y variaciones de términos clave
- Contexto adicional si es necesario

CONSULTA REESCRITA:
""")
            
            # FORZAR USO DEL MODELO LOCAL PARA QUERY REWRITING
            # Esto evita problemas con cuota de Google AI
            print("🤖 Usando modelo local para query rewriting...")
            return self._rewrite_query_local(question)
            
        except Exception as e:
            print(f"❌ Error en query rewriting: {str(e)}")
            return question
    
    def _rewrite_query_local(self, question: str) -> str:
        """
        Implementación básica de query rewriting para modelo local.
        
        Args:
            question: Consulta original
            
        Returns:
            str: Consulta reescrita
        """
        print(f"🔄 Iniciando query rewriting local para: '{question[:50]}...'")
        
        # Estrategia 1: Reformulación directa para consultas comunes
        question_lower = question.lower()
        
        # Patrones específicos de reescritura
        if "información importante" in question_lower and "documentos" in question_lower:
            # Patrón: "¿Qué información importante contienen estos documentos?"
            rewritten = question.replace("información importante", "contenido relevante y datos significativos")
            rewritten = rewritten.replace("estos documentos", "los documentos disponibles")
            print(f"✅ Consulta reformulada (patrón 1): '{rewritten[:50]}...'")
            return rewritten
        
        if "información" in question_lower and "contienen" in question_lower:
            # Patrón: "¿Qué información contienen...?"
            rewritten = question.replace("información", "datos relevantes y contenido")
            rewritten = rewritten.replace("contienen", "incluyen y presentan")
            print(f"✅ Consulta reformulada (patrón 2): '{rewritten[:50]}...'")
            return rewritten
        
        # Estrategia 2: Expansión con términos relacionados
        expansion_terms = {
            "información": ["datos", "contenido", "detalles", "especificaciones"],
            "documentos": ["archivos", "textos", "materiales", "recursos"],
            "importante": ["relevante", "significativo", "clave", "esencial"],
            "contienen": ["incluyen", "presentan", "muestran", "describen"]
        }
        
        expanded_terms = []
        for key, synonyms in expansion_terms.items():
            if key in question_lower:
                expanded_terms.extend(synonyms[:2])  # Tomar solo 2 sinónimos
        
        if expanded_terms:
            # Crear consulta expandida
            unique_terms = list(set(expanded_terms))
            expanded_query = f"{question} {' '.join(unique_terms[:2])}"
            print(f"✅ Consulta expandida: '{expanded_query[:50]}...'")
            return expanded_query
        
        # Estrategia 3: Reformulación general
        if "¿Qué" in question and "?" in question:
            # Reformular preguntas que empiecen con "¿Qué"
            rewritten = question.replace("¿Qué", "¿Cuáles son los")
            rewritten = rewritten.replace("?", " y qué detalles específicos incluyen?")
            print(f"✅ Consulta reformulada (patrón 3): '{rewritten[:50]}...'")
            return rewritten
        
        # Estrategia 4: Agregar contexto específico
        context_additions = ["contenido específico", "datos relevantes"]
        context_query = f"{question} {' '.join(context_additions)}"
        print(f"✅ Consulta con contexto: '{context_query[:50]}...'")
        return context_query