"""
Servidor MCP para el Agente Especializado
==========================================

Este módulo implementa el servidor MCP que expone múltiples herramientas
personalizadas para el Agente Especializado. Las herramientas permiten al agente
acceder a fuentes de datos externas y realizar tareas específicas del dominio.

IMPLEMENTACIÓN SEMANA 7:
- Implementar al menos 2-3 herramientas MCP personalizadas
- Cada herramienta debe tener un propósito claro y documentado
- Las herramientas deben ser relevantes para el caso de negocio
- Conectar con APIs externas, bases de datos o servicios externos

IMPORTANTE:
- Todas las funciones deben ser async
- Docstrings claros (el LLM los lee para decidir qué herramienta usar)
- Retornar siempre strings
- Manejar errores apropiadamente
"""

from mcp.server.fastmcp import FastMCP
import logging
import sys
import os
import pandas as pd
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


# Configurar logging con UTF-8
# IMPORTANTE: Usar stderr en lugar de stdout para no interferir con la comunicación MCP
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

mcp = FastMCP("custom-server")

# Ruta al archivo CSV con las convocatorias
CONVOCATORIAS_CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "convocatorias.csv"
)

# Configuración del RAG (para la herramienta ask)
RAG_BASE_URL = os.getenv("RAG_BASE_URL", "http://localhost:8001")
RAG_COLLECTION = os.getenv("RAG_COLLECTION", "test_collection")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))


# ===============================================================================
# SEMANA 7: Implementar el servidor MCP personalizado
# ===============================================================================
# Implementación de herramientas personalizadas
# ----------------------------------------------------------
# Agrega aquí las funciones que tu servidor expondrá como herramientas.
# Cada función decorada con @mcp.tool() se registrará automáticamente.
# EJEMPLOS DE HERRAMIENTAS:
#
# a) Búsqueda en Wikipedia:
#    - get_summary(term: str) -> str: Obtiene resumen de un artículo
#    - get_page_sections(term: str) -> str: Lista secciones de un artículo
#    - get_section_content(term: str, section: str) -> str: Obtiene contenido de sección
#
# b) APIs Externas:
#    - get_weather(city: str) -> str: Consulta clima en una ciudad
#    - get_news(topic: str) -> str: Busca noticias sobre un tema
#    - get_stock_price(symbol: str) -> str: Obtiene precio de acciones
#
# c) Cálculos/Utilidades:
#    - calculate(expression: str) -> str: Evalúa expresiones matemáticas
#    - convert_units(value: float, from_unit: str, to_unit: str) -> str
#    - translate_text(text: str, target_lang: str) -> str
#
# d) Bases de datos:
#    - search_database(query: str) -> str: Busca en base de datos
#    - get_user_info(user_id: str) -> str: Obtiene info de usuario
#
# LAS HERRAMIENTAS QUE VAN A IMPLEMENTAR DEBEN ESTAR RELACIONADOS CON EL CASO DE SU NEGOCIO.
#
# Ejemplo:
#
# @mcp.tool()
# async def greet(name: str) -> str:
#     '''
#     Devuelve un saludo personalizado.
#
#     Args:
#         name (str): Nombre de la persona a saludar.
#
#     Returns:
#         str: Mensaje de saludo.
#     '''
#     return f"Hello, {name}!"


