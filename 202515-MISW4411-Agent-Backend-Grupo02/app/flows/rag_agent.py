"""
Workflow del Agente RAG
========================

Este módulo define el flujo de ejecución del Agente RAG utilizando LangGraph.
El agente implementa un flujo LINEAL que consulta el sistema RAG y genera una
respuesta basada en el contexto recuperado.

IMPLEMENTACIÓN SEMANA 6:
- Construir el workflow del agente RAG con LangGraph
- Definir el estado del agente (AgentState)
- Crear nodo "ask" que invoca la herramienta MCP del RAG
- Crear nodo "llm" que genera respuesta con el contexto
- Conectar los nodos en flujo lineal: ask → llm

CARACTERÍSTICAS:
- Flujo determinístico (sin ramificaciones)
- No usa bind_tools (herramienta específica recibida como parámetro)
- Siempre ejecuta la misma secuencia de pasos
"""

from typing import Annotated, Sequence, TypedDict

import logging
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
import sys


# Configurar logging con UTF-8
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
# Asegurar que el handler use UTF-8
for handler in logging.root.handlers:
    if hasattr(handler, 'stream') and hasattr(handler.stream, 'reconfigure'):
        try:
            handler.stream.reconfigure(encoding='utf-8')
        except:
            pass

logger = logging.getLogger(__name__)

# ===============================================================================
# SEMANA 6: Construir el flujo del agente RAG
# ===============================================================================

# ===============================================================================
# ESTADO DEL AGENTE
# ===============================================================================

class AgentState(TypedDict):
    """
    Estado del agente RAG.
    
    Campos:
        messages: Historial de mensajes de la conversación
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ===============================================================================
# NODOS DEL GRAFO
# ===============================================================================

def build_rag_agent(model, ask_tool):
    """
    Construye un agente RAG con flujo lineal.
    Recuerden usar la herrmaienta del MCP definida para consultar el RAG.
    
    Args:
        model: El modelo LLM (Gemini) configurado
        ask_tool: Herramienta MCP para consultar el RAG
    
    Returns:
        CompiledGraph: El grafo compilado listo para ejecutar
    """
    
    # ==========================================================
    # Construcción del agente RAG
    # ----------------------------------------------------------
    # En esta sección implementarás la lógica del agente RAG
    # que consulta el sistema RAG y genera respuestas basadas
    # en el contexto recuperado.
    #
    # Pasos:
    #   1. Definir el estado del agente (AgentState)
    #   2. Crear nodo "ask" que invoca la herramienta MCP del RAG
    #   3. Crear nodo "llm" que genera respuesta con el contexto
    #   4. Conectar los nodos en flujo lineal: ask → llm
    #
    # Ejemplo:
    #   from langgraph.graph import StateGraph, END
    #   graph = StateGraph()
    #   graph.add_node("model", model)
    #   graph.add_edge("model", END)
    #   flow = graph.compile()
    #   return flow
    # ==========================================================
    
    logger.info("[RAG AGENT] Building linear RAG agent")
    
    # Crear el grafo
    workflow = StateGraph(AgentState)
    
    # Crear nodo "ask" que invoca la herramienta MCP del RAG
    # Guardamos ask_tool en la función para que esté disponible en el closure
    async def ask_node(state: AgentState) -> AgentState:
        """Nodo que invoca la herramienta ask del RAG."""
        messages = state["messages"]
        
        # Extraer la pregunta del último mensaje del usuario
        question = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                question = msg.content
                break
            elif hasattr(msg, "content"):
                question = msg.content
                break
        
        if not question:
            logger.warning("[RAG AGENT] No se encontró pregunta del usuario")
            return state
        
        logger.info(f"[RAG AGENT] Invoking RAG tool with question: {question}")
        
        try:
            # Invocar la herramienta MCP "ask" para consultar el RAG de forma asíncrona
            # Las herramientas MCP son asíncronas, por lo que usamos ainvoke()
            context = await ask_tool.ainvoke({"query": question})
            
            logger.info(f"[RAG AGENT] RAG context retrieved (length: {len(context)})")
            
            # Agregar el contexto como mensaje del sistema para que el LLM pueda usarlo
            from langchain_core.messages import SystemMessage
            context_message = SystemMessage(content=f"Contexto del RAG:\n{context}")
            
            # Agregar el mensaje de contexto al estado
            new_messages = list(messages) + [context_message]
            
            return {
                **state,
                "messages": new_messages
            }
            
        except Exception as e:
            logger.error(f"[RAG AGENT] Error invoking RAG tool: {str(e)}")
            # En caso de error, continuar sin contexto
            from langchain_core.messages import SystemMessage
            error_message = SystemMessage(content=f"Error al consultar el RAG: {str(e)}")
            new_messages = list(messages) + [error_message]
            return {
                **state,
                "messages": new_messages
            }
    
    # Crear nodo "llm" que genera respuesta con el contexto y formateo
    async def llm_node(state: AgentState) -> AgentState:
        """
        Nodo que invoca al LLM con instrucciones de formateo.
        El LLM se encarga de extraer el nombre del historial y formatear la respuesta.
        """
        messages = state["messages"]
        
        # Agregar instrucciones de formateo como SystemMessage
        from langchain_core.messages import SystemMessage
        
        format_instructions = SystemMessage(content="""
Eres un asistente que formatea respuestas de manera clara y personalizada.

INSTRUCCIONES DE FORMATEO:
1. Formatea la respuesta de ser necesario con viñetas, saltos de linea, negrilla o tablas.

FORMATO ESPERADO:
Hola, Santiago!

IMPORTANTE: 
- Usa el contexto del RAG para generar la respuesta informada, respondiendo de forma amable y agradable
- Tu unica informacion es la del RAG
""")
        
        # Combinar mensajes: instrucciones de formateo + historial completo
        messages_with_instructions = [format_instructions] + list(messages)
        
        logger.info("[RAG AGENT] Invoking LLM with formatting instructions")
        
        # Invocar al LLM con las instrucciones y el historial de forma asíncrona
        # El LLM leerá el historial, encontrará el nombre, y formateará la respuesta
        response = await model.ainvoke(messages_with_instructions)
        
        # Extraer el contenido de la respuesta (ya formateada por el LLM)
        formatted_content = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"[RAG AGENT] LLM response generated (length: {len(formatted_content)})")
        
        # Crear AIMessage con la respuesta formateada
        formatted_message = AIMessage(content=formatted_content)
        
        # Agregar respuesta formateada al estado
        new_messages = list(messages) + [formatted_message]
        
        return {
            **state,
            "messages": new_messages
        }
    
    workflow.add_node("ask", ask_node)
    workflow.add_node("llm", llm_node)
    
    # Conectar los nodos en flujo lineal: ask → llm → END
    workflow.add_edge(START, "ask")
    workflow.add_edge("ask", "llm")
    workflow.add_edge("llm", END)
    
    # Compilar el grafo
    app = workflow.compile()
    logger.info("[RAG AGENT] Linear RAG agent built successfully")
    
    return app
