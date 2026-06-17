"""
analyzer/signal_detector.py - Detección de señales comerciales

Analiza el contenido y tecnologías de un sitio web para detectar
indicadores de madurez, tamaño y oportunidad de venta.

Cada señal tiene:
  - signal:   nombre descriptivo
  - score:    puntos que aporta al score total (puede ser negativo)
  - evidence: texto breve de evidencia
"""
import re
from dataclasses import dataclass, field


@dataclass
class Signal:
    signal:   str
    score:    int
    evidence: str = ""

    def to_dict(self) -> dict:
        return {"signal": self.signal, "score": self.score, "evidence": self.evidence}


# ── Constantes de detección ──────────────────────────────────────────────────────

CORPORATE_EMAIL_DOMAINS = {
    "gmail.com", "hotmail.com", "yahoo.com", "outlook.com",
    "live.com", "icloud.com", "me.com", "aol.com",
}

BLOG_KEYWORDS = re.compile(
    r"\b(blog|noticias|news|artículos|publicaciones|novedades)\b", re.I
)

JOB_KEYWORDS = re.compile(
    r"\b(trabaja con nosotros|únete|vacantes|empleos|careers|jobs|"
    r"postula|oportunidades laborales|trabaja aquí)\b", re.I
)

BRANCH_KEYWORDS = re.compile(
    r"\b(sucursales|puntos de venta|tiendas|locales|sedes|"
    r"nuestras tiendas|encuéntranos en)\b", re.I
)

GROWTH_KEYWORDS = re.compile(
    r"\b(nuevo|expandiendo|crecimiento|expansión|abrimos|"
    r"nueva sucursal|nuevos productos|nuevo servicio)\b", re.I
)

OUTDATED_YEAR_THRESHOLD = 2021   # copyright anterior a este año → sitio desactualizado


# ── Detector principal ────────────────────────────────────────────────────────────

def detect_signals(
    website_data: dict,
    technologies: list[str],
) -> list[dict]:
    """
    Detecta señales comerciales a partir de datos del sitio web.

    Args:
        website_data: dict con campos de WebsiteData
        technologies: lista de tecnologías detectadas

    Returns:
        Lista de dicts {signal, score, evidence}
    """
    signals: list[Signal] = []
    text = website_data.get("raw_text_snippet", "")
    emails = website_data.get("emails", [])
    socials = website_data.get("social_links", {})
    copyright_year = website_data.get("copyright_year", "")
    title = website_data.get("title", "")
    scrape_ok = website_data.get("scrape_ok", True)

    # ── Señal: sitio web activo ───────────────────────────────────────────────
    if scrape_ok and website_data.get("url"):
        signals.append(Signal(
            "Sitio web activo",
            score=10,
            evidence="Sitio accesible y con contenido"
        ))
    elif not scrape_ok:
        signals.append(Signal(
            "Sin sitio web o inaccesible",
            score=-5,
            evidence=website_data.get("scrape_error", "")
        ))

    # ── Señal: correo corporativo ─────────────────────────────────────────────
    corporate = [e for e in emails if e.split("@")[-1] not in CORPORATE_EMAIL_DOMAINS]
    personal  = [e for e in emails if e.split("@")[-1] in CORPORATE_EMAIL_DOMAINS]

    if corporate:
        signals.append(Signal(
            "Correo corporativo",
            score=15,
            evidence=f"Detectado: {corporate[0]}"
        ))
    elif personal:
        signals.append(Signal(
            "Solo correo personal (no corporativo)",
            score=5,
            evidence=f"Usa: {personal[0]}"
        ))

    # ── Señal: redes sociales activas ────────────────────────────────────────
    n_socials = len(socials)
    if n_socials >= 3:
        signals.append(Signal(
            "Redes sociales activas (múltiples)",
            score=10,
            evidence=f"Redes detectadas: {', '.join(socials.keys())}"
        ))
    elif n_socials >= 1:
        signals.append(Signal(
            "Redes sociales presentes",
            score=5,
            evidence=f"Redes detectadas: {', '.join(socials.keys())}"
        ))

    # ── Señal: blog o noticias ────────────────────────────────────────────────
    if BLOG_KEYWORDS.search(text):
        match = BLOG_KEYWORDS.search(text)
        signals.append(Signal(
            "Blog o sección de noticias",
            score=8,
            evidence=f"Encontrado: '{match.group()}'"
        ))

    # ── Señal: vacantes / trabaja con nosotros ───────────────────────────────
    if JOB_KEYWORDS.search(text):
        match = JOB_KEYWORDS.search(text)
        signals.append(Signal(
            "Publicación de vacantes o empleos",
            score=12,
            evidence=f"Sección detectada: '{match.group()}'"
        ))

    # ── Señal: múltiples sucursales ───────────────────────────────────────────
    if BRANCH_KEYWORDS.search(text):
        match = BRANCH_KEYWORDS.search(text)
        signals.append(Signal(
            "Múltiples sucursales o puntos de venta",
            score=15,
            evidence=f"Detectado: '{match.group()}'"
        ))

    # ── Señal: señales de crecimiento ─────────────────────────────────────────
    if GROWTH_KEYWORDS.search(text):
        match = GROWTH_KEYWORDS.search(text)
        signals.append(Signal(
            "Señales de crecimiento",
            score=12,
            evidence=f"Detectado: '{match.group()}'"
        ))

    # ── Señal: ecommerce activo ───────────────────────────────────────────────
    ecommerce_techs = {"WooCommerce", "Shopify", "Prestashop", "Tiendanube", "Jumpseller"}
    detected_ecommerce = ecommerce_techs.intersection(set(technologies))
    if detected_ecommerce:
        signals.append(Signal(
            "Plataforma ecommerce activa",
            score=18,
            evidence=f"Tecnología: {', '.join(detected_ecommerce)}"
        ))

    # ── Señal: analytics configurado ─────────────────────────────────────────
    analytics_techs = {"Google Analytics", "Google Tag Manager", "Meta Pixel"}
    detected_analytics = analytics_techs.intersection(set(technologies))
    if detected_analytics:
        signals.append(Signal(
            "Analytics de marketing configurado",
            score=8,
            evidence=f"Tecnología: {', '.join(detected_analytics)}"
        ))

    # ── Señal: sitio desactualizado ───────────────────────────────────────────
    if copyright_year:
        try:
            year = int(copyright_year)
            if year < OUTDATED_YEAR_THRESHOLD:
                signals.append(Signal(
                    "Sitio web desactualizado",
                    score=-5,
                    evidence=f"Copyright indica año {year}"
                ))
        except ValueError:
            pass

    # ── Señal: empresa con nombre corporativo en web ──────────────────────────
    corporate_terms = re.compile(
        r"\b(S\.A\.|SpA|Ltda\.|EIRL|S\.R\.L\.|S\.p\.A\.)\b", re.I
    )
    if corporate_terms.search(title + text[:200]):
        signals.append(Signal(
            "Empresa con personalidad jurídica formal",
            score=10,
            evidence="Detectado tipo sociedad en sitio"
        ))

    return [s.to_dict() for s in signals]