@mcp.tool()
async def ask(query: str) -> str:
    """
    Consulta el sistema RAG externo para recuperar contexto relevante sobre convocatorias.
    
    Esta herramienta se conecta al backend RAG y recupera información contextualizada
    basada en la pregunta del usuario. Útil para información general sobre convocatorias,
    conceptos, procedimientos, o cualquier información que esté en los documentos del RAG.
    
    ÚTIL PARA:
    - Información general sobre convocatorias
    - Conceptos y definiciones
    - Procedimientos y procesos
    - Información que está en los documentos cargados en el RAG
    - Cualquier pregunta que NO sea específicamente sobre fechas, recursos o estado actual
    - Identificar o listar nombres de convocatorias mencionadas en los documentos del RAG
    - Enviar historial de la conversionsacion. Se debe enviar la solicitud + correo electronico
    
    NO ÚTIL PARA:
    - Fechas específicas de convocatorias (usar consultar_informacion_convocatoria)
    - Recursos disponibles actuales (usar consultar_informacion_convocatoria)
    - Estado actual de una convocatoria (usar consultar_informacion_convocatoria)
    
    Args:
        query (str): La pregunta del usuario que se enviará al RAG | solicitud enviar historial a correo electroncio (solicitud + correo electronico)
    
    Returns:
        str: El contexto recuperado del sistema RAG con formato listo para ser presentado. mantener el formato de las respuesta
    """
    try:
        logger.info(f"[CUSTOM SERVER] Querying RAG with: {query}")
        
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
                logger.error(f"[CUSTOM SERVER] {error_msg}")
                return f"{error_msg}. Verifica que el servidor RAG esté corriendo en {RAG_BASE_URL}"
            except httpx.HTTPStatusError as e:
                error_msg = f"Error HTTP del RAG (status {e.response.status_code}): {e.response.text}"
                logger.error(f"[CUSTOM SERVER] {error_msg}")
                return error_msg
            
            result = response.json()
            
            # Extraer el contexto de la respuesta
            if "answer" in result:
                context = result["answer"]
                logger.info(f"[CUSTOM SERVER] RAG returned answer (length: {len(context)})")
                return context
            else:
                # Si no hay campo específico, convertir toda la respuesta a string
                context = str(result)
                logger.warning(f"[CUSTOM SERVER] RAG response format unexpected, returning as string")
                return context
            
    except httpx.TimeoutException:
        error_msg = f"Timeout al conectar con el RAG en {rag_url}"
        logger.error(f"[CUSTOM SERVER] {error_msg}")
        return error_msg
    except httpx.RequestError as e:
        error_msg = f"Error de conexión con el RAG: {str(e)}"
        logger.error(f"[CUSTOM SERVER] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error inesperado al consultar el RAG: {str(e)}"
        logger.error(f"[CUSTOM SERVER] {error_msg}")
        return error_msg


@mcp.tool()
async def obtener_url_convocatoria(nombre_convocatoria: str) -> str:
    """
    Busca y devuelve la URL pública de una convocatoria específica.
    
    Esta herramienta busca en el archivo de convocatorias el nombre proporcionado
    y retorna la URL pública donde se encuentra más información sobre la convocatoria,
    incluyendo recursos disponibles y fechas.
    
    Útil cuando el usuario pregunta sobre:
    - "¿Dónde puedo encontrar información sobre la convocatoria X?"
    - "¿Cuál es el link de la convocatoria Y?"
    - "Necesito la URL de la convocatoria Z"
    
    Args:
        nombre_convocatoria: Nombre o parte del nombre de la convocatoria a buscar.
                           Puede ser el nombre completo o palabras clave.
                           Ejemplos:
                           - "Océanos Clima"
                           - "Convocatoria 970"
                           - "IDI"
    
    Returns:
        str: URL de la convocatoria si se encuentra, o mensaje indicando que no se encontró.
    """
    try:
        logger.info(f"[CUSTOM SERVER] Searching for convocatoria: {nombre_convocatoria}")
        
        # Verificar que el archivo existe
        if not os.path.exists(CONVOCATORIAS_CSV_PATH):
            error_msg = f"Archivo de convocatorias no encontrado en: {CONVOCATORIAS_CSV_PATH}"
            logger.error(f"[CUSTOM SERVER] {error_msg}")
            return error_msg
        
        # Leer el archivo CSV
        df = pd.read_csv(CONVOCATORIAS_CSV_PATH)
        
        # Buscar la convocatoria (búsqueda case-insensitive y parcial)
        nombre_lower = nombre_convocatoria.lower()
        matches = df[
            df['nombre_convocatoria'].str.lower().str.contains(nombre_lower, na=False)
        ]
        
        if matches.empty:
            # Listar las convocatorias disponibles
            disponibles = "\n".join([f"- {nombre}" for nombre in df['nombre_convocatoria'].tolist()])
            return (
                f"No se encontró ninguna convocatoria que coincida con '{nombre_convocatoria}'.\n\n"
                f"Convocatorias disponibles:\n{disponibles}"
            )
        
        # Si hay múltiples coincidencias, retornar la primera
        if len(matches) > 1:
            logger.warning(f"[CUSTOM SERVER] Múltiples coincidencias encontradas, usando la primera")
        
        convocatoria = matches.iloc[0]
        nombre = convocatoria['nombre_convocatoria']
        url = convocatoria['url']
        
        logger.info(f"[CUSTOM SERVER] Found convocatoria: {nombre} -> {url}")
        return f"URL de la convocatoria '{nombre}': {url}"
        
    except pd.errors.EmptyDataError:
        error_msg = "El archivo de convocatorias está vacío"
        logger.error(f"[CUSTOM SERVER] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error al buscar la convocatoria: {str(e)}"
        logger.error(f"[CUSTOM SERVER] {error_msg}")
        return error_msg


@mcp.tool()
async def consultar_informacion_convocatoria(
    url_convocatoria: str,
    pregunta: str
) -> str:
    """
    Accede a la URL de una convocatoria, extrae la información de la página web
    y responde una pregunta específica sobre la convocatoria.
    
    Esta herramienta hace web scraping de la página de la convocatoria,
    extrae el contenido relevante (texto, fechas, recursos disponibles, etc.)
    y utiliza esa información para responder la pregunta del usuario.
    
    ÚTIL PARA:
    - Fechas de la convocatoria (apertura, cierre, resultados, plazos)
    - Recursos disponibles (montos, presupuesto, financiamiento)
    - Estado actual de la convocatoria (abierta, cerrada, en evaluación)
    - Información actualizada y específica de la página oficial
    
    NO ÚTIL PARA:
    - Información general sobre conceptos (usar herramienta 'ask' del RAG)
    - Procedimientos generales (usar herramienta 'ask' del RAG)
    - Información que ya está en los documentos del RAG (usar herramienta 'ask' del RAG)
    
    IMPORTANTE: Esta herramienta debe usarse cuando se necesita información específica
    y actualizada de la página oficial de la convocatoria, especialmente fechas, recursos
    y estado actual.
    
    Args:
        url_convocatoria: URL completa de la página de la convocatoria
        pregunta: Pregunta específica sobre la convocatoria que se desea responder.
                 Ejemplos:
                 - "¿Cuáles son las fechas de apertura y cierre?"
                 - "¿Cuál es el monto disponible?"
                 - "¿Cuál es el estado actual de la convocatoria?"
                 - "¿Cuándo se publican los resultados?"
    
    Returns:
        str: Respuesta a la pregunta basada en la información extraída de la página web.
             Si no se puede acceder a la página o extraer información, retorna un mensaje de error.
    """
    try:
        logger.info(f"[CUSTOM SERVER] Fetching information from: {url_convocatoria}")
        logger.info(f"[CUSTOM SERVER] Question: {pregunta}")
        
        # Configurar headers para simular un navegador
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        # Hacer la petición HTTP
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=headers
        ) as client:
            try:
                response = await client.get(url_convocatoria)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                error_msg = f"Error HTTP al acceder a la URL (status {e.response.status_code})"
                logger.error(f"[CUSTOM SERVER] {error_msg}")
                return f"{error_msg}. URL: {url_convocatoria}"
            except httpx.RequestError as e:
                error_msg = f"Error de conexión al acceder a la URL: {str(e)}"
                logger.error(f"[CUSTOM SERVER] {error_msg}")
                return f"{error_msg}. URL: {url_convocatoria}"
        
        # Parsear el HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remover scripts y estilos ANTES de buscar el contenido
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Extraer el texto principal
        # Buscar en el body pero excluyendo elementos no relevantes
        main_content = None
        body = soup.find('body')
        if body:
            # Remover elementos de navegación y menús antes de extraer
            for elem in body.find_all(['nav', 'header', 'footer', 'aside']):
                elem.decompose()
            main_content = body
        else:
            main_content = soup.find('main') or soup.find('article') or soup
        
        # Log para debugging
        if main_content:
            classes = main_content.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
            logger.info(f"[CUSTOM SERVER] Found content element: {main_content.name} with classes: {classes}")
            raw_text = main_content.get_text(separator='\n', strip=True)
            logger.info(f"[CUSTOM SERVER] Content element has {len(raw_text)} characters before cleaning")
        
        # Extraer texto y limpiarlo
        text = main_content.get_text(separator='\n', strip=True)
        
        # Limpiar espacios múltiples y líneas vacías
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        # Filtrar líneas que son solo símbolos o muy cortas sin información útil
        # Remover líneas que son solo "|", "ENG", "app", etc.
        filtered_lines = []
        for line in lines:
            # Saltar líneas que son solo símbolos, muy cortas o contienen solo "app", "ENG", etc.
            if len(line) < 3:
                continue
            if line in ['ENG', 'ESP', 'FRA', 'POR', '|', 'app']:
                continue
            if line.startswith('app |'):
                continue
            filtered_lines.append(line)
        
        cleaned_text = '\n'.join(filtered_lines)
        
        # Si el texto es muy corto, puede que no encontró el contenido correcto
        if len(cleaned_text) < 100:
            logger.warning(f"[CUSTOM SERVER] Texto extraído es muy corto ({len(cleaned_text)} chars), intentando extraer del body completo")
            # Intentar extraer del body completo como último recurso
            body = soup.find('body')
            if body:
                # Remover más elementos no relevantes
                for elem in body.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                    elem.decompose()
                body_text = body.get_text(separator='\n', strip=True)
                body_lines = [line.strip() for line in body_text.split('\n') if line.strip() and len(line.strip()) > 3]
                # Filtrar líneas de ruido
                body_filtered = [line for line in body_lines if line not in ['ENG', 'ESP', 'FRA', 'POR', '|'] and not line.startswith('app |')]
                if len('\n'.join(body_filtered)) > len(cleaned_text):
                    cleaned_text = '\n'.join(body_filtered)
                    logger.info(f"[CUSTOM SERVER] Usando contenido del body completo ({len(cleaned_text)} chars)")
        
        # Limitar el texto a un tamaño razonable (mantener los primeros caracteres, no los últimos)
        # porque la información importante suele estar al inicio
        if len(cleaned_text) > 10000:
            cleaned_text = cleaned_text[:10000] + "..."
            logger.warning(f"[CUSTOM SERVER] Texto truncado a 10000 caracteres (manteniendo inicio)")
        
        logger.info(f"[CUSTOM SERVER] Extracted {len(cleaned_text)} characters from page")
        
        # Construir respuesta con la información extraída
        # La información está en cleaned_text, y el LLM la usará para responder la pregunta
        respuesta = (
            f"Información extraída de la página de la convocatoria:\n\n"
            f"{cleaned_text}\n\n"
            f"Pregunta: {pregunta}\n\n"
            f"Nota: La información anterior fue extraída de la página web. "
            f"Por favor, responde la pregunta basándote en el contenido extraído."
        )
        
        return respuesta
        
    except httpx.TimeoutException:
        error_msg = f"Timeout al acceder a la URL: {url_convocatoria}"
        logger.error(f"[CUSTOM SERVER] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error al consultar información de la convocatoria: {str(e)}"
        logger.error(f"[CUSTOM SERVER] {error_msg}")
        return error_msg


if __name__ == "__main__":
    mcp.run(transport="stdio")
