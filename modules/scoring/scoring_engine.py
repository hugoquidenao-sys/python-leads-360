"""
scoring/scoring_engine.py - Motor de scoring de leads (0 a 100)

Algoritmo puramente basado en reglas (sin IA):
  1. Suma puntos de señales detectadas (con tope).
  2. Bonus por dolores de alta severidad.
  3. Bonus por tecnologías de valor.
  4. Penalizaciones por indicadores negativos.
  5. Clasifica: COLD / WARM / HOT.

No modifica las señales ni dolores; solo los agrega.
"""
from config import SCORE_HOT_THRESHOLD, SCORE_WARM_THRESHOLD
from utils.logger import logger


# ── Constantes ───────────────────────────────────────────────────────────────────

SEVERITY_BONUS = {"high": 8, "medium": 4, "low": 1}
TECH_BONUS = {
    "WooCommerce":  12,
    "Shopify":      12,
    "Tiendanube":   10,
    "Jumpseller":   10,
    "Prestashop":    8,
    "HubSpot":       6,
}
NEGATIVE_SIGNALS = {
    "Sin sitio web o inaccesible": -10,
    "Solo correo personal (no corporativo)": -5,
    "Sitio web desactualizado": -5,
}

MAX_SIGNAL_SCORE    = 60   # tope de puntos por señales
MAX_PAIN_BONUS      = 25   # tope de bonus por dolores
MAX_TECH_BONUS      = 15   # tope de bonus por tecnologías


# ── Motor principal ──────────────────────────────────────────────────────────────

def calculate_score(
    signals:    list[dict],
    pain_points: list[dict],
    technologies: list[str],
) -> tuple[int, str]:
    """
    Calcula el score de oportunidad de una empresa.

    Args:
        signals:      lista de dicts {signal, score, evidence}
        pain_points:  lista de dicts {pain, severity, evidence}
        technologies: lista de nombres de tecnologías

    Returns:
        Tupla (score: int 0-100, classification: str COLD|WARM|HOT)
    """
    signal_total = 0
    pain_bonus   = 0
    tech_bonus   = 0

    # ── 1. Puntos por señales (positivos y negativos) ─────────────────────────
    for s in signals:
        signal_pts = s.get("score", 0)
        neg_adj = NEGATIVE_SIGNALS.get(s["signal"], 0)
        signal_total += signal_pts + neg_adj

    signal_total = min(signal_total, MAX_SIGNAL_SCORE)
    signal_total = max(signal_total, 0)

    # ── 2. Bonus por dolores de alta/media severidad ──────────────────────────
    for p in pain_points:
        severity = p.get("severity", "low")
        pain_bonus += SEVERITY_BONUS.get(severity, 1)

    pain_bonus = min(pain_bonus, MAX_PAIN_BONUS)

    # ── 3. Bonus por tecnologías de valor ─────────────────────────────────────
    for tech in technologies:
        tech_bonus += TECH_BONUS.get(tech, 0)

    tech_bonus = min(tech_bonus, MAX_TECH_BONUS)

    # ── Score total ───────────────────────────────────────────────────────────
    raw_score = signal_total + pain_bonus + tech_bonus
    score = min(max(raw_score, 0), 100)

    classification = _classify(score)

    logger.debug(
        f"  Scoring: señales={signal_total} + dolores={pain_bonus} + tech={tech_bonus} "
        f"= {score} ({classification})"
    )

    return score, classification


def _classify(score: int) -> str:
    """Clasifica el lead según el score."""
    if score >= SCORE_HOT_THRESHOLD:
        return "HOT"
    if score >= SCORE_WARM_THRESHOLD:
        return "WARM"
    return "COLD"
