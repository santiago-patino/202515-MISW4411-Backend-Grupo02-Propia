"""
Servidor MCP para envío de historial de chat por correo

Este paquete contiene la herramienta MCP que permite al LLM
enviar el historial de conversación por correo electrónico.
"""

from .chat_history_email import mcp

__all__ = ["mcp"]

