"""
Workflow del Agente Especializado
==========================================

Este módulo define el flujo de ejecución del Agente Especializado utilizando
LangGraph. El agente implementa el patrón ReAct (Reasoning + Acting) que permite
tomar decisiones dinámicas sobre qué herramientas usar.

IMPLEMENTACIÓN SEMANA 7:
- Construir el workflow ReAct del agente especilizado
- Definir el estado del agente (solo necesita "messages")
- Crear nodo "llm" que razona y decide qué hacer
- Crear nodo "tools" que ejecuta herramientas solicitadas
- Crear función should_continue que decide si usar más herramientas
- Construir grafo con ciclo: llm ↔ tools

CARACTERÍSTICAS:
- Patrón ReAct: Reasoning (razonamiento) + Acting (acción)
- Decisiones dinámicas sobre qué herramientas usar
- Puede ejecutar múltiples herramientas en secuencia
- El LLM analiza resultados y decide siguientes pasos
"""

from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
import logging
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
# SEMANA 7: Construir el agente ReAct con herramientas
# ===============================================================================
#
# DIFERENCIAS CON EL RAG AGENT:
# - RAG Agent: Flujo LINEAL (siempre ejecuta "ask")
# - Custom Agent: Flujo CÍCLICO (decide dinámicamente qué hacer)

