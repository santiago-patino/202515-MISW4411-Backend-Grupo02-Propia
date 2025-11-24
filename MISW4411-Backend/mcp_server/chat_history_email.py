"""
Servidor MCP para envío de historial de chat por correo

Este módulo implementa una herramienta MCP que permite al LLM
enviar el historial completo de la conversación por correo electrónico usando Gmail SMTP.
"""

from mcp.server.fastmcp import FastMCP
from typing import List, Dict
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import html

# Cargar variables de entorno
load_dotenv()

# Inicializa el servidor MCP
mcp = FastMCP("chat-history-email")


def _format_history_html(chat_history: List[Dict]) -> str:
    """Formatea el historial en HTML"""
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_msgs = len(chat_history)
    
    html_content = '<!DOCTYPE html>\n'
    html_content += '<html>\n'
    html_content += '<head>\n'
    html_content += '    <meta charset="UTF-8">\n'
    html_content += '    <style>\n'
    html_content += '        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }\n'
    html_content += '        .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }\n'
    html_content += '        .message { margin: 20px 0; padding: 15px; border-radius: 8px; }\n'
    html_content += '        .user { background-color: #e3f2fd; border-left: 4px solid #2196f3; }\n'
    html_content += '        .assistant { background-color: #f5f5f5; border-left: 4px solid #4caf50; }\n'
    html_content += '        .timestamp { font-size: 0.85em; color: #666; margin-bottom: 5px; }\n'
    html_content += '        .sources { font-size: 0.9em; color: #666; margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd; }\n'
    html_content += '        .download-link { color: #2196f3; text-decoration: none; font-weight: 500; }\n'
    html_content += '        .download-link:hover { text-decoration: underline; }\n'
    html_content += '        .footer { margin-top: 30px; padding-top: 20px; border-top: 2px solid #ddd; font-size: 0.9em; color: #666; text-align: center; }\n'
    html_content += '    </style>\n'
    html_content += '</head>\n'
    html_content += '<body>\n'
    html_content += '    <div class="header">\n'
    html_content += '        <h2>Historial de Conversacion</h2>\n'
    html_content += '        <p><strong>Fecha:</strong> ' + date_str + '</p>\n'
    html_content += '        <p><strong>Total de mensajes:</strong> ' + str(total_msgs) + '</p>\n'
    html_content += '    </div>\n'
    
    user_count_html = 0
    assistant_count_html = 0
    
    for i, msg in enumerate(chat_history, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        sources = msg.get("sources", [])
        download_link = msg.get("download_link", "")
        tool_used = msg.get("tool_used")
        
        if role == "user":
            user_count_html += 1
        elif role == "assistant":
            assistant_count_html += 1
        
        role_class = "user" if role == "user" else "assistant"
        role_label = "Usuario" if role == "user" else "Asistente"
        
        # Formatear timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = timestamp
        else:
            formatted_time = "N/A"
        
        # Escapar contenido HTML para evitar problemas
        content_escaped = html.escape(str(content))
        
        # Construir HTML de forma segura
        html_content += '<div class="message ' + role_class + '">\n'
        html_content += '    <div class="timestamp">\n'
        html_content += '        <strong>' + role_label + '</strong> - Mensaje #' + str(i) + ' - ' + formatted_time + '\n'
        html_content += '    </div>\n'
        html_content += '    <div>' + content_escaped + '</div>\n'
        
        if sources:
            sources_list = ", ".join([html.escape(str(s)) for s in sources]) if isinstance(sources, list) else html.escape(str(sources))
            html_content += '<div class="sources"><strong>Fuentes consultadas:</strong> ' + sources_list + '</div>\n'
        
        if download_link:
            download_link_escaped = html.escape(str(download_link))
            html_content += '<div class="sources"><a href="' + download_link_escaped + '" class="download-link">Descargar archivo</a></div>\n'
        
        if tool_used:
            tool_escaped = html.escape(str(tool_used))
            html_content += '<div class="sources"><strong>Herramienta usada:</strong> ' + tool_escaped + '</div>\n'
        
        html_content += '</div>\n'
    
    print(f"✅ [FORMAT HTML] HTML generado: {user_count_html} mensajes user, {assistant_count_html} mensajes assistant")
    
    html_content += '    <div class="footer">\n'
    html_content += '        <p>Este email fue generado automaticamente por el sistema RAG.</p>\n'
    html_content += '        <p>Para mas informacion, contacta al administrador del sistema.</p>\n'
    html_content += '    </div>\n'
    html_content += '</body>\n'
    html_content += '</html>\n'
    
    return html_content


def _format_history_text(chat_history: List[Dict]) -> str:
    """Formatea el historial en texto plano"""
    text = "=" * 60 + "\n"
    text += "HISTORIAL DE CONVERSACIÓN\n"
    text += "=" * 60 + "\n"
    text += f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    text += f"Total de mensajes: {len(chat_history)}\n"
    text += "=" * 60 + "\n\n"
    
    for i, msg in enumerate(chat_history, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        sources = msg.get("sources", [])
        download_link = msg.get("download_link", "")
        tool_used = msg.get("tool_used")
        
        role_label = "USUARIO" if role == "user" else "ASISTENTE"
        
        # Formatear timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = timestamp
        else:
            formatted_time = "N/A"
        
        text += f"\n[{role_label}] - Mensaje #{i} - {formatted_time}\n"
        text += "-" * 60 + "\n"
        text += f"{content}\n"
        
        if sources:
            sources_list = ", ".join(sources) if isinstance(sources, list) else str(sources)
            text += f"\nFuentes consultadas: {sources_list}\n"
        
        if download_link:
            text += f"\nLink de descarga: {download_link}\n"
        
        if tool_used:
            text += f"\nHerramienta usada: {tool_used}\n"
        
        text += "\n" + "=" * 60 + "\n"
    
    text += "\nEste email fue generado automáticamente por el sistema RAG.\n"
    
    return text


@mcp.tool()
def send_chat_history_email(
    recipient_email: str,
    chat_history: List[Dict]
) -> str:
    """
    Envía el historial completo del chat por correo electrónico usando Gmail SMTP.

    Esta herramienta formatea el historial de la conversación (mensajes del usuario
    y respuestas del asistente) y lo envía por correo electrónico al destinatario
    especificado usando Gmail SMTP. El email se envía siempre en formato HTML.

    Args:
        recipient_email (str): Email del destinatario donde se enviará el historial
        chat_history (List[Dict]): Lista de mensajes del chat. Cada mensaje debe tener:
            - role: "user" o "assistant"
            - content: Contenido del mensaje
            - timestamp: Fecha y hora del mensaje (opcional)
            - sources: Lista de fuentes consultadas (opcional)
            - download_link: Link de descarga si aplica (opcional)
            - tool_used: Herramienta MCP usada (opcional)

    Returns:
        str: JSON con el resultado del envío del email
    """
    try:
        print("\n" + "="*80)
        print("📧 [MCP TOOL: send_chat_history_email] Ejecutando herramienta MCP")
        print("="*80)
        print(f"📮 Email destinatario: {recipient_email}")
        print(f"📊 Mensajes en historial: {len(chat_history)}")
        
        # Validar email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        print(f"🔍 Validando formato de email...")
        if not re.match(email_pattern, recipient_email):
            print(f"❌ Email inválido: {recipient_email}")
            return json.dumps({
                "success": False,
                "error": f"Email inválido: {recipient_email}"
            }, indent=2, ensure_ascii=False)
        print(f"✅ Email válido")
        
        # Validar historial
        print(f"🔍 Validando historial...")
        if not chat_history or len(chat_history) == 0:
            print(f"❌ Historial vacío")
            return json.dumps({
                "success": False,
                "error": "El historial del chat está vacío"
            }, indent=2, ensure_ascii=False)
        print(f"✅ Historial válido: {len(chat_history)} mensajes")
        
        # Generar asunto automáticamente
        date_str = datetime.now().strftime("%Y-%m-%d")
        subject = f"Historial de Conversación - {date_str}"
        print(f"📝 Asunto generado: {subject}")
        
        # Formatear historial siempre en HTML
        email_body = _format_history_html(chat_history)
        print(f"✅ Email HTML generado: {len(email_body)} caracteres")
        
        # Obtener configuración Gmail SMTP de variables de entorno
        print(f"🔐 Obteniendo configuración Gmail SMTP...")
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        
        # Validar configuración
        if not gmail_user or not gmail_password:
            print(f"❌ Configuración Gmail no encontrada")
            return json.dumps({
                "success": False,
                "error": "Configuración Gmail no encontrada. Configura GMAIL_USER y GMAIL_APP_PASSWORD en el archivo .env"
            }, indent=2, ensure_ascii=False)
        print(f"✅ Configuración Gmail encontrada: {gmail_user}")
        
        # Crear mensaje
        print(f"📧 Creando mensaje de email...")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = recipient_email
        
        # Siempre en formato HTML
        msg.attach(MIMEText(email_body, "html", "utf-8"))
        print(f"✅ Mensaje creado")
        
        # Enviar email usando Gmail SMTP
        print(f"📤 Conectando a servidor SMTP (smtp.gmail.com:587)...")
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                print(f"🔒 Iniciando TLS...")
                server.starttls()
                print(f"🔐 Autenticando con Gmail...")
                server.login(gmail_user, gmail_password)
                print(f"✅ Autenticación exitosa")
                print(f"📨 Enviando mensaje...")
                server.send_message(msg)
                print(f"✅ Email enviado exitosamente")
            
            result = {
                "success": True,
                "recipient": recipient_email,
                "sent_at": datetime.now().isoformat(),
                "message": "Historial enviado exitosamente por correo electrónico",
                "total_messages": len(chat_history),
                "format": "html",
                "subject": subject
            }
            print("="*80)
            print("✅ [MCP TOOL RESULT] Éxito en ejecución de herramienta")
            print("="*80)
            print(f"📧 Recipient: {result['recipient']}")
            print(f"📅 Sent at: {result['sent_at']}")
            print(f"📊 Total messages: {result['total_messages']}")
            print(f"📝 Subject: {result['subject']}")
            print("="*80 + "\n")
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ [MCP TOOL ERROR] Error de autenticación SMTP: {str(e)}")
            return json.dumps({
                "success": False,
                "error": "Error de autenticación Gmail. Verifica GMAIL_USER y GMAIL_APP_PASSWORD. Necesitas una 'Contraseña de aplicación' de Google, no tu contraseña normal."
            }, indent=2, ensure_ascii=False)
        except smtplib.SMTPException as e:
            print(f"❌ [MCP TOOL ERROR] Error SMTP: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Error al enviar email: {str(e)}"
            }, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"❌ [MCP TOOL EXCEPTION] Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "success": False,
            "error": f"Error inesperado: {str(e)}"
        }, indent=2, ensure_ascii=False)


# Ejecución del servidor MCP
if __name__ == "__main__":
    mcp.run(transport="stdio")
