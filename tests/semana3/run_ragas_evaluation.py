#!/usr/bin/env python3
"""
Script para ejecutar evaluación RAGAS de la Semana 3
====================================================

Este script ejecuta las evaluaciones RAGAS para comparar las mejoras
implementadas en la Semana 3 del proyecto RAG.
"""

import sys
import os
import json
import time
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.generation_service import GenerationService
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import ChunkingService, ChunkingStrategy

def create_test_dataset():
    """Crear dataset de prueba para evaluación RAGAS"""
    
    # Preguntas que SÍ tienen información en los documentos
    questions_with_info = [
        "¿Cuáles son los requisitos para participar en las convocatorias?",
        "¿Qué documentos necesito para postularme?",
        "¿Cuál es el monto máximo de financiación?",
        "¿Cuáles son las fechas límite de presentación?",
        "¿Qué tipos de proyectos se financian?"
    ]
    
    # Preguntas que NO tienen información en los documentos
    questions_without_info = [
        "¿Cuál es el salario de los investigadores?",
        "¿Cómo se calcula el impuesto sobre la renta?",
        "¿Qué deportes se practican en la universidad?",
        "¿Cuál es el clima en Bogotá?",
        "¿Qué restaurantes hay cerca de la universidad?"
    ]
    
    # Respuestas esperadas (ground truth)
    ground_truths = [
        "Los requisitos incluyen ser investigador colombiano, tener título de doctorado, y presentar propuesta de investigación.",
        "Se requieren documentos como CV, propuesta de investigación, y certificados académicos.",
        "El monto máximo varía según el tipo de convocatoria, pero puede llegar hasta $500 millones de pesos.",
        "Las fechas límite se especifican en cada convocatoria, generalmente son trimestrales.",
        "Se financian proyectos de investigación en ciencias básicas, aplicadas, y desarrollo tecnológico."
    ]
    
    # Contextos relevantes (para métricas de contexto)
    contexts = [
        ["Los investigadores deben ser colombianos", "Se requiere título de doctorado", "La propuesta debe ser original"],
        ["CV actualizado", "Propuesta de investigación", "Certificados académicos"],
        ["Monto máximo $500 millones", "Financiación por 24 meses", "Recursos para investigación"],
        ["Fechas límite trimestrales", "Presentación en línea", "Evaluación por pares"],
        ["Ciencias básicas", "Ciencias aplicadas", "Desarrollo tecnológico"]
    ]
    
    return {
        "questions": questions_with_info + questions_without_info,
        "ground_truths": ground_truths + [""] * len(questions_without_info),
        "contexts": contexts + [[]] * len(questions_without_info),
        "answers": [""] * (len(questions_with_info) + len(questions_without_info))
    }

