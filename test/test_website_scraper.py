"""
tests/test_website_scraper.py - Tests del scraper de sitios web
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch, MagicMock
from analyzer.website_scraper import scrape_website, _parse_html


SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <title>Ferretería San José - Herramientas y Materiales</title>
  <meta name="description" content="La mejor ferretería de Santiago con más de 30 años de experiencia.">
</head>
<body>
  <h1>Ferretería San José</h1>
  <h2>Nuestros Productos</h2>
  <h2>Trabaja con Nosotros</h2>
  <p>Contáctanos en info@ferreteriasjose.cl o llamanos al +56 2 2345 6789</p>
  <p>Síguenos en redes sociales</p>
  <a href="https://facebook.com/ferreteriasjose">Facebook</a>
  <a href="https://instagram.com/ferreteriasjose">Instagram</a>
  <p>Nuestras sucursales en Santiago, Maipú y Puente Alto</p>
  <footer>© Copyright 2024 Ferretería San José</footer>
</body>
</html>
"""


class TestParseHtml:
    def test_extracts_title(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert "Ferretería San José" in data.title

    def test_extracts_meta_description(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert "ferretería" in data.meta_description.lower()

    def test_extracts_h1(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert "Ferretería San José" in data.h1

    def test_extracts_h2_list(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert len(data.h2_list) == 2
        assert "Nuestros Productos" in data.h2_list

    def test_extracts_emails(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert "info@ferreteriasjose.cl" in data.emails

    def test_extracts_phones(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert len(data.phones) >= 1

    def test_extracts_social_links(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert "facebook" in data.social_links
        assert "instagram" in data.social_links

    def test_extracts_copyright_year(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert data.copyright_year == "2024"

    def test_scrape_ok_true(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert data.scrape_ok is True

    def test_raw_text_snippet_not_empty(self):
        data = _parse_html("https://example.cl", SAMPLE_HTML)
        assert len(data.raw_text_snippet) > 10


class TestScrapeWebsite:
    def test_empty_url_returns_error(self):
        data = scrape_website("")
        assert data.scrape_ok is False

    def test_returns_websitedata_object(self):
        with patch("analyzer.website_scraper._download_html", return_value=SAMPLE_HTML):
            data = scrape_website("https://ferreteriasjose.cl")
            assert data.scrape_ok is True
            assert data.title != ""

    def test_failed_download_returns_error_state(self):
        with patch("analyzer.website_scraper._download_html", return_value=None):
            data = scrape_website("https://sitioquenoexiste123456.cl")
            assert data.scrape_ok is False
            assert data.scrape_error != ""
