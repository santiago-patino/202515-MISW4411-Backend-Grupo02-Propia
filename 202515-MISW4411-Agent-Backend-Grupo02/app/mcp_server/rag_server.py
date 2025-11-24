"""
Servidor MCP para el Agente RAG
================================

Este módulo implementa el servidor MCP que expone la herramienta para consultar
el sistema RAG externo. El agente RAG utilizará esta herramienta para recuperar
contexto relevante de la base de datos vectorial.

IMPLEMENTACIÓN SEMANA 6:
- Implementar la herramienta MCP "ask" que consulta el sistema RAG
- La herramienta debe conectarse a la API del RAG (desarrollado en semanas anteriores)
- Debe manejar errores de conexión y timeout
- Retornar el contexto recuperado como string
"""

from mcp.server.fastmcp import FastMCP
import logging
import httpx
import os
import sys


# Configurar logging con UTF-8
# IMPORTANTE: Usar stderr en lugar de stdout para no interferir con la comunicación MCP
# MCP usa stdout para JSONRPC, por lo que los logs deben ir a stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)  # Cambiar a stderr para no interferir con MCP
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

mcp = FastMCP("rag-server")


# ===============================================================================
# SEMANA 6: Implementar el servidor MCP para RAG
# ===============================================================================

# Configuración del RAG
RAG_BASE_URL = os.getenv("RAG_BASE_URL", "http://localhost:8001")
RAG_COLLECTION = os.getenv("RAG_COLLECTION", "test_collection")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))


@mcp.tool()
async def ask(query: str) -> str:
    """
    Consulta el sistema RAG externo para recuperar contexto relevante.
    
    Esta herramienta se conecta al backend RAG y recupera información
    contextualizada basada en la pregunta del usuario.
    
    Args:
        query (str): La pregunta del usuario que se enviará al RAG
    
    Returns:
        str: El contexto recuperado del sistema RAG como texto plano
    """
    try:
        # Construir la URL completa del endpoint
        rag_url = f"{RAG_BASE_URL}/api/v1/ask"
        
        # Preparar el body de la petición
        body = {
            "question": query,
            "top_k": RAG_TOP_K,
            "collection": RAG_COLLECTION,
            "force_rebuild": False
        }
        
        # Realizar la petición HTTP POST
        # Configurar el cliente con opciones para mejorar la conectividad
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False  # Deshabilitar verificación SSL si es necesario
        ) as client:
            try:
                response = await client.post(rag_url, json=body)
                response.raise_for_status()  # Lanza excepción si hay error HTTP
            except httpx.ConnectError as e:
                error_msg = f"Error de conexión con el RAG: {str(e)}"
                logger.error(f"[RAG SERVER] {error_msg}")
                raise Exception(error_msg) from e
            except httpx.HTTPStatusError as e:
                error_msg = f"Error HTTP del RAG (status {e.response.status_code}): {e.response.text}"
                logger.error(f"[RAG SERVER] {error_msg}")
                raise Exception(error_msg) from e
            
            result = response.json()
            
            # Extraer el contexto de la respuesta
            # Asumiendo que el RAG retorna un campo con el contexto/answer
            # Ajustar según la estructura real de la respuesta del RAG
            if "answer" in result:
                context = result["answer"]
            else:
                # Si no hay campo específico, convertir toda la respuesta a string
                context = str(result)
            
            return context
            
    except httpx.TimeoutException:
        error_msg = f"Timeout al conectar con el RAG en {rag_url}"
        logger.error(f"[RAG SERVER] {error_msg}")
        raise Exception(error_msg)
    except httpx.RequestError as e:
        error_msg = f"Error de conexión con el RAG: {str(e)}"
        logger.error(f"[RAG SERVER] {error_msg}")
        raise Exception(error_msg)
    except httpx.HTTPStatusError as e:
        error_msg = f"Error HTTP del RAG (status {e.response.status_code}): {e.response.text}"
        logger.error(f"[RAG SERVER] {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error inesperado al consultar el RAG: {str(e)}"
        logger.error(f"[RAG SERVER] {error_msg}")
        raise Exception(error_msg)


if __name__ == "__main__":
    mcp.run(transport="stdio")