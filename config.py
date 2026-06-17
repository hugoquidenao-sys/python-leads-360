"""
config.py - Configuración central de Python Leads 360
Carga variables de entorno y define constantes del sistema.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
OUTPUT_DIR  = BASE_DIR / Path(os.getenv("OUTPUT_DIR", "outputs"))

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Base de datos ───────────────────────────────────────────────────────────────
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/leads360.db")

# ── APIs ────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENAI_MODEL        = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── Scraping ────────────────────────────────────────────────────────────────────
SCRAPING_TIMEOUT    = int(os.getenv("SCRAPING_TIMEOUT", 15))
SCRAPING_MAX_RETRIES = int(os.getenv("SCRAPING_MAX_RETRIES", 3))
SCRAPING_DELAY      = float(os.getenv("SCRAPING_DELAY", 1.5))

# ── Búsqueda ────────────────────────────────────────────────────────────────────
MAX_COMPANIES_PER_SEARCH = int(os.getenv("MAX_COMPANIES_PER_SEARCH", 20))

# ── Scoring ─────────────────────────────────────────────────────────────────────
SCORE_HOT_THRESHOLD  = 65
SCORE_WARM_THRESHOLD = 35

# ── Servicios disponibles ───────────────────────────────────────────────────────
AVAILABLE_SERVICES = [
    "Contabilidad mensual",
    "Remuneraciones",
    "Tributación",
    "Outsourcing contable",
    "Constitución de empresas",
    "Gestión administrativa",
]

# ── Headers HTTP ────────────────────────────────────────────────────────────────
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
