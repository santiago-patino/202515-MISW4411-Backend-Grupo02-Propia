"""
Grafos para LangGraph Studio
============================

Este módulo exporta los grafos del proyecto para que puedan ser utilizados
con LangGraph Studio mediante el comando `langgraph dev`.

Los grafos se inicializan con configuración por defecto para permitir
visualización y depuración en LangGraph Studio.

NOTA: Para uso en producción, los grafos se inicializan a través de
los servicios (rag_agent_service.py y custom_agent_service.py) que
manejan correctamente las conexiones MCP.
"""

import os
import sys
import logging
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Asegurar que las variables de entorno estén cargadas
try:
    from dotenv import load_dotenv
    # Intentar cargar .env desde app/.env o .env en la raíz
    env_paths = [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        ".env"
    ]
    loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Variables de entorno cargadas desde: {env_path}")
            loaded = True
            break
    if not loaded:
        logger.warning("No se encontró archivo .env, usando variables de entorno del sistema")
except ImportError:
    logger.warning("python-dotenv no está instalado, usando variables de entorno del sistema")

# Importar componentes necesarios
from flows.rag_agent import build_rag_agent, AgentState
from flows.custom_agent import build_custom_agent
from mcp_server.model import llm

# Intentar importar herramientas MCP
try:
    from mcp.client.stdio import stdio_client
    from mcp_server.tools import load_tools
    from mcp_server.config import get_server_parameters
    from mcp import ClientSession
    import asyncio
    
    MCP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MCP no disponible: {e}")
    MCP_AVAILABLE = False


