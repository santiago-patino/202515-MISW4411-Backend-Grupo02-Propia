"""
Prueba rápida sin interacción - Solo para verificar configuración
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

# Verificar configuración
print("Verificando configuracion Gmail...\n")

gmail_user = os.getenv("GMAIL_USER")
gmail_password = os.getenv("GMAIL_APP_PASSWORD")

if not gmail_user:
    print("[ERROR] GMAIL_USER no configurado en .env")
    print("   Agrega: GMAIL_USER=tu_email@gmail.com")
    exit(1)

if not gmail_password:
    print("[ERROR] GMAIL_APP_PASSWORD no configurado en .env")
    print("   Agrega: GMAIL_APP_PASSWORD=tu_contraseña_de_aplicacion")
    print("   Obten la contraseña en: https://myaccount.google.com/apppasswords")
    exit(1)

print(f"[OK] GMAIL_USER: {gmail_user}")
print(f"[OK] GMAIL_APP_PASSWORD: {'*' * len(gmail_password)} (configurado)")
print()
print("Para probar el envio, ejecuta:")
print("   python mcp_server/test_email.py")
print()

