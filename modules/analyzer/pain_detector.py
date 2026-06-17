"""
analyzer/pain_detector.py - Detección de dolores de negocio contable/tributario

Cruza señales detectadas y tecnologías para inferir necesidades
específicas de servicios contables, tributarios y administrativos.

Retorna lista de dicts:
  {pain, severity: low|medium|high, evidence}
"""
import re
from dataclasses import dataclass


@dataclass
class PainPoint:
    pain:     str
    severity: str = "medium"  # low | medium | high
    evidence: str = ""

    def to_dict(self) -> dict:
        return {"pain": self.pain, "severity": self.severity, "evidence": self.evidence}


# ── Detector principal ────────────────────────────────────────────────────────────

def detect_pains(
    website_data: dict,
    technologies:  list[str],
    signals:       list[dict],
) -> list[dict]:
    """
    Detecta dolores de negocio contable/administrativo.

    Args:
        website_data: dict de WebsiteData
        technologies: tecnologías detectadas
        signals:      señales detectadas

    Returns:
        Lista de dicts {pain, severity, evidence}
    """
    pains: list[PainPoint] = []
    text      = website_data.get("raw_text_snippet", "")
    emails    = website_data.get("emails", [])
    signal_names = {s["signal"] for s in signals}
    tech_set  = set(technologies)

    # ── ECOMMERCE → IVA + conciliación ──────────────────────────────────────
    ecommerce_techs = {"WooCommerce", "Shopify", "Prestashop", "Tiendanube", "Jumpseller"}
    if tech_set.intersection(ecommerce_techs):
        pains.append(PainPoint(
            pain="Gestión compleja de IVA en ventas online",
            severity="high",
            evidence=f"Plataforma ecommerce detectada: {', '.join(tech_set.intersection(ecommerce_techs))}"
        ))
        pains.append(PainPoint(
            pain="Conciliación bancaria con múltiples medios de pago",
            severity="high",
            evidence="Ecommerce activo implica pasarelas de pago múltiples"
        ))
        pains.append(PainPoint(
            pain="Boletas de honorarios electrónicas o DTE sin gestión centralizada",
            severity="medium",
            evidence="Ventas electrónicas requieren facturación DTE"
        ))

    # ── MÚLTIPLES SUCURSALES → outsourcing ──────────────────────────────────
    if "Múltiples sucursales o puntos de venta" in signal_names:
        pains.append(PainPoint(
            pain="Necesidad de outsourcing contable por volumen multilocal",
            severity="high",
            evidence="Empresa con múltiples sucursales detectada"
        ))
        pains.append(PainPoint(
            pain="Complejidad tributaria por operaciones en múltiples comunas",
            severity="medium",
            evidence="Múltiples puntos de venta generan mayor complejidad fiscal"
        ))

    # ── VACANTES → remuneraciones ─────────────────────────────────────────────
    if "Publicación de vacantes o empleos" in signal_names:
        pains.append(PainPoint(
            pain="Gestión de remuneraciones y contratos en crecimiento",
            severity="high",
            evidence="Empresa activamente contratando personal"
        ))
        pains.append(PainPoint(
            pain="Obligaciones laborales: liquidaciones, finiquitos, cotizaciones",
            severity="high",
            evidence="Alta rotación o crecimiento de dotación"
        ))

    # ── CRECIMIENTO → constitución + remuneraciones ───────────────────────────
    if "Señales de crecimiento" in signal_names:
        pains.append(PainPoint(
            pain="Necesidad de formalización y constitución de empresa",
            severity="medium",
            evidence="Señales de expansión del negocio"
        ))
        pains.append(PainPoint(
            pain="Planificación tributaria ante crecimiento de ingresos",
            severity="medium",
            evidence="Mayor nivel de ventas aumenta carga tributaria"
        ))

    # ── SOLO CORREO PERSONAL → informalidad ──────────────────────────────────
    personal_email_signal = "Solo correo personal (no corporativo)"
    if personal_email_signal in signal_names:
        pains.append(PainPoint(
            pain="Empresa posiblemente no formalizada o con contabilidad informal",
            severity="high",
            evidence="Uso de correo personal (Gmail/Hotmail) como contacto de empresa"
        ))

    # ── SIN SITIO WEB → informalidad ─────────────────────────────────────────
    if "Sin sitio web o inaccesible" in signal_names:
        pains.append(PainPoint(
            pain="Empresa con baja presencia digital y posible contabilidad informal",
            severity="medium",
            evidence="Sin sitio web propio o accesible"
        ))

    # ── WORDPRESS SIN WOO → profesional de servicios ─────────────────────────
    if "WordPress" in tech_set and not tech_set.intersection(ecommerce_techs):
        pains.append(PainPoint(
            pain="Empresa de servicios posiblemente sin sistema contable integrado",
            severity="medium",
            evidence="Sitio informativo sin ecommerce sugiere facturación manual"
        ))

    # ── ANALYTICS PERO SIN ASESORÍA ──────────────────────────────────────────
    if "Plataforma ecommerce activa" in signal_names and "Analytics de marketing configurado" in signal_names:
        pains.append(PainPoint(
            pain="Alto volumen de transacciones sin necesariamente asesoría tributaria especializada",
            severity="high",
            evidence="Ecommerce con analytics activo → empresa digital con necesidades contables complejas"
        ))

    # ── EMPRESA FORMAL → F29 + declaraciones ─────────────────────────────────
    if "Empresa con personalidad jurídica formal" in signal_names:
        pains.append(PainPoint(
            pain="Obligaciones tributarias recurrentes: F29, F22, DJ informativos",
            severity="medium",
            evidence="Sociedad formal con obligaciones SII mensuales y anuales"
        ))

    # Siempre sugerimos revisión contable como baseline
    if not pains:
        pains.append(PainPoint(
            pain="Necesidad de revisión y ordenamiento contable general",
            severity="low",
            evidence="Empresa sin señales específicas detectadas"
        ))

    return [p.to_dict() for p in pains]
