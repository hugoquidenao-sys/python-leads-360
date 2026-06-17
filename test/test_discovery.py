"""
tests/test_discovery.py - Tests del módulo de descubrimiento de empresas
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch
from discovery.google_maps import search_companies, _mock_companies


class TestDiscovery:
    def test_mock_companies_returns_list(self):
        """Sin API key debe retornar lista de empresas de ejemplo."""
        with patch("discovery.google_maps.GOOGLE_MAPS_API_KEY", ""):
            companies = search_companies("ferretería", "Santiago")
        assert isinstance(companies, list)
        assert len(companies) > 0

    def test_mock_companies_have_required_fields(self):
        companies = _mock_companies("ferretería", "Santiago")
        required = {"name", "website", "phone", "address", "category", "city", "keyword"}
        for c in companies:
            missing = required - set(c.keys())
            assert not missing, f"Campos faltantes: {missing}"

    def test_mock_companies_include_keyword_and_city(self):
        companies = _mock_companies("restaurante", "Valparaíso")
        for c in companies:
            assert c["keyword"] == "restaurante"
            assert c["city"] == "Valparaíso"

    def test_deduplication_in_mock(self):
        """No debe haber duplicados por nombre en la misma búsqueda."""
        companies = _mock_companies("tienda", "Concepción")
        names = [c["name"] for c in companies]
        assert len(names) == len(set(names)), "Hay empresas duplicadas"

    def test_search_returns_list_without_api_key(self):
        with patch("discovery.google_maps.GOOGLE_MAPS_API_KEY", ""):
            result = search_companies("contabilidad", "Santiago")
        assert isinstance(result, list)
        assert len(result) > 0
