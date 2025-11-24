"""
Endpoint de Consultas RAG
=====================================================

Este módulo implementa el endpoint principal para realizar consultas al sistema RAG.

OBJETIVOS POR SEMANA:
-----------------------
SEMANA 1 (COMPLETADA):
- ✅ Endpoint funcional que retorne JSON válido
- ✅ Validación básica de parámetros
- ✅ Estructura de respuesta correcta

SEMANA 2 (IMPLEMENTAR):
- Implementar conexión con ChunkingService
- Implementar conexión con EmbeddingService
- Implementar conexión con RetrievalService
- Implementar conexión con GenerationService
- Generar respuesta con contexto recuperado

SEMANA 3 (IMPLEMENTAR):
- Implementar query rewriting (opcional, activado por parámetro)
- Implementar reranking de documentos (opcional, activado por parámetro)

NOTAS:
-------------------------
- Este archivo es el punto de integración de todos los servicios RAG
- Los estudiantes deben modificar basic_rag_processing()
- Mantener la estructura de respuesta para compatibilidad con tests
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
import time

# Importar modelos desde la carpeta models
from app.models.ask import AskRequest, AskResponse

# Configuración del router
router = APIRouter(prefix="/api/v1", tags=["Ask"])

# Almacenar historial de conversación (en producción usar Redis o base de datos)
# Por ahora, un diccionario simple en memoria
chat_history_store: Dict[str, List[Dict[str, Any]]] = {}

# ===========================================
# FUNCIONES AUXILIARES
# ===========================================

async def basic_rag_processing(
    question: str, 
    top_k: int, 
    collection: str, 
    force_rebuild: bool,
    use_reranking: bool = False,
    use_query_rewriting: bool = False,
    session_id: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Función principal de procesamiento RAG
    
    SEMANA 1: Retorna respuesta básica estática ✅
    SEMANA 2: Implementar lógica RAG básica
    SEMANA 3: Agregar reranking y query rewriting
    
    Args:
        question: La consulta del usuario
        top_k: Número de documentos a recuperar
        collection: Nombre de la colección de documentos
        force_rebuild: Si forzar reconstrucción del índice
        use_reranking: Si aplicar reranking (Semana 3)
        use_query_rewriting: Si aplicar reescritura de consulta (Semana 3)
    
    Returns:
        Dict con la respuesta estructurada
    """
    start_time = time.time()
        
    # ===========================================
    # IMPLEMENTACIÓN RAG BÁSICA - SEMANA 2
    # ===========================================
    try:
        # 1. Importar servicios necesarios
        from app.services.embedding_service import EmbeddingService
        from app.services.retrieval_service import RetrievalService
        from app.services.generation_service import GenerationService
        
        # 2. Inicializar servicios
        embedding_service = EmbeddingService()
        retrieval_service = RetrievalService()
        generation_service = GenerationService()
        
        # 2.1. Manejar historial de conversación
        session_key = session_id or "default"
        if chat_history is not None:
            # Usar historial proporcionado (hacer copia para no modificar el original)
            import copy
            current_history = copy.deepcopy(chat_history)
        elif session_key in chat_history_store:
            # Usar historial existente de la sesión (hacer copia profunda)
            import copy
            current_history = copy.deepcopy(chat_history_store[session_key])
        else:
            # Crear nuevo historial
            current_history = []
            chat_history_store[session_key] = current_history
        
        # 2.2. Verificar si es una solicitud de email ANTES de recuperar documentos
        # Esto permite manejar solicitudes de email incluso si no hay documentos
        print("\n" + "="*80)
        print("🔍 [MCP TOOL DETECTION] Analizando solicitud para detectar uso de herramienta MCP")
        print("="*80)
        print(f"📝 Pregunta del usuario: '{question}'")
        print(f"📊 Historial actual: {len(current_history)} mensajes")
        
        question_lower = question.lower().strip()
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        has_email = bool(re.search(email_pattern, question))
        email_keywords = ["enviar", "correo", "email", "historial", "conversación", "chat", "envía", "envíame"]
        has_email_keywords = any(keyword in question_lower for keyword in email_keywords)
        
        print(f"🔎 Análisis de detección:")
        print(f"   - Contiene email: {has_email}")
        if has_email:
            emails_found = re.findall(email_pattern, question)
            print(f"   - Emails encontrados: {emails_found}")
        print(f"   - Contiene palabras clave de email: {has_email_keywords}")
        if has_email_keywords:
            found_keywords = [kw for kw in email_keywords if kw in question_lower]
            print(f"   - Palabras clave encontradas: {found_keywords}")
        
        # Verificar si la pregunta anterior era sobre enviar email
        previous_was_email_request = False
        if len(current_history) > 0:
            last_assistant_msg = None
            for msg in reversed(current_history):
                if msg.get("role") == "assistant":
                    last_assistant_msg = msg.get("content", "").lower()
                    break
            
            if last_assistant_msg and ("correo electrónico" in last_assistant_msg or "dirección de correo" in last_assistant_msg):
                previous_was_email_request = True
                print(f"   - Pregunta anterior era sobre correo: {previous_was_email_request}")
        
        # Detectar solicitud de email
        is_email_request = (
            (has_email_keywords and ("correo" in question_lower or "email" in question_lower)) or
            (has_email and previous_was_email_request) or
            (has_email and len(question.split()) <= 5)
        )
        
        print(f"\n✅ Resultado de detección: {'SOLICITUD DE EMAIL DETECTADA' if is_email_request else 'No es solicitud de email'}")
        if is_email_request:
            print(f"📧 [MCP TOOL] Se detectó solicitud para usar herramienta: send_chat_history_email")
        print("="*80 + "\n")
        
        # 3. Usar colección default si no se especifica
        collection_name = collection if collection else "default"
        
        # 4. SEMANA 3: Query Rewriting (opcional) - solo si NO es solicitud de email
        final_query = question
        if use_query_rewriting and not is_email_request:
            final_query = generation_service.rewrite_query(question)
        
        # 5. Recuperar documentos relevantes del vector store (solo si NO es solicitud de email)
        retrieved_docs = []
        if not is_email_request:
            retrieved_docs = retrieval_service.similarity_search(
                query=final_query,
                collection_name=collection_name,
                k=top_k,
                embedding_service=embedding_service
            )
        
        # 6. Si no hay documentos y NO es solicitud de email, retornar respuesta apropiada
        if not retrieved_docs and not is_email_request:
            processing_time = time.time() - start_time
            return {
                "question": question,
                "final_query": final_query,
                "answer": "No tengo información suficiente en la base de datos para responder a esta pregunta.",
                "collection": collection_name,
                "files_consulted": [],
                "context_docs": [],
                "reranker_used": False,
                "query_rewriting_used": use_query_rewriting,
                "response_time_sec": round(processing_time, 3)
            }
        
        # 7. SEMANA 3: Reranking (opcional) - solo si NO es solicitud de email
        reranker_used = False
        if use_reranking and not is_email_request and retrieved_docs:
            # Llamar al método rerank_documents del retrieval_service
            retrieved_docs = retrieval_service.rerank_documents(
                query=final_query,
                documents=retrieved_docs,
                top_n=top_k
            )
            reranker_used = True
        
        # 8. Generar respuesta con el contexto recuperado
        generation_result = generation_service.generate_response(
            question=question,
            retrieved_docs=retrieved_docs,
            chat_history=current_history
        )
        
        # 8.1. Actualizar historial almacenado con el historial actualizado del servicio
        # Hacer copia profunda para evitar problemas de referencia
        import copy
        updated_history = copy.deepcopy(generation_service.chat_history)
        chat_history_store[session_key] = updated_history
        
        # 9. Construir lista de archivos consultados
        files_consulted = generation_result["sources"]
        
        # 10. Construir context_docs con estructura correcta
        context_docs = []
        for doc in retrieved_docs:
            context_doc = {
                "file_name": doc.metadata.get("source_file", "unknown"),
                "chunk_type": doc.metadata.get("chunking_strategy", "unknown"),
                "snippet": doc.page_content[:200],  # Preview
                "content": doc.page_content,  # Contenido completo para RAGAS
                "priority": "high" if len(context_docs) == 0 else "medium"
            }
            
            # SEMANA 3: Añadir rerank_score si existe
            if "rerank_score" in doc.metadata:
                context_doc["rerank_score"] = doc.metadata["rerank_score"]
            
            context_docs.append(context_doc)
        
        processing_time = time.time() - start_time
        
        # 11. Retornar respuesta completa
        return {
            "question": question,
            "final_query": final_query,  # Cambia si use_query_rewriting=True
            "answer": generation_result["answer"],
            "collection": collection_name,
            "files_consulted": files_consulted,
            "context_docs": context_docs,
            "reranker_used": reranker_used,  # True si use_reranking=True
            "query_rewriting_used": use_query_rewriting,  # True si use_query_rewriting=True
            "response_time_sec": round(processing_time, 3)
        }
        
    except Exception as e:
        # Manejo de errores
        print(f"Error en procesamiento RAG: {str(e)}")
        import traceback
        traceback.print_exc()
        processing_time = time.time() - start_time
        return {
            "question": question,
            "final_query": question,
            "answer": f"Error procesando la consulta: {str(e)}",
            "collection": collection if collection else "default",
            "files_consulted": [],
            "context_docs": [],
            "reranker_used": use_reranking,
            "query_rewriting_used": use_query_rewriting,
            "response_time_sec": round(processing_time, 3)
        }


