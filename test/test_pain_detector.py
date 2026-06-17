"""
tests/test_pain_detector.py - Tests del detector de dolores
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.pain_detector import detect_pains


class TestPainDetector:
    def _base_website(self, text="", emails=None):
        return {
            "raw_text_snippet": text,
            "emails": emails or [],
            "scrape_ok": True,
            "url": "https://example.cl",
            "title": "",
        }

    def test_ecommerce_generates_iva_pain(self):
        pains = detect_pains(
            self._base_website(),
            technologies=["WooCommerce"],
            signals=[],
        )
        pain_names = [p["pain"] for p in pains]
        assert any("IVA" in p for p in pain_names)

    def test_ecommerce_generates_conciliation_pain(self):
        pains = detect_pains(
            self._base_website(),
            technologies=["Shopify"],
            signals=[],
        )
        pain_names = [p["pain"] for p in pains]
        assert any("conciliación" in p.lower() for p in pain_names)

    def test_job_vacancies_generate_remunerations_pain(self):
        signals = [{"signal": "Publicación de vacantes o empleos", "score": 12, "evidence": ""}]
        pains = detect_pains(self._base_website(), technologies=[], signals=signals)
        pain_names = [p["pain"] for p in pains]
        assert any("remuneraciones" in p.lower() or "laboral" in p.lower() for p in pain_names)

    def test_multiple_branches_generate_outsourcing_pain(self):
        signals = [{"signal": "Múltiples sucursales o puntos de venta", "score": 15, "evidence": ""}]
        pains = detect_pains(self._base_website(), technologies=[], signals=signals)
        pain_names = [p["pain"] for p in pains]
        assert any("outsourcing" in p.lower() or "multilocal" in p.lower() for p in pain_names)

    def test_personal_email_generates_informality_pain(self):
        signals = [{"signal": "Solo correo personal (no corporativo)", "score": 5, "evidence": ""}]
        pains = detect_pains(
            self._base_website(emails=["empresa@gmail.com"]),
            technologies=[],
            signals=signals,
        )
        pain_names = [p["pain"] for p in pains]
        assert any("informal" in p.lower() or "formaliz" in p.lower() for p in pain_names)

    def test_no_signals_returns_at_least_one_pain(self):
        pains = detect_pains(self._base_website(), technologies=[], signals=[])
        assert len(pains) >= 1

    def test_severity_values_are_valid(self):
        pains = detect_pains(
            self._base_website(),
            technologies=["WooCommerce"],
            signals=[{"signal": "Publicación de vacantes o empleos", "score": 12, "evidence": ""}],
        )
        valid = {"low", "medium", "high"}
        for p in pains:
            assert p["severity"] in valid, f"Severidad inválida: {p['severity']}"
