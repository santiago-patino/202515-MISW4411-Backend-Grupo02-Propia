"""
Evaluación RAGAS para Semana 3
==============================

Este módulo implementa la evaluación completa del sistema RAG
usando RAGAS para medir el impacto de las mejoras implementadas
en la Semana 3.
"""

import os
import sys
import json
import time
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datasets import Dataset

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.chunking_service import ChunkingService, ChunkingStrategy
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.services.generation_service import GenerationService
from app.routers.ask import basic_rag_processing

# Importar métricas RAGAS
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
    answer_similarity
)


class Semana3RagasEvaluator:
    """Evaluador RAGAS para la Semana 3."""
    
    def __init__(self, config_path: str = "tests/semana3/ragas_config.yml"):
        """
        Inicializa el evaluador con la configuración.
        
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.results = {}
        
        # Inicializar servicios
        self.embedding_service = EmbeddingService()
        self.retrieval_service = RetrievalService()
        self.generation_service = GenerationService()
        
        print(f"📊 Evaluador RAGAS Semana 3 inicializado")
        print(f"📋 Configuración cargada desde: {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"❌ Error cargando configuración: {str(e)}")
            return {}
    
    def _load_test_questions(self) -> List[Dict[str, Any]]:
        """Carga las preguntas de prueba."""
        questions_file = self.config.get("test_data", {}).get("questions_file", "sample_questions.json")
        questions_path = Path("tests/semana2") / questions_file
        
        try:
            with open(questions_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            return questions
        except Exception as e:
            print(f"⚠️ Error cargando preguntas: {str(e)}")
            return []
    
    def _create_test_dataset(self, questions: List[Dict[str, Any]]) -> Dataset:
        """Crea el dataset de prueba para RAGAS."""
        dataset_data = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": []
        }
        
        for q in questions:
            dataset_data["question"].append(q["question"])
            dataset_data["answer"].append(q.get("answer", ""))
            dataset_data["contexts"].append(q.get("contexts", []))
            dataset_data["ground_truth"].append(q.get("ground_truth", ""))
        
        return Dataset.from_dict(dataset_data)
    
    def _get_metrics(self) -> List:
        """Obtiene las métricas configuradas para la evaluación."""
        metrics = []
        metrics_config = self.config.get("metrics", {})
        
        if metrics_config.get("faithfulness", {}).get("enabled", False):
            metrics.append(faithfulness)
        
        if metrics_config.get("context_precision", {}).get("enabled", False):
            metrics.append(context_precision)
        
        if metrics_config.get("context_recall", {}).get("enabled", False):
            metrics.append(context_recall)
        
        if metrics_config.get("answer_relevancy", {}).get("enabled", False):
            metrics.append(answer_relevancy)
        
        if metrics_config.get("answer_correctness", {}).get("enabled", False):
            metrics.append(answer_correctness)
        
        if metrics_config.get("answer_similarity", {}).get("enabled", False):
            metrics.append(answer_similarity)
        
        return metrics
    
    def evaluate_configuration(self, config_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa una configuración específica.
        
        Args:
            config_name: Nombre de la configuración
            config: Parámetros de configuración
            
        Returns:
            Resultados de la evaluación
        """
        print(f"\n🔄 Evaluando configuración: {config_name}")
        print(f"📋 Parámetros: {config}")
        
        try:
            # Cargar preguntas de prueba
            questions = self._load_test_questions()
            if not questions:
                print("⚠️ No hay preguntas de prueba disponibles")
                return {}
            
            # Crear dataset para RAGAS
            dataset = self._create_test_dataset(questions)
            
            # Obtener métricas
            metrics = self._get_metrics()
            
            print(f"📊 Evaluando con {len(metrics)} métricas")
            print(f"📝 Dataset: {len(dataset)} ejemplos")
            
            # Ejecutar evaluación
            start_time = time.time()
            results = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self.generation_service.llm,
                embeddings=self.embedding_service.get_embeddings_model()
            )
            evaluation_time = time.time() - start_time
            
            # Procesar resultados
            evaluation_results = {
                "config_name": config_name,
                "config": config,
                "evaluation_time": evaluation_time,
                "total_samples": len(dataset),
                "metrics": {}
            }
            
            # Extraer métricas individuales
            for metric in metrics:
                metric_name = metric.__name__
                if metric_name in results:
                    evaluation_results["metrics"][metric_name] = float(results[metric_name])
            
            print(f"✅ Evaluación completada en {evaluation_time:.2f} segundos")
            return evaluation_results
            
        except Exception as e:
            print(f"❌ Error en evaluación: {str(e)}")
            return {
                "config_name": config_name,
                "config": config,
                "error": str(e),
                "metrics": {}
            }
    
    def run_comparative_evaluation(self) -> Dict[str, Any]:
        """Ejecuta la evaluación comparativa entre Semana 2 y Semana 3."""
        print("\n🚀 Iniciando evaluación comparativa Semana 2 vs Semana 3")
        
        results = {}
        comparisons = self.config.get("comparisons", {})
        
        # Evaluación Semana 2 (baseline)
        if comparisons.get("semana2_vs_semana3", {}).get("enabled", False):
            baseline_config = comparisons["semana2_vs_semana3"]["baseline"]["config"]
            baseline_results = self.evaluate_configuration("Semana 2", baseline_config)
            results["semana2"] = baseline_results
        
        # Evaluación Semana 3 (mejorada)
        if comparisons.get("semana2_vs_semana3", {}).get("enabled", False):
            improved_config = comparisons["semana2_vs_semana3"]["improved"]["config"]
            improved_results = self.evaluate_configuration("Semana 3", improved_config)
            results["semana3"] = improved_results
        
        # Evaluación de funcionalidades individuales
        if comparisons.get("individual_features", {}).get("enabled", False):
            individual_tests = comparisons["individual_features"]["tests"]
            for test in individual_tests:
                test_results = self.evaluate_configuration(test["name"], test["config"])
                results[test["name"]] = test_results
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Genera un reporte de los resultados."""
        report = []
        report.append("# Reporte de Evaluación RAGAS - Semana 3")
        report.append(f"📅 Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Resumen de configuraciones evaluadas
        report.append("## Configuraciones Evaluadas")
        for config_name, config_results in results.items():
            if "error" in config_results:
                report.append(f"- **{config_name}**: ❌ Error - {config_results['error']}")
            else:
                report.append(f"- **{config_name}**: ✅ Completada")
        report.append("")
        
        # Comparación de métricas
        report.append("## Comparación de Métricas")
        report.append("")
        
        # Crear tabla de métricas
        metrics_table = []
        metrics_table.append("| Configuración | Faithfulness | Context Precision | Context Recall | Answer Relevancy |")
        metrics_table.append("|---------------|--------------|-------------------|---------------|------------------|")
        
        for config_name, config_results in results.items():
            if "metrics" in config_results:
                metrics = config_results["metrics"]
                row = f"| {config_name} |"
                row += f" {metrics.get('faithfulness', 0):.3f} |"
                row += f" {metrics.get('context_precision', 0):.3f} |"
                row += f" {metrics.get('context_recall', 0):.3f} |"
                row += f" {metrics.get('answer_relevancy', 0):.3f} |"
                metrics_table.append(row)
        
        report.extend(metrics_table)
        report.append("")
        
        # Análisis de mejoras
        report.append("## Análisis de Mejoras")
        report.append("")
        
        if "semana2" in results and "semana3" in results:
            semana2_metrics = results["semana2"].get("metrics", {})
            semana3_metrics = results["semana3"].get("metrics", {})
            
            for metric_name in ["faithfulness", "context_precision", "context_recall", "answer_relevancy"]:
                if metric_name in semana2_metrics and metric_name in semana3_metrics:
                    improvement = semana3_metrics[metric_name] - semana2_metrics[metric_name]
                    if improvement > 0:
                        report.append(f"- **{metric_name}**: +{improvement:.3f} ✅ Mejora")
                    elif improvement < 0:
                        report.append(f"- **{metric_name}**: {improvement:.3f} ❌ Regresión")
                    else:
                        report.append(f"- **{metric_name}**: Sin cambio")
        
        report.append("")
        
        # Recomendaciones
        report.append("## Recomendaciones")
        report.append("")
        report.append("1. **Preprocesamiento**: Evalúa si el uso de markitdown mejora la calidad de los fragmentos")
        report.append("2. **Reranking**: Verifica si el reranking mejora la relevancia de los documentos recuperados")
        report.append("3. **Query Rewriting**: Analiza si la reescritura de consultas mejora la recuperación")
        report.append("4. **Métricas preocupantes**: Revisa métricas por debajo de los umbrales configurados")
        
        return "\n".join(report)
    
    def save_results(self, results: Dict[str, Any], output_dir: str = "tests/semana3/results"):
        """Guarda los resultados en archivos."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Guardar resultados JSON
        results_file = output_path / "evaluation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Generar y guardar reporte
        report = self.generate_report(results)
        report_file = output_path / "evaluation_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📁 Resultados guardados en: {output_path}")
        print(f"📄 Reporte: {report_file}")
        print(f"📊 Datos: {results_file}")


def main():
    """Función principal para ejecutar la evaluación."""
    print("🚀 Iniciando evaluación RAGAS para Semana 3")
    
    # Crear evaluador
    evaluator = Semana3RagasEvaluator()
    
    # Ejecutar evaluación comparativa
    results = evaluator.run_comparative_evaluation()
    
    # Generar reporte
    report = evaluator.generate_report(results)
    print("\n" + "="*50)
    print(report)
    print("="*50)
    
    # Guardar resultados
    evaluator.save_results(results)
    
    print("\n✅ Evaluación completada")


if __name__ == "__main__":
    main()
