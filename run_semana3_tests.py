#!/usr/bin/env python3
"""
Script de ejecución para pruebas de Semana 3
============================================

Este script ejecuta todas las pruebas y evaluaciones de la Semana 3,
incluyendo preprocesamiento, reranking, query rewriting y evaluación RAGAS.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """
    Ejecuta un comando y muestra el resultado.
    
    Args:
        command: Comando a ejecutar
        description: Descripción del comando
        
    Returns:
        bool: True si el comando fue exitoso
    """
    print(f"\n🔄 {description}")
    print(f"📝 Comando: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - EXITOSO")
            if result.stdout:
                print("📤 Salida:")
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FALLÓ")
            if result.stderr:
                print("📤 Error:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando {description}: {str(e)}")
        return False

def main():
    """Función principal del script."""
    print("🚀 Iniciando pruebas de Semana 3")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not Path("app").exists():
        print("❌ Error: Ejecutar desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Lista de pruebas a ejecutar
    tests = [
        {
            "command": "python -m pytest tests/semana3/test_preprocessing.py -v",
            "description": "Pruebas de preprocesamiento"
        },
        {
            "command": "python -m pytest tests/semana3/test_reranking.py -v",
            "description": "Pruebas de reranking"
        },
        {
            "command": "python -m pytest tests/semana3/test_query_rewriting.py -v",
            "description": "Pruebas de query rewriting"
        },
        {
            "command": "python -m pytest tests/semana3/test_integration.py -v",
            "description": "Pruebas de integración"
        }
    ]
    
    # Ejecutar pruebas unitarias
    print("\n📋 Ejecutando pruebas unitarias...")
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        if run_command(test["command"], test["description"]):
            passed_tests += 1
        time.sleep(1)  # Pausa entre pruebas
    
    # Resumen de pruebas unitarias
    print(f"\n📊 Resumen de pruebas unitarias: {passed_tests}/{total_tests} exitosas")
    
    # Ejecutar evaluación RAGAS
    print("\n📋 Ejecutando evaluación RAGAS...")
    ragas_success = run_command(
        "python tests/semana3/ragas_eval.py",
        "Evaluación RAGAS Semana 3"
    )
    
    # Ejecutar pruebas del endpoint
    print("\n📋 Ejecutando pruebas del endpoint...")
    endpoint_success = run_command(
        "python -m pytest tests/semana1/test_endpoints_basic.py -v",
        "Pruebas del endpoint básico"
    )
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    print(f"✅ Pruebas unitarias: {passed_tests}/{total_tests}")
    print(f"✅ Evaluación RAGAS: {'EXITOSA' if ragas_success else 'FALLÓ'}")
    print(f"✅ Pruebas endpoint: {'EXITOSA' if endpoint_success else 'FALLÓ'}")
    
    # Determinar éxito general
    all_success = (passed_tests == total_tests and ragas_success and endpoint_success)
    
    if all_success:
        print("\n🎉 ¡Todas las pruebas de Semana 3 fueron exitosas!")
        print("✅ El sistema está listo para la entrega")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisar los errores arriba.")
    
    print("\n📁 Resultados guardados en:")
    print("   - tests/semana3/results/evaluation_results.json")
    print("   - tests/semana3/results/evaluation_report.md")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
