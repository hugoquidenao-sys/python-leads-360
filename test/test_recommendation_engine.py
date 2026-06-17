"""
tests/test_recommendation_engine.py - Tests del motor de recomendaciones
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from recommendations.recommendation_engine import generate_recommendations
from config import AVAILABLE_SERVICES


class TestRecommendationEngine:
    def test_returns_list(self):
        recs = generate_recommendations([], [], 50)
        assert isinstance(recs, list)

    def test_no_empty_result(self):
        recs = generate_recommendations([], [], 0)
        assert len(recs) >= 1

    def test_ecommerce_pain_recommends_taxation(self):
        pains = [{"pain": "Gestión compleja de IVA en ventas online", "severity": "high", "evidence": ""}]
        recs = generate_recommendations(pains, [], 70)
        services = [r["service"] for r in recs]
        assert "Tributación" in services

    def test_hiring_pain_recommends_remuneraciones(self):
        pains = [{"pain": "Gestión de remuneraciones y contratos en crecimiento", "severity": "high", "evidence": ""}]
        recs = generate_recommendations(pains, [], 60)
        services = [r["service"] for r in recs]
        assert "Remuneraciones" in services

    def test_outsourcing_signal_recommends_outsourcing(self):
        signals = [{"signal": "Múltiples sucursales o puntos de venta", "score": 15, "evidence": ""}]
        recs = generate_recommendations([], signals, 75)
        services = [r["service"] for r in recs]
        assert "Outsourcing contable" in services

    def test_all_recommended_services_are_valid(self):
        pains = [
            {"pain": "Gestión compleja de IVA en ventas online", "severity": "high", "evidence": ""},
            {"pain": "Gestión de remuneraciones y contratos en crecimiento", "severity": "high", "evidence": ""},
        ]
        recs = generate_recommendations(pains, [], 80)
        for r in recs:
            assert r["service"] in AVAILABLE_SERVICES, f"Servicio inválido: {r['service']}"

    def test_recommendations_have_required_fields(self):
        recs = generate_recommendations(
            [{"pain": "Obligaciones tributarias recurrentes", "severity": "medium", "evidence": ""}],
            [], 40
        )
        for r in recs:
            assert "service" in r
            assert "priority" in r
            assert "rationale" in r

    def test_priority_is_positive_integer(self):
        recs = generate_recommendations(
            [{"pain": "Necesidad de remuneraciones", "severity": "high", "evidence": ""}],
            [], 60
        )
        for r in recs:
            assert isinstance(r["priority"], int)
            assert r["priority"] >= 1
