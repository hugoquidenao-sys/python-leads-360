"""
utils/logger.py - Configuración de Loguru para Python Leads 360
"""
import sys
from pathlib import Path
from loguru import logger

LOG_DIR = Path(__file__).parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Eliminar handler por defecto
logger.remove()

# Consola: solo INFO y superiores, formato limpio
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    colorize=True,
)

# Archivo: DEBUG completo con rotación
logger.add(
    LOG_DIR / "leads360_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    rotation="1 day",
    retention="7 days",
    encoding="utf-8",
)

__all__ = ["logger"]
