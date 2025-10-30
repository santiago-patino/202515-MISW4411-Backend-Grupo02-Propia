"""
Pruebas para la reescritura de consultas - Semana 3
====================================================

Este módulo contiene las pruebas para verificar que la reescritura
de consultas funciona correctamente.
"""

import pytest
from app.services.generation_service import GenerationService


class TestQueryRewriting:
    """Pruebas para la reescritura de consultas."""
    
    def test_query_rewriting_basic(self):
        """Prueba básica de reescritura de consultas."""
        generation_service = GenerationService(use_local=True)
        
        original_query = "¿Qué son las convocatorias?"
        rewritten_query = generation_service.rewrite_query(original_query)
        
        # Verificar que se retorna una consulta
        assert rewritten_query is not None
        assert isinstance(rewritten_query, str)
        assert len(rewritten_query) > 0
    
    def test_query_rewriting_expansion(self):
        """Prueba la expansión de consultas con términos relacionados."""
        generation_service = GenerationService(use_local=True)
        
        # Consulta que debería expandirse
        original_query = "convocatoria investigación"
        rewritten_query = generation_service.rewrite_query(original_query)
        
        # Verificar que la consulta expandida contiene términos relacionados
        assert "convocatoria" in rewritten_query.lower()
        # Debería incluir términos expandidos
        assert len(rewritten_query) >= len(original_query)
    
    def test_query_rewriting_empty_query(self):
        """Prueba reescritura con consulta vacía."""
        generation_service = GenerationService(use_local=True)
        
        rewritten_query = generation_service.rewrite_query("")
        
        # Debe retornar la consulta original (vacía)
        assert rewritten_query == ""
    
    def test_query_rewriting_no_expansion(self):
        """Prueba reescritura cuando no hay términos para expandir."""
        generation_service = GenerationService(use_local=True)
        
        # Consulta que no debería expandirse
        original_query = "consulta muy específica sin términos clave"
        rewritten_query = generation_service.rewrite_query(original_query)
        
        # Debe retornar la consulta original
        assert rewritten_query == original_query
    
    def test_query_rewriting_local_fallback(self):
        """Prueba el fallback local para reescritura."""
        generation_service = GenerationService(use_local=True)
        
        # Probar con diferentes tipos de consultas
        test_queries = [
            "convocatoria",
            "proyecto investigación",
            "financiación desarrollo",
            "requisitos participación"
        ]
        
        for query in test_queries:
            rewritten = generation_service.rewrite_query(query)
            assert rewritten is not None
            assert isinstance(rewritten, str)
    
    def test_query_rewriting_error_handling(self):
        """Prueba el manejo de errores en reescritura."""
        generation_service = GenerationService(use_local=True)
        
        # Consulta con caracteres especiales
        special_query = "¿Qué son las convocatorias? ¡Importante!"
        rewritten_query = generation_service.rewrite_query(special_query)
        
        # Debe manejar caracteres especiales sin errores
        assert rewritten_query is not None
        assert isinstance(rewritten_query, str)
    
    def test_query_rewriting_consistency(self):
        """Prueba la consistencia de la reescritura."""
        generation_service = GenerationService(use_local=True)
        
        query = "convocatoria investigación"
        
        # Ejecutar múltiples veces
        results = []
        for _ in range(3):
            rewritten = generation_service.rewrite_query(query)
            results.append(rewritten)
        
        # Los resultados deben ser consistentes
        assert all(result == results[0] for result in results)
    
    def test_query_rewriting_long_query(self):
        """Prueba reescritura con consultas largas."""
        generation_service = GenerationService(use_local=True)
        
        long_query = "¿Cuáles son los requisitos y condiciones para participar en las convocatorias de investigación y desarrollo tecnológico en el área de ciencias de la computación?"
        rewritten_query = generation_service.rewrite_query(long_query)
        
        # Debe manejar consultas largas
        assert rewritten_query is not None
        assert isinstance(rewritten_query, str)
        assert len(rewritten_query) > 0