# ===========================================
# ENDPOINT FASTAPI
# ===========================================

@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest):
    """
    Endpoint principal para realizar consultas al sistema RAG.
    
    SEMANA 1: Validación básica y respuesta estática ✅
    SEMANA 2: Implementación RAG básica
    SEMANA 3: Funcionalidades avanzadas (reranking, query rewriting)
    
    Este endpoint:
    1. Valida la entrada del usuario
    2. Procesa la consulta usando el sistema RAG
    3. Retorna una respuesta estructurada con metadatos
    
    Args:
        payload: Objeto AskRequest con la consulta y parámetros
    
    Returns:
        AskResponse: Respuesta estructurada con la información solicitada
    
    Raises:
        HTTPException: 
            - 400: Si la pregunta está vacía
            - 500: Si ocurre un error durante el procesamiento
    """
    # Validación de entrada
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=400, 
            detail="La pregunta es requerida y no puede estar vacía"
        )
    
    try:
        # Procesamiento principal
        data = await basic_rag_processing(
            question=payload.question.strip(),
            top_k=payload.top_k or 5,
            collection=payload.collection or "default",
            force_rebuild=payload.force_rebuild or False,
            use_reranking=payload.use_reranking or False,
            use_query_rewriting=payload.use_query_rewriting or False
        )
        
        return data
        
    except Exception as e:
        # Manejo robusto de errores
        raise HTTPException(
            status_code=500, 
            detail=f"Error procesando la consulta: {str(e)}"
        )