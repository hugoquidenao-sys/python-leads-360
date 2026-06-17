"""
tests/test_signal_detector.py - Tests del detector de señales
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.signal_detector import detect_signals


def _base_data(**kwargs):
    defaults = {
        "raw_text_snippet": "",
        "emails": [],
        "social_links": {},
        "copyright_year": "",
        "title": "",
        "url": "https://example.cl",
        "scrape_ok": True,
        "scrape_error": "",
    }
    defaults.update(kwargs)
    return defaults


class TestSignalDetector:
    def test_active_site_signal(self):
        signals = detect_signals(_base_data(), [])
        names = [s["signal"] for s in signals]
        assert "Sitio web activo" in names

    def test_inactive_site_signal(self):
        data = _base_data(scrape_ok=False, scrape_error="404", url="")
        signals = detect_signals(data, [])
        names = [s["signal"] for s in signals]
        assert "Sin sitio web o inaccesible" in names

    def test_corporate_email_detected(self):
        data = _base_data(emails=["contacto@empresa.cl"])
        signals = detect_signals(data, [])
        names = [s["signal"] for s in signals]
        assert "Correo corporativo" in names

    def test_personal_email_detected(self):
        data = _base_data(emails=["empresa@gmail.com"])
        signals = detect_signals(data, [])
        names = [s["signal"] for s in signals]
        assert "Solo correo personal (no corporativo)" in names

    def test_multiple_socials_detected(self):
        socials = {
            "facebook": "https://fb.com/empresa",
            "instagram": "https://ig.com/empresa",
            "linkedin": "https://linkedin.com/empresa",
        }
        data = _base_data(social_links=socials)
        signals = detect_signals(data, [])
        names = [s["signal"] for s in signals]
        assert "Redes sociales activas (múltiples)" in names

    def test_job_vacancy_signal(self):
        data = _base_data(raw_text_snippet="Trabaja con nosotros - Postula aquí")
        signals = detect_signals(data, [])
        names = [s["signal"] for s in signals]
        assert "Publicación de vacantes o empleos" in names

    def test_branch_signal(self):
        data = _base_data(raw_text_snippet="Encuéntranos en nuestras sucursales en todo Chile")
        signals = detect_signals(data, [])
        names = [s["signal"] for s in signals]
        assert "Múltiples sucursales o puntos de venta" in names

    def test_ecommerce_signal_from_tech(self):
        signals = detect_signals(_base_data(), ["WooCommerce"])
        names = [s["signal"] for s in signals]
        assert "Plataforma ecommerce activa" in names

    def test_outdated_site_signal(self):
        data = _base_data(copyright_year="2019")
        signals = detect_signals(data, [])
        names = [s["signal"] for s in signals]
        assert "Sitio web desactualizado" in names

    def test_all_signals_have_required_fields(self):
        data = _base_data(
            emails=["empresa@example.cl"],
            raw_text_snippet="vacantes disponibles",
            social_links={"facebook": "https://fb.com/empresa"},
        )
        signals = detect_signals(data, ["WordPress", "Google Analytics"])
        for s in signals:
            assert "signal" in s
            assert "score" in s
            assert "evidence" in s
            assert isinstance(s["score"], int)
