"""
tests/test_scoring.py - Tests del motor de scoring
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scoring.scoring_engine import calculate_score, _classify


class TestClassify:
    def test_hot_threshold(self):
        assert _classify(65) == "HOT"
        assert _classify(100) == "HOT"
        assert _classify(80) == "HOT"

    def test_warm_threshold(self):
        assert _classify(35) == "WARM"
        assert _classify(50) == "WARM"
        assert _classify(64) == "WARM"

    def test_cold_threshold(self):
        assert _classify(0) == "COLD"
        assert _classify(20) == "COLD"
        assert _classify(34) == "COLD"


class TestCalculateScore:
    def test_empty_inputs(self):
        score, cls = calculate_score([], [], [])
        assert score == 0
        assert cls == "COLD"

    def test_high_score_with_many_signals(self):
        signals = [
            {"signal": "Sitio web activo", "score": 10, "evidence": ""},
            {"signal": "Correo corporativo", "score": 15, "evidence": ""},
            {"signal": "Plataforma ecommerce activa", "score": 18, "evidence": ""},
            {"signal": "Múltiples sucursales o puntos de venta", "score": 15, "evidence": ""},
            {"signal": "Publicación de vacantes o empleos", "score": 12, "evidence": ""},
            {"signal": "Señales de crecimiento", "score": 12, "evidence": ""},
        ]
        pains = [
            {"pain": "IVA", "severity": "high"},
            {"pain": "remuneraciones", "severity": "high"},
            {"pain": "outsourcing", "severity": "medium"},
        ]
        technologies = ["WooCommerce", "Google Analytics"]
        score, cls = calculate_score(signals, pains, technologies)
        assert score > 60
        assert cls == "HOT"

    def test_negative_signals_reduce_score(self):
        signals = [
            {"signal": "Sin sitio web o inaccesible", "score": -5, "evidence": ""},
            {"signal": "Solo correo personal (no corporativo)", "score": 5, "evidence": ""},
            {"signal": "Sitio web desactualizado", "score": -5, "evidence": ""},
        ]
        score, _ = calculate_score(signals, [], [])
        assert score < 20

    def test_score_capped_at_100(self):
        # Escenario maximalista
        signals = [{"signal": f"señal_{i}", "score": 20, "evidence": ""} for i in range(20)]
        pains   = [{"pain": f"dolor_{i}", "severity": "high"} for i in range(20)]
        techs   = ["WooCommerce", "Shopify", "HubSpot"]
        score, _ = calculate_score(signals, pains, techs)
        assert score <= 100

    def test_score_never_negative(self):
        signals = [
            {"signal": "Sin sitio web o inaccesible", "score": -50, "evidence": ""},
            {"signal": "Sitio web desactualizado", "score": -50, "evidence": ""},
        ]
        score, _ = calculate_score(signals, [], [])
        assert score >= 0
