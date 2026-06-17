"""
discovery/google_maps.py - Descubrimiento de empresas vía Google Maps Places API

Estrategia:
  1. Llama a la Places API (Text Search) con keyword + city.
  2. Desduplicar por nombre + ciudad.
  3. Persistir en SQLite y retornar lista normalizada.

Nota: Si no hay API key, usa un mock para desarrollo local.
"""
import time
import requests

from config import GOOGLE_MAPS_API_KEY, MAX_COMPANIES_PER_SEARCH, DEFAULT_HEADERS, SCRAPING_DELAY
from utils.logger import logger
from utils.helpers import clean_text, normalize_url
from database.sqlite_manager import upsert_company


PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


def search_companies(keyword: str, city: str) -> list[dict]:
    """
    Busca empresas en Google Maps y las persiste en SQLite.

    Args:
        keyword: Rubro o tipo de empresa. Ej: "ferretería"
        city:    Ciudad. Ej: "Santiago"

    Returns:
        Lista de dicts con name, website, phone, address, category
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY no configurada — usando datos de ejemplo")
        return _mock_companies(keyword, city)

    logger.info(f"Buscando '{keyword}' en '{city}' vía Google Maps…")
    results = _fetch_places(keyword, city)
    companies = _normalize_results(results, keyword, city)
    _persist(companies, keyword, city)

    logger.info(f"✓ {len(companies)} empresas encontradas y guardadas")
    return companies


# ── Fetching ────────────────────────────────────────────────────────────────────

def _fetch_places(keyword: str, city: str) -> list[dict]:
    """Llama a la Places Text Search API con paginación."""
    query   = f"{keyword} en {city}"
    params  = {"query": query, "key": GOOGLE_MAPS_API_KEY, "language": "es"}
    raw: list[dict] = []

    for page in range(3):  # máximo 3 páginas (60 resultados)
        try:
            resp = requests.get(PLACES_URL, params=params, timeout=15, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.error(f"Places API error: {data.get('status')} — {data.get('error_message', '')}")
                break

            raw.extend(data.get("results", []))
            logger.debug(f"  Página {page+1}: {len(data.get('results', []))} resultados")

            if len(raw) >= MAX_COMPANIES_PER_SEARCH:
                break

            next_token = data.get("next_page_token")
            if not next_token:
                break

            # Google exige esperar ~2s antes de usar next_page_token
            time.sleep(2)
            params = {"pagetoken": next_token, "key": GOOGLE_MAPS_API_KEY}

        except requests.RequestException as e:
            logger.error(f"Error HTTP en Places API: {e}")
            break

    return raw[:MAX_COMPANIES_PER_SEARCH]


def _normalize_results(raw: list[dict], keyword: str, city: str) -> list[dict]:
    """Convierte resultados de la API al formato interno."""
    seen: set[str] = set()
    companies: list[dict] = []

    for place in raw:
        name = clean_text(place.get("name", ""))
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())

        address = clean_text(
            place.get("formatted_address", "")
            or place.get("vicinity", "")
        )
        category = ", ".join(place.get("types", [])[:3]).replace("_", " ")

        # website y phone requieren Place Details (llamada adicional)
        website, phone = _fetch_details(place.get("place_id", ""))

        companies.append({
            "name":     name,
            "website":  website,
            "phone":    phone,
            "address":  address,
            "category": category,
            "city":     city,
            "keyword":  keyword,
        })

    return companies


def _fetch_details(place_id: str) -> tuple[str, str]:
    """Obtiene website y teléfono desde Place Details."""
    if not place_id:
        return "", ""
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "website,formatted_phone_number",
            "key": GOOGLE_MAPS_API_KEY,
            "language": "es",
        }
        resp = requests.get(url, params=params, timeout=10)
        result = resp.json().get("result", {})
        website = normalize_url(result.get("website", ""))
        phone   = result.get("formatted_phone_number", "")
        time.sleep(SCRAPING_DELAY * 0.5)
        return website, phone
    except Exception as e:
        logger.debug(f"Place Details error ({place_id}): {e}")
        return "", ""


# ── Persistencia ────────────────────────────────────────────────────────────────

def _persist(companies: list[dict], keyword: str, city: str) -> None:
    """Guarda las empresas en SQLite."""
    for c in companies:
        try:
            cid = upsert_company(c)
            logger.debug(f"  Empresa guardada id={cid}: {c['name']}")
        except Exception as e:
            logger.warning(f"No se pudo guardar '{c['name']}': {e}")


# ── Mock para desarrollo sin API key ────────────────────────────────────────────

def _mock_companies(keyword: str, city: str) -> list[dict]:
    """Retorna empresas de ejemplo para desarrollo local."""
    mock = [
        {
            "name": f"Comercial {keyword.title()} Ltda.",
            "website": "https://www.ejemplo-comercial.cl",
            "phone": "+56 2 2345 6789",
            "address": f"Av. Providencia 1234, {city}",
            "category": "empresa, comercio",
            "city": city,
            "keyword": keyword,
        },
        {
            "name": f"Importadora {keyword.title()} SpA",
            "website": "https://www.importadora-ejemplo.cl",
            "phone": "+56 9 8765 4321",
            "address": f"Calle Los Leones 567, {city}",
            "category": "importadora, distribuidora",
            "city": city,
            "keyword": keyword,
        },
        {
            "name": f"Distribuidora {keyword.title()} S.A.",
            "website": "https://www.distribuidora-ejemplo.cl",
            "phone": "+56 2 2987 6543",
            "address": f"Gran Avenida 890, {city}",
            "category": "distribuidora, mayorista",
            "city": city,
            "keyword": keyword,
        },
        {
            "name": f"Servicios {keyword.title()} Eirl",
            "website": "",
            "phone": "+56 9 1234 5678",
            "address": f"Maipú 321, {city}",
            "category": "servicios",
            "city": city,
            "keyword": keyword,
        },
    ]
    _persist(mock, keyword, city)
    return mock
