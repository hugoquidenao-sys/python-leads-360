"""
analyzer/website_scraper.py - Scraper de sitios web empresariales

Extrae:
  - title, meta description, h1, h2[]
  - correos y teléfonos
  - redes sociales
  - año de copyright
  - texto principal (para IA)

Estrategia:
  1. requests con User-Agent realista (rápido, 90% de casos)
  2. Playwright como fallback para sitios JS-rendered
"""
import re
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import SCRAPING_TIMEOUT, SCRAPING_MAX_RETRIES, SCRAPING_DELAY, DEFAULT_HEADERS
from utils.logger import logger
from utils.helpers import clean_text, extract_emails, extract_phones, normalize_url


# ── Modelo de datos ──────────────────────────────────────────────────────────────

@dataclass
class WebsiteData:
    url:              str = ""
    title:            str = ""
    meta_description: str = ""
    h1:               str = ""
    h2_list:          list[str] = field(default_factory=list)
    emails:           list[str] = field(default_factory=list)
    phones:           list[str] = field(default_factory=list)
    social_links:     dict[str, str] = field(default_factory=dict)
    copyright_year:   str = ""
    technologies:     list[str] = field(default_factory=list)
    raw_text_snippet: str = ""
    scrape_ok:        bool = True
    scrape_error:     str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


# ── Scraper principal ────────────────────────────────────────────────────────────

def scrape_website(url: str) -> WebsiteData:
    """
    Descarga y analiza un sitio web.

    Args:
        url: URL del sitio a analizar

    Returns:
        WebsiteData con toda la información extraída
    """
    url = normalize_url(url)
    if not url:
        return WebsiteData(scrape_ok=False, scrape_error="URL vacía")

    logger.debug(f"  Scraping: {url}")

    html = _download_html(url)
    if html is None:
        return WebsiteData(url=url, scrape_ok=False, scrape_error="No se pudo descargar el sitio")

    return _parse_html(url, html)


# ── Descarga ─────────────────────────────────────────────────────────────────────

def _download_html(url: str) -> str | None:
    """Intenta descargar HTML con requests; fallback a Playwright si falla."""
    html = _requests_download(url)
    if html and len(html) > 500:
        return html

    # Fallback: Playwright para sitios JavaScript-heavy
    logger.debug(f"  Requests falló o HTML muy corto, intentando Playwright…")
    return _playwright_download(url)


def _requests_download(url: str) -> str | None:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    for attempt in range(SCRAPING_MAX_RETRIES):
        try:
            resp = session.get(
                url,
                timeout=SCRAPING_TIMEOUT,
                allow_redirects=True,
                verify=False,   # algunos sitios tienen cert caducado
            )
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text

        except requests.exceptions.SSLError:
            logger.debug(f"  SSL error, reintentando con http://")
            url = url.replace("https://", "http://")
        except requests.exceptions.Timeout:
            logger.debug(f"  Timeout en intento {attempt+1}")
            time.sleep(SCRAPING_DELAY)
        except requests.RequestException as e:
            logger.debug(f"  Request error: {e}")
            if attempt < SCRAPING_MAX_RETRIES - 1:
                time.sleep(SCRAPING_DELAY)

    return None


def _playwright_download(url: str) -> str | None:
    """Usa Playwright para sitios JS-rendered. Requiere: playwright install chromium"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=DEFAULT_HEADERS["User-Agent"],
                extra_http_headers={"Accept-Language": "es-CL,es;q=0.9"},
            )
            page.goto(url, timeout=SCRAPING_TIMEOUT * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.debug(f"  Playwright error: {e}")
        return None


# ── Parsing ──────────────────────────────────────────────────────────────────────

def _parse_html(url: str, html: str) -> WebsiteData:
    """Extrae todos los campos relevantes del HTML."""
    soup = BeautifulSoup(html, "lxml")

    # Remover scripts y estilos para el texto limpio
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    full_text = clean_text(soup.get_text(separator=" "))

    data = WebsiteData(url=url)
    data.title            = _get_title(soup)
    data.meta_description = _get_meta(soup)
    data.h1               = _get_h1(soup)
    data.h2_list          = _get_h2(soup)
    data.emails           = extract_emails(html + full_text)
    data.phones           = extract_phones(full_text)
    data.social_links     = _get_social_links(soup, url)
    data.copyright_year   = _get_copyright_year(full_text)
    data.raw_text_snippet = full_text[:3000]

    return data


def _get_title(soup: BeautifulSoup) -> str:
    tag = soup.find("title")
    return clean_text(tag.get_text()) if tag else ""


def _get_meta(soup: BeautifulSoup) -> str:
    tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if tag and tag.get("content"):
        return clean_text(tag["content"])
    # Open Graph fallback
    tag = soup.find("meta", attrs={"property": "og:description"})
    if tag and tag.get("content"):
        return clean_text(tag["content"])
    return ""


def _get_h1(soup: BeautifulSoup) -> str:
    tag = soup.find("h1")
    return clean_text(tag.get_text()) if tag else ""


def _get_h2(soup: BeautifulSoup, max_items: int = 8) -> list[str]:
    return [
        clean_text(h.get_text())
        for h in soup.find_all("h2")[:max_items]
        if h.get_text(strip=True)
    ]


def _get_social_links(soup: BeautifulSoup, base_url: str) -> dict[str, str]:
    """Extrae enlaces a redes sociales."""
    social_patterns = {
        "facebook":  r"facebook\.com/",
        "instagram": r"instagram\.com/",
        "twitter":   r"twitter\.com/|x\.com/",
        "linkedin":  r"linkedin\.com/",
        "youtube":   r"youtube\.com/",
        "tiktok":    r"tiktok\.com/",
    }
    found: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        for network, pattern in social_patterns.items():
            if network not in found and re.search(pattern, href, re.I):
                found[network] = href if href.startswith("http") else urljoin(base_url, href)
    return found


def _get_copyright_year(text: str) -> str:
    """Extrae el año de copyright más reciente mencionado."""
    matches = re.findall(r"(?:©|copyright|copy|\(c\))\s*(\d{4})", text, re.I)
    if matches:
        return max(matches)
    # Buscar años sueltos al final del texto
    years = re.findall(r"\b(20[012]\d)\b", text[-500:])
    return max(years) if years else ""
