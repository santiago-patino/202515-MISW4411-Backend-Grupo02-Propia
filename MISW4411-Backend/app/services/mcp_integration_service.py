"""
Servicio de Integración MCP con el LLM
======================================

Este módulo integra las herramientas MCP con el sistema de generación,
permitiendo que el LLM use herramientas externas como envío de emails.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Agregar mcp_server al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_server.chat_history_email import send_chat_history_email


class MCPIntegrationService:
    """
    Servicio para integrar herramientas MCP con el LLM.
    
    Permite que el LLM use herramientas externas como envío de emails
    basándose en las solicitudes del usuario.
    """
    
    def __init__(self):
        """Inicializa el servicio de integración MCP."""
        self.available_tools = {
            "send_chat_history_email": {
                "name": "send_chat_history_email",
                "description": "Envía el historial completo de la conversación por correo electrónico al destinatario especificado. Usa esta herramienta cuando el usuario solicite enviar el historial por correo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient_email": {
                            "type": "string",
                            "description": "Email del destinatario donde se enviará el historial"
                        },
                        "chat_history": {
                            "type": "array",
                            "description": "Lista de mensajes del chat con role (user/assistant) y content",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant"]},
                                    "content": {"type": "string"}
                                },
                                "required": ["role", "content"]
                            }
                        }
                    },
                    "required": ["recipient_email", "chat_history"]
                }
            }
        }
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Retorna las herramientas MCP en formato compatible con LangChain/Gemini.
        
        Returns:
            Lista de herramientas disponibles para el LLM
        """
        return [self.available_tools["send_chat_history_email"]]
    
    def execute_tool(
        self, 
        tool_name: str, 
        tool_input: Dict[str, Any],
        chat_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ejecuta una herramienta MCP.
        
        Args:
            tool_name: Nombre de la herramienta a ejecutar
            tool_input: Parámetros de entrada para la herramienta
            chat_history: Historial completo de la conversación
            
        Returns:
            Resultado de la ejecución de la herramienta
        """
        print(f"\n🔧 [MCP INTEGRATION SERVICE] Ejecutando herramienta: {tool_name}")
        print(f"📥 Parámetros recibidos:")
        for key, value in tool_input.items():
            if key == "chat_history":
                print(f"   - {key}: {len(value) if isinstance(value, list) else 'N/A'} mensajes")
            else:
                print(f"   - {key}: {value}")
        print(f"📊 Historial proporcionado: {len(chat_history)} mensajes")
        
        if tool_name == "send_chat_history_email":
            return self._execute_send_email(tool_input, chat_history)
        else:
            print(f"❌ [MCP ERROR] Herramienta desconocida: {tool_name}")
            return {
                "success": False,
                "error": f"Herramienta desconocida: {tool_name}"
            }
    
    def _execute_send_email(
        self, 
        tool_input: Dict[str, Any],
        chat_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ejecuta la herramienta de envío de email.
        
        Args:
            tool_input: Debe contener 'recipient_email' y opcionalmente 'chat_history'
            chat_history: Historial completo de la conversación
            
        Returns:
            Resultado del envío del email
        """
        try:
            print(f"\n📧 [MCP TOOL: send_chat_history_email] Iniciando ejecución...")
            recipient_email = tool_input.get("recipient_email")
            
            if not recipient_email:
                print(f"❌ [MCP TOOL ERROR] Email del destinatario no proporcionado")
                return {
                    "success": False,
                    "error": "Email del destinatario requerido"
                }
            
            # SIEMPRE usar el historial pasado como parámetro (es el historial completo formateado)
            # No buscar en tool_input porque el historial se pasa como parámetro separado
            history_to_send = chat_history if chat_history else []
            
            # Asegurar que el historial tenga el formato correcto
            formatted_history = []
            for msg in history_to_send:
                if isinstance(msg, dict):
                    formatted_msg = {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    }
                    # Preservar timestamp si existe
                    if "timestamp" in msg:
                        formatted_msg["timestamp"] = msg["timestamp"]
                    formatted_history.append(formatted_msg)
            
            # Llamar a la herramienta MCP
            result_str = send_chat_history_email(
                recipient_email=recipient_email,
                chat_history=formatted_history
            )
            
            # Parsear el resultado
            result = json.loads(result_str)
            
            return result
            
        except Exception as e:
            print(f"❌ [MCP TOOL EXCEPTION] Error ejecutando herramienta: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Error ejecutando herramienta: {str(e)}"
            }
    
    def format_chat_history_for_tool(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formatea el historial de mensajes para la herramienta MCP.
        
        Args:
            messages: Lista de mensajes en formato del sistema
            
        Returns:
            Historial formateado para la herramienta
        """
        formatted = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_msg = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                # Agregar timestamp si existe
                if "timestamp" in msg and msg["timestamp"]:
                    formatted_msg["timestamp"] = msg["timestamp"]
                formatted.append(formatted_msg)
        
        return formatted