class MockTool:
    """Herramienta mock para uso en LangGraph Studio cuando MCP no está disponible."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def ainvoke(self, input_data: dict) -> str:
        """Simula la invocación de una herramienta."""
        query = input_data.get("query", "")
        return f"[MOCK] Respuesta simulada para la consulta: {query}\n\nEsta es una herramienta mock. En producción, esta herramienta se conecta al sistema RAG real."


async def _initialize_rag_agent():
    """Inicializa el agente RAG con herramientas MCP reales o mock."""
    try:
        # Intentar inicializar con MCP real
        if MCP_AVAILABLE:
            server_params = get_server_parameters("/app/mcp_server/rag_server.py")
            stdio_ctx = stdio_client(server_params)
            read, write = await stdio_ctx.__aenter__()
            session = await ClientSession(read, write).__aenter__()
            await session.initialize()
            
            tools, tools_by_name = await load_tools(session)
            
            if "ask" in tools_by_name:
                ask_tool = tools_by_name["ask"]
                logger.info("RAG Agent inicializado con herramienta MCP real")
                return build_rag_agent(llm, ask_tool)
            else:
                logger.warning("Herramienta 'ask' no encontrada, usando mock")
                ask_tool = MockTool("ask")
                return build_rag_agent(llm, ask_tool)
        else:
            # Usar herramienta mock
            logger.info("Usando herramienta mock para RAG Agent")
            ask_tool = MockTool("ask")
            return build_rag_agent(llm, ask_tool)
    except Exception as e:
        logger.warning(f"Error al inicializar RAG Agent con MCP: {e}. Usando mock.")
        ask_tool = MockTool("ask")
        return build_rag_agent(llm, ask_tool)


async def _initialize_custom_agent():
    """Inicializa el agente personalizado con herramientas MCP reales o mock."""
    try:
        # Verificar si build_custom_agent está implementado
        import inspect
        source = inspect.getsource(build_custom_agent)
        if "pass" in source and "Reemplazar" in source:
            # build_custom_agent no está implementado, crear placeholder
            logger.warning("Custom Agent no está implementado, creando placeholder")
            from langgraph.graph import StateGraph, END, START
            from langchain_core.messages import AIMessage
            
            placeholder_graph = StateGraph(AgentState)
            
            async def placeholder_node(state: AgentState) -> AgentState:
                """Nodo placeholder para Custom Agent no implementado."""
                messages = state["messages"]
                response = AIMessage(
                    content="Custom Agent aún no está implementado. Este es un grafo placeholder para LangGraph Studio."
                )
                return {
                    **state,
                    "messages": list(messages) + [response]
                }
            
            placeholder_graph.add_node("placeholder", placeholder_node)
            placeholder_graph.add_edge(START, "placeholder")
            placeholder_graph.add_edge("placeholder", END)
            return placeholder_graph.compile()
        
        # Intentar inicializar con MCP real
        if MCP_AVAILABLE:
            server_params = get_server_parameters("/app/mcp_server/custom_server.py")
            stdio_ctx = stdio_client(server_params)
            read, write = await stdio_ctx.__aenter__()
            session = await ClientSession(read, write).__aenter__()
            await session.initialize()
            
            tools, tools_by_name = await load_tools(session)
            
            if tools:
                logger.info(f"Custom Agent inicializado con {len(tools)} herramientas MCP reales")
                return build_custom_agent(llm.bind_tools(tools), tools_by_name)
            else:
                logger.warning("No se encontraron herramientas, usando mock")
                mock_tools = [MockTool("mock_tool_1"), MockTool("mock_tool_2")]
                tools_by_name = {tool.name: tool for tool in mock_tools}
                return build_custom_agent(llm.bind_tools(mock_tools), tools_by_name)
        else:
            # Usar herramientas mock
            logger.info("Usando herramientas mock para Custom Agent")
            mock_tools = [MockTool("mock_tool_1"), MockTool("mock_tool_2")]
            tools_by_name = {tool.name: tool for tool in mock_tools}
            return build_custom_agent(llm.bind_tools(mock_tools), tools_by_name)
    except Exception as e:
        logger.warning(f"Error al inicializar Custom Agent: {e}. Creando placeholder.")
        # Crear placeholder en caso de error
        from langgraph.graph import StateGraph, END, START
        from langchain_core.messages import AIMessage
        
        placeholder_graph = StateGraph(AgentState)
        
        async def placeholder_node(state: AgentState) -> AgentState:
            """Nodo placeholder para Custom Agent."""
            messages = state["messages"]
            response = AIMessage(
                content=f"Error al inicializar Custom Agent: {str(e)}. Este es un grafo placeholder."
            )
            return {
                **state,
                "messages": list(messages) + [response]
            }
        
        placeholder_graph.add_node("placeholder", placeholder_node)
        placeholder_graph.add_edge(START, "placeholder")
        placeholder_graph.add_edge("placeholder", END)
        return placeholder_graph.compile()


# Inicializar grafos de forma síncrona para LangGraph Studio
# LangGraph Studio espera que los grafos estén disponibles de forma síncrona
try:
    # Crear un event loop para inicialización
    if sys.platform == 'win32':
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()
    
    # Inicializar grafos
    rag_graph = loop.run_until_complete(_initialize_rag_agent())
    logger.info("RAG graph inicializado exitosamente")
    
    # Para custom_agent, inicializar
    try:
        custom_graph = loop.run_until_complete(_initialize_custom_agent())
        logger.info("Custom graph inicializado exitosamente")
    except Exception as e:
        logger.error(f"Error al inicializar Custom graph: {e}")
        # Crear un grafo placeholder si hay error
        from langgraph.graph import StateGraph, END, START
        from langchain_core.messages import AIMessage
        
        placeholder_graph = StateGraph(AgentState)
        
        async def placeholder_node(state: AgentState) -> AgentState:
            messages = state["messages"]
            response = AIMessage(content="Error al inicializar Custom Agent")
            return {
                **state,
                "messages": list(messages) + [response]
            }
        
        placeholder_graph.add_node("placeholder", placeholder_node)
        placeholder_graph.add_edge(START, "placeholder")
        placeholder_graph.add_edge("placeholder", END)
        custom_graph = placeholder_graph.compile()
        logger.info("Custom graph placeholder creado")
        
except Exception as e:
    logger.error(f"Error al inicializar grafos: {e}")
    # Crear grafos placeholder en caso de error
    from langgraph.graph import StateGraph, END, START
    from langchain_core.messages import AIMessage
    
    def create_placeholder_graph():
        placeholder_graph = StateGraph(AgentState)
        
        async def placeholder_node(state: AgentState) -> AgentState:
            messages = state["messages"]
            response = AIMessage(content=f"Error al inicializar grafo: {str(e)}")
            return {
                **state,
                "messages": list(messages) + [response]
            }
        
        placeholder_graph.add_node("placeholder", placeholder_node)
        placeholder_graph.add_edge(START, "placeholder")
        placeholder_graph.add_edge("placeholder", END)
        return placeholder_graph.compile()
    
    rag_graph = create_placeholder_graph()
    custom_graph = create_placeholder_graph()

