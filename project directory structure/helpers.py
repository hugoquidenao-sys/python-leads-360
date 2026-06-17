"""
utils/helpers.py - Funciones de utilidad general
"""
import re
import time
import unicodedata
from urllib.parse import urlparse, urljoin


def clean_text(text: str) -> str:
    """Limpia y normaliza texto."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_emails(text: str) -> list[str]:
    """Extrae correos electrónicos de un texto."""
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    emails = re.findall(pattern, text)
    # Filtrar dominios de imagen comunes (falsos positivos)
    blacklist = {".png", ".jpg", ".gif", ".svg", ".webp"}
    return list({
        e.lower() for e in emails
        if not any(e.lower().endswith(b) for b in blacklist)
    })


def extract_phones(text: str) -> list[str]:
    """Extrae teléfonos chilenos y genéricos."""
    patterns = [
        r"\+56\s?[29]\s?\d{4}\s?\d{4}",      # +56 9 XXXX XXXX
        r"\(?\d{2}\)?\s?\d{4}[\s\-]?\d{4}",  # (XX) XXXX XXXX
        r"\+\d{1,3}[\s\-]?\d{7,12}",          # Internacional genérico
    ]
    phones = []
    for p in patterns:
        phones.extend(re.findall(p, text))
    return list(set(phones))


def normalize_url(url: str) -> str:
    """Asegura que la URL tenga esquema http/https."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def get_domain(url: str) -> str:
    """Extrae el dominio de una URL."""
    try:
        return urlparse(normalize_url(url)).netloc.lower()
    except Exception:
        return ""


def safe_sleep(seconds: float) -> None:
    """Sleep con manejo de interrupciones."""
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        pass


def truncate(text: str, max_len: int = 200) -> str:
    """Trunca texto con ellipsis si supera el máximo."""
    if not text or len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"
