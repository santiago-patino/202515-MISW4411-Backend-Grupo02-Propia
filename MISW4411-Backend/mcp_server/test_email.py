"""
Script de prueba para la herramienta de envío de historial por email
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.chat_history_email import send_chat_history_email


def test_send_email():
    """Prueba el envío de historial por email"""
    
    print("=" * 60)
    print("PRUEBA DE ENVÍO DE HISTORIAL POR EMAIL")
    print("=" * 60)
    print()
    
    # Verificar configuración primero
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not gmail_user or not gmail_password:
        print("[ERROR] Configuracion Gmail no encontrada")
        print()
        print("Por favor, configura en el archivo .env:")
        print("  GMAIL_USER=tu_email@gmail.com")
        print("  GMAIL_APP_PASSWORD=tu_contraseña_de_aplicacion")
        print()
        return
    
    print(f"[OK] Gmail configurado: {gmail_user}")
    print()
    
    # Ejemplo de historial de chat
    chat_history = [
        {
            "role": "user",
            "content": "¿Cuáles son los requisitos para participar en la convocatoria 970?",
            "timestamp": datetime.now().isoformat()
        },
        {
            "role": "assistant",
            "content": "Los requisitos para la convocatoria 970 incluyen: tener título de doctorado, mínimo 5 años de experiencia en investigación, y al menos 10 publicaciones indexadas.",
            "timestamp": datetime.now().isoformat(),
            "sources": ["convocatoria_970.pdf"]
        },
        {
            "role": "user",
            "content": "Descarga el documento convocatoria_970.pdf en formato markdown",
            "timestamp": datetime.now().isoformat()
        },
    ]
    
    # Solicitar email del destinatario
    print("Ingresa los datos para la prueba:")
    print("-" * 60)
    recipient = input("Email del destinatario: ").strip()
    
    if not recipient:
        print("[ERROR] Email requerido")
        return
    
    print()
    print("Enviando historial por email (formato HTML)...")
    print()
    
    # Llamar a la herramienta
    result = send_chat_history_email(
        recipient_email=recipient,
        chat_history=chat_history
    )
    
    # Mostrar resultado
    result_dict = json.loads(result)
    
    print("=" * 60)
    print("RESULTADO:")
    print("=" * 60)
    print(json.dumps(result_dict, indent=2, ensure_ascii=False))
    print("=" * 60)
    print()
    
    # Verificar éxito
    if result_dict.get("success"):
        print(f"[OK] Email enviado exitosamente a {recipient}")
        print(f"   Revisa tu bandeja de entrada (y spam si no lo ves)")
    else:
        print(f"[ERROR] Error: {result_dict.get('error', 'Error desconocido')}")
        print()
        print("Posibles soluciones:")
        print("1. Verifica que GMAIL_USER y GMAIL_APP_PASSWORD estén correctos en .env")
        print("2. Asegúrate de usar una 'Contraseña de aplicación', no tu contraseña normal")
        print("3. Verifica que la verificación en 2 pasos esté activada en tu cuenta Google")


if __name__ == "__main__":
    try:
        test_send_email()
    except KeyboardInterrupt:
        print("\n\n[INFO] Interrupcion del usuario")
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