def build_custom_agent(model, tools_by_name):
    """
    Construye un agente ReAct que puede usar múltiples herramientas.
    
    Args:
        model: El modelo LLM con herramientas ya vinculadas (bind_tools)
        tools_by_name: Diccionario mapeando nombres a herramientas MCP
    
    Returns:
        CompiledGraph: El grafo compilado listo para ejecutar
    """
    
    # ==========================================================
    # Construcción del agente personalizado
    # ----------------------------------------------------------
    # En esta sección implementarás la lógica de tu agente que
    # incorpora fuentes de datos externas y otras funcionalidades.
    # Aquí podrás combinar el modelo y las herramientas MCP 
    # para definir cómo el agente procesa las consultas.
    #
    # Ejemplo:
    #   from langgraph.graph import StateGraph, END
    #   graph = StateGraph()
    #   graph.add_node("model", model)
    #   graph.add_edge("model", END)
    #   flow = graph.compile()
    #   return flow
    # ==========================================================
    
    # ===============================================================================
    # ESTADO DEL AGENTE
    # ===============================================================================
    
    class AgentState(TypedDict):
        """
        Estado del agente personalizado ReAct.
        
        Campos:
            messages: Historial de mensajes de la conversación (usuario, modelo, herramientas)
        """
        messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # ===============================================================================
    # NODOS DEL GRAFO
    # ===============================================================================
    
    # NODO 1: LLM (Reasoning)
    # Recibe todo el historial de mensajes y devuelve la siguiente respuesta del modelo,
    # ya sea con o sin tool calls. El modelo decide dinámicamente si necesita usar herramientas.
    def call_model(state: AgentState, config: RunnableConfig = None):
        """
        Nodo que invoca al LLM con el historial de mensajes.
        El LLM puede decidir llamar herramientas o responder directamente.
        """
        messages = state["messages"]
        logger.info(f"[CUSTOM AGENT] Invoking LLM with {len(messages)} messages in history")
        
        try:
            # Invocar al modelo con el historial completo
            # El modelo tiene bind_tools, por lo que puede decidir usar herramientas
            if config:
                response = model.invoke(messages, config)
            else:
                response = model.invoke(messages)
            
            logger.info(f"[CUSTOM AGENT] LLM responded with content: {str(response.content)[:60]}...")
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"[CUSTOM AGENT] LLM requested {len(response.tool_calls)} tool call(s)")
            
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"[CUSTOM AGENT] Error invoking LLM: {str(e)}")
            raise
    
    # NODO 2: TOOLS (Acting)
    # Toma la última respuesta del modelo que contiene tool calls.
    # Para cada llamada busca la herramienta correspondiente por nombre,
    # la invoca con los argumentos necesarios y empaqueta la respuesta como ToolMessage.
    async def call_tool(state: AgentState):
        """
        Nodo que ejecuta las herramientas solicitadas por el LLM.
        """
        last_message = state["messages"][-1]
        
        # Verificar que el último mensaje tiene tool calls
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            logger.warning("[CUSTOM AGENT] call_tool invoked but no tool_calls found")
            return {"messages": []}
        
        logger.info(f"[CUSTOM AGENT] Processing {len(last_message.tool_calls)} tool call(s)")
        
        # Mostrar qué herramientas se van a utilizar
        tool_names = [tc["name"] for tc in last_message.tool_calls]
        logger.info(f"[CUSTOM AGENT] Tools to be used: {', '.join(tool_names)}")
        
        tool_messages = []
        
        try:
            # Procesar cada tool call
            for tc in last_message.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_call_id = tc["id"]
                
                logger.info(f"[CUSTOM AGENT] → Using tool: '{tool_name}' with args: {tool_args}")
                
                # Buscar la herramienta en el diccionario
                if tool_name not in tools_by_name:
                    error_msg = f"Tool '{tool_name}' not found in available tools"
                    logger.error(f"[CUSTOM AGENT] {error_msg}")
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: {error_msg}",
                            name=tool_name,
                            tool_call_id=tool_call_id
                        )
                    )
                    continue
                
                tool = tools_by_name[tool_name]
                
                # Invocar la herramienta de forma asíncrona
                try:
                    result = await tool.ainvoke(tool_args)
                    logger.info(f"[CUSTOM AGENT] Tool '{tool_name}' returned: {str(result)[:60]}...")
                    
                    # Empaquetar la respuesta como ToolMessage
                    tool_messages.append(
                        ToolMessage(
                            content=str(result),
                            name=tool_name,
                            tool_call_id=tool_call_id
                        )
                    )
                except Exception as e:
                    error_msg = f"Error executing tool '{tool_name}': {str(e)}"
                    logger.error(f"[CUSTOM AGENT] {error_msg}")
                    tool_messages.append(
                        ToolMessage(
                            content=error_msg,
                            name=tool_name,
                            tool_call_id=tool_call_id
                        )
                    )
            
            return {"messages": tool_messages}
            
        except Exception as e:
            logger.error(f"[CUSTOM AGENT] Error in call_tool: {str(e)}")
            raise
    
    # ===============================================================================
    # FUNCIÓN DE DECISIÓN CONDICIONAL
    # ===============================================================================
    
    def should_continue(state: AgentState):
        """
        Decide si el flujo debe continuar (usar herramientas) o terminar.
        
        Si el modelo pidió herramientas, continúa al nodo de herramientas.
        Si el modelo no pidió herramientas, termina el flujo.
        """
        last_message = state["messages"][-1]
        
        # Verificar si hay tool calls
        has_tool_calls = (
            hasattr(last_message, 'tool_calls') and 
            last_message.tool_calls and 
            len(last_message.tool_calls) > 0
        )
        
        decision = "continue" if has_tool_calls else "end"
        logger.info(f"[CUSTOM AGENT] Flow decision: {decision} (tool_calls: {has_tool_calls})")
        
        return decision
    
    # ===============================================================================
    # COMPILACIÓN DEL FLUJO
    # ===============================================================================
    
    # Crear el grafo de estado
    workflow = StateGraph(AgentState)
    
    # Agregar nodos
    workflow.add_node("llm", call_model)
    workflow.add_node("tools", call_tool)
    
    # Configurar el punto de entrada
    workflow.set_entry_point("llm")
    
    # Agregar arista condicional desde llm
    # Si hay tool_calls -> "continue" -> tools
    # Si no hay tool_calls -> "end" -> END
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    
    # Agregar arista desde tools de vuelta a llm (ciclo)
    workflow.add_edge("tools", "llm")
    
    # Compilar el grafo
    app = workflow.compile()
    logger.info("[CUSTOM AGENT] ReAct agent workflow built successfully")
    
    return app