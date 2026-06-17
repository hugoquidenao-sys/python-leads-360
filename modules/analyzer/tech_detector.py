"""
analyzer/tech_detector.py - Detección de tecnologías en sitios web

Detecta CMSs, plataformas ecommerce y herramientas de marketing
usando únicamente análisis de HTML y patrones de texto (sin APIs externas).
"""
import re
from dataclasses import dataclass


@dataclass
class TechSignature:
    name:     str
    patterns: list[str]   # Regex patterns sobre HTML crudo


# ── Firmas de detección ──────────────────────────────────────────────────────────

TECH_SIGNATURES: list[TechSignature] = [
    TechSignature("WordPress", [
        r"wp-content/",
        r"wp-includes/",
        r'<meta name="generator" content="WordPress',
        r"wp-json",
    ]),
    TechSignature("WooCommerce", [
        r"woocommerce",
        r"wc-api",
        r"add-to-cart",
    ]),
    TechSignature("Shopify", [
        r"cdn\.shopify\.com",
        r'content="Shopify',
        r"myshopify\.com",
        r"shopify-section",
    ]),
    TechSignature("Wix", [
        r"static\.wixstatic\.com",
        r"wix\.com",
        r"X-Wix-",
        r"wixsite\.com",
    ]),
    TechSignature("Squarespace", [
        r"squarespace\.com",
        r'Generator.*Squarespace',
        r"sqsp-",
    ]),
    TechSignature("Webflow", [
        r"webflow\.com",
        r"webflow\.io",
        r"w-webflow-badge",
    ]),
    TechSignature("Google Analytics", [
        r"google-analytics\.com/analytics\.js",
        r"gtag/js\?id=G-",
        r"gtag/js\?id=UA-",
        r"GoogleAnalyticsObject",
    ]),
    TechSignature("Google Tag Manager", [
        r"googletagmanager\.com/gtm\.js",
        r"GTM-[A-Z0-9]+",
    ]),
    TechSignature("Meta Pixel", [
        r"connect\.facebook\.net/en_US/fbevents\.js",
        r"fbq\('init'",
        r"facebook-jssdk",
    ]),
    TechSignature("HubSpot", [
        r"js\.hs-scripts\.com",
        r"hubspot\.com",
        r"hs-analytics",
    ]),
    TechSignature("Mailchimp", [
        r"list-manage\.com",
        r"mailchimp\.com",
        r"mc\.js",
    ]),
    TechSignature("Joomla", [
        r"Joomla!",
        r"/components/com_",
        r"joomla",
    ]),
    TechSignature("Drupal", [
        r"Drupal\.settings",
        r"/sites/default/files/",
        r'Generator.*Drupal',
    ]),
    TechSignature("Prestashop", [
        r"prestashop",
        r"add-to-cart-or-refresh",
    ]),
    TechSignature("Tiendanube", [
        r"tiendanube\.com",
        r"d26lpennugtm8s\.cloudfront\.net",
    ]),
    TechSignature("Jumpseller", [
        r"jumpseller\.com",
        r"js\.jumpseller\.com",
    ]),
]


# ── Detector principal ────────────────────────────────────────────────────────────

def detect_technologies(html: str) -> list[str]:
    """
    Analiza el HTML crudo y retorna lista de tecnologías detectadas.

    Args:
        html: HTML completo del sitio web

    Returns:
        Lista de nombres de tecnologías detectadas
    """
    if not html:
        return []

    detected: list[str] = []

    for tech in TECH_SIGNATURES:
        for pattern in tech.patterns:
            if re.search(pattern, html, re.IGNORECASE):
                detected.append(tech.name)
                break   # Una coincidencia es suficiente por tecnología

    return detected


def is_ecommerce(technologies: list[str]) -> bool:
    """Determina si el sitio tiene capacidad de ecommerce."""
    ecommerce_techs = {"WooCommerce", "Shopify", "Prestashop", "Tiendanube", "Jumpseller"}
    return bool(ecommerce_techs.intersection(set(technologies)))


def has_analytics(technologies: list[str]) -> bool:
    """Determina si el sitio tiene analytics configurado."""
    analytics_techs = {"Google Analytics", "Google Tag Manager", "Meta Pixel", "HubSpot"}
    return bool(analytics_techs.intersection(set(technologies)))


def has_modern_cms(technologies: list[str]) -> bool:
    """Determina si usa un CMS moderno."""
    cms_techs = {"WordPress", "Wix", "Squarespace", "Webflow", "Drupal", "Joomla"}
    return bool(cms_techs.intersection(set(technologies)))