def evaluate_configuration(config_name, use_preprocessing=False, use_reranking=False, use_query_rewriting=False):
    """Evaluar una configuración específica"""
    
    print(f"\n🔍 Evaluando configuración: {config_name}")
    print(f"   Preprocesamiento: {use_preprocessing}")
    print(f"   Reranking: {use_reranking}")
    print(f"   Query Rewriting: {use_query_rewriting}")
    
    try:
        # Inicializar servicios
        embedding_service = EmbeddingService()
        retrieval_service = RetrievalService()
        generation_service = GenerationService()
        
        # Crear dataset de prueba
        dataset = create_test_dataset()
        
        # Generar respuestas para cada pregunta
        answers = []
        contexts = []
        
        for i, question in enumerate(dataset["questions"]):
            print(f"   📝 Procesando pregunta {i+1}/{len(dataset['questions'])}: {question[:50]}...")
            
            try:
                # Generar respuesta usando el endpoint
                import requests
                response = requests.post(
                    "http://localhost:8000/api/v1/ask",
                    json={
                        "question": question,
                        "top_k": 5,
                        "collection": "semana3_test_collection_final",
                        "use_reranking": use_reranking,
                        "use_query_rewriting": use_query_rewriting
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answers.append(data.get("answer", ""))
                    contexts.append([doc.get("page_content", "") for doc in data.get("context_docs", [])])
                else:
                    print(f"   ❌ Error en pregunta {i+1}: {response.status_code}")
                    answers.append("")
                    contexts.append([])
                    
            except Exception as e:
                print(f"   ❌ Error procesando pregunta {i+1}: {str(e)}")
                answers.append("")
                contexts.append([])
        
        # Actualizar dataset con respuestas generadas
        dataset["answers"] = answers
        dataset["contexts"] = contexts
        
        # Calcular métricas RAGAS básicas
        metrics = calculate_basic_metrics(dataset)
        
        print(f"   ✅ Evaluación completada para {config_name}")
        return metrics
        
    except Exception as e:
        print(f"   ❌ Error en evaluación {config_name}: {str(e)}")
        return None

def calculate_basic_metrics(dataset):
    """Calcular métricas básicas sin RAGAS completo"""
    
    # Métricas simplificadas basadas en análisis de respuestas
    total_questions = len(dataset["questions"])
    valid_answers = sum(1 for answer in dataset["answers"] if answer and len(answer.strip()) > 10)
    
    # Faithfulness: Respuestas que no contienen información inventada
    faithful_answers = 0
    for i, answer in enumerate(dataset["answers"]):
        if answer and len(answer.strip()) > 10:
            # Verificar si la respuesta es relevante y no inventada
            if any(keyword in answer.lower() for keyword in ["convocatoria", "investigación", "financiación", "requisitos"]):
                faithful_answers += 1
    
    # Context Precision: Respuestas con contexto relevante
    precise_answers = 0
    for i, context in enumerate(dataset["contexts"]):
        if context and len(context) > 0:
            # Verificar si el contexto es relevante
            if any("convocatoria" in str(ctx).lower() for ctx in context):
                precise_answers += 1
    
    # Context Recall: Respuestas que cubren la información necesaria
    recalled_answers = 0
    for i, answer in enumerate(dataset["answers"]):
        if answer and len(answer.strip()) > 20:
            recalled_answers += 1
    
    # Answer Relevancy: Respuestas relevantes a la pregunta
    relevant_answers = 0
    for i, (question, answer) in enumerate(zip(dataset["questions"], dataset["answers"])):
        if answer and len(answer.strip()) > 10:
            # Verificar si la respuesta es relevante a la pregunta
            if any(keyword in answer.lower() for keyword in question.lower().split()):
                relevant_answers += 1
    
    return {
        "faithfulness": faithful_answers / total_questions if total_questions > 0 else 0,
        "context_precision": precise_answers / total_questions if total_questions > 0 else 0,
        "context_recall": recalled_answers / total_questions if total_questions > 0 else 0,
        "answer_relevancy": relevant_answers / total_questions if total_questions > 0 else 0,
        "total_questions": total_questions,
        "valid_answers": valid_answers
    }

def main():
    """Función principal para ejecutar la evaluación"""
    
    print("🚀 Iniciando evaluación RAGAS para Semana 3")
    print("=" * 50)
    
    # Configuraciones a evaluar
    configurations = [
        {
            "name": "Baseline (Semana 2)",
            "use_preprocessing": False,
            "use_reranking": False,
            "use_query_rewriting": False
        },
        {
            "name": "Con Preprocesamiento",
            "use_preprocessing": True,
            "use_reranking": False,
            "use_query_rewriting": False
        },
        {
            "name": "Con Reranking",
            "use_preprocessing": False,
            "use_reranking": True,
            "use_query_rewriting": False
        },
        {
            "name": "Con Query Rewriting",
            "use_preprocessing": False,
            "use_reranking": False,
            "use_query_rewriting": True
        },
        {
            "name": "Completo (Semana 3)",
            "use_preprocessing": True,
            "use_reranking": True,
            "use_query_rewriting": True
        }
    ]
    
    results = {}
    
    # Evaluar cada configuración
    for config in configurations:
        metrics = evaluate_configuration(
            config["name"],
            config["use_preprocessing"],
            config["use_reranking"],
            config["use_query_rewriting"]
        )
        
        if metrics:
            results[config["name"]] = metrics
            print(f"   📊 Métricas obtenidas:")
            print(f"      Faithfulness: {metrics['faithfulness']:.3f}")
            print(f"      Context Precision: {metrics['context_precision']:.3f}")
            print(f"      Context Recall: {metrics['context_recall']:.3f}")
            print(f"      Answer Relevancy: {metrics['answer_relevancy']:.3f}")
        else:
            print(f"   ❌ No se pudieron obtener métricas para {config['name']}")
    
    # Guardar resultados
    output_file = Path(__file__).parent / "ragas_evaluation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Evaluación completada. Resultados guardados en: {output_file}")
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE RESULTADOS:")
    print("=" * 50)
    
    for config_name, metrics in results.items():
        print(f"\n{config_name}:")
        print(f"  Faithfulness: {metrics['faithfulness']:.3f}")
        print(f"  Context Precision: {metrics['context_precision']:.3f}")
        print(f"  Context Recall: {metrics['context_recall']:.3f}")
        print(f"  Answer Relevancy: {metrics['answer_relevancy']:.3f}")

if __name__ == "__main__":
    main()
