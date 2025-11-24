"""
Servicio del Agente Especializado
==================================

Este módulo gestiona el ciclo de vida del Agente Especializado (ReAct), incluyendo
la inicialización de la sesión MCP, carga de múltiples herramientas y ejecución
del agente para procesar tareas complejas de los usuarios.

IMPLEMENTACIÓN SEMANA 7:
- Completar el método ask_custom para invocar el agente ReAct
- Pasar la pregunta del usuario al agente compilado
- Extraer el último mensaje (respuesta final) del resultado
- Retornar el string de la respuesta final
"""

from langchain_core.messages import HumanMessage, AIMessage
from flows.custom_agent import build_custom_agent
from mcp.client.stdio import stdio_client
from mcp_server.tools import load_tools
from mcp_server.model import llm
from mcp import ClientSession
import asyncio
import logging
from typing import Dict, List
from collections import defaultdict


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CustomAgentService:


    def __init__(self):
        self.server_parameters = None
        self._lock = asyncio.Lock()
        self._stdio_ctx = None
        self._session = None
        self.agent = None
        # Diccionario para mantener historial de conversaciones por session_id
        self.conversation_history: Dict[str, List] = defaultdict(list)

    
    def set_server_parameters(self, server_parameters):
        self.server_parameters = server_parameters
    

    async def initialize(self):
        """
        Inicializa la sesión MCP y construye el agente personalizado.
        
        NOTA: Este método ya está implementado y NO necesita modificación.
        """
        async with self._lock:
            if self._session is None:
                if not self.server_parameters:
                    raise ValueError("MCP server parameters not set. Call set_server_parameters() first")
                
                logger.info("Starting stdio_client...")
                self._stdio_ctx = stdio_client(self.server_parameters)
                read, write = await self._stdio_ctx.__aenter__()
                self._session = await ClientSession(read, write).__aenter__()
                await self._session.initialize()
                logger.info("MCP session initialized successfully")

                # Cargar herramientas del MCP server
                tools, tools_by_name = await load_tools(self._session)
                logger.info(f"Loaded {len(tools)} tools from MCP server")

                # Construir el agente personalizado con herramientas vinculadas
                # IMPORTANTE: El model ya viene con bind_tools(tools) aplicado
                self.agent = build_custom_agent(llm.bind_tools(tools), tools_by_name)
                logger.info("Custom Agent created successfully")
    

    # ===============================================================================
    # SEMANA 7: Implementar la ejecución del agente personalizado
    # ===============================================================================
    

    async def ask_custom(self, question, session_id="default"):
        """
        Procesa una pregunta usando el agente personalizado ReAct.
        
        Args:
            question (str): La pregunta o tarea del usuario
            session_id (str): ID de sesión para mantener memoria conversacional
        
        Returns:
            str: La respuesta generada por el agente
        """
        # Asegurarse de que el agente está inicializado
        if self._session is None or self.agent is None:
            await self.initialize()
        
        logger.info(f"[CUSTOM SERVICE] Processing question: {question}")
        
        # ==========================================================
        # Ejecución del agente personalizado
        # ----------------------------------------------------------
        # En este bloque deberás invocar al agente compilado para 
        # procesar la consulta del usuario.
        #
        # Pasos sugeridos:
        #   1. Enviar el mensaje o pregunta al agente.
        #   2. Esperar la respuesta generada (async/await).
        #   3. Retornar el resultado final.
        #
        # Ejemplo:
        #   response = await self.agent.ainvoke({"input": question})
        #   return response
        # ==========================================================
        
        # Obtener el historial de conversación para esta sesión
        history = self.conversation_history[session_id]
        if session_id != "default" and len(history) > 0:
            logger.info(f"[CUSTOM SERVICE] Session '{session_id}' has {len(history)} previous messages")
        
        # Crear el mensaje del usuario
        user_message = HumanMessage(content=question)
        
        # Crear el estado inicial con el historial completo + nuevo mensaje
        initial_state = {
            "messages": history + [user_message]
        }
        
        try:
            # Invocar al agente compilado
            # El agente ejecutará el flujo ReAct: llm -> tools -> llm -> ... -> END
            result = await self.agent.ainvoke(initial_state)
            
            # Extraer el último mensaje (respuesta final del agente)
            messages = result.get("messages", [])
            if not messages:
                logger.warning("[CUSTOM SERVICE] No messages in response")
                return "Lo siento, no pude generar una respuesta."
            
            # El último mensaje debería ser la respuesta del asistente (sin tool_calls)
            # Buscar el último mensaje del asistente que no tenga tool_calls
            last_ai_message = None
            for msg in reversed(messages):
                if hasattr(msg, 'content') and hasattr(msg, 'type'):
                    # Verificar que es un mensaje del asistente
                    if msg.type == 'ai' or isinstance(msg, AIMessage):
                        # Verificar que no tiene tool_calls (es la respuesta final)
                        if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                            last_ai_message = msg
                            break
            
            # Si no encontramos un mensaje AI sin tool_calls, usar el último mensaje
            if last_ai_message is None:
                last_ai_message = messages[-1]
            
            # Extraer el contenido de la respuesta
            if hasattr(last_ai_message, "content"):
                answer = last_ai_message.content
            elif isinstance(last_ai_message, dict):
                answer = last_ai_message.get("content", str(last_ai_message))
            else:
                answer = str(last_ai_message)
            
            logger.info(f"[CUSTOM SERVICE] Response generated (length: {len(answer)})")
            
            # Actualizar el historial de conversación con el nuevo mensaje y respuesta
            ai_message = AIMessage(content=answer)
            self.conversation_history[session_id].extend([user_message, ai_message])
            
            # Limitar el historial a los últimos 20 mensajes para evitar que crezca demasiado
            if len(self.conversation_history[session_id]) > 20:
                self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
                if session_id != "default":
                    logger.info(f"[CUSTOM SERVICE] History truncated to last 20 messages for session '{session_id}'")
            
            if session_id != "default":
                logger.info(f"[CUSTOM SERVICE] Updated conversation history for session '{session_id}' ({len(self.conversation_history[session_id])} messages)")
            
            return answer
            
        except Exception as e:
            logger.error(f"[CUSTOM SERVICE] Error processing question: {str(e)}")
            raise e
    

    async def shutdown(self):
        """
        Cierra la sesión MCP y limpia recursos.
        
        NOTA: Este método ya está implementado y NO necesita modificación.
        """
        async with self._lock:
            if self._session:
                await self._session.__aexit__(None, None, None)
                self._session = None
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
                self._stdio_ctx = None
            logger.debug("MCP session and stdio_client shut down")


CUSTOM_AGENT_SERVICE = CustomAgentService()
