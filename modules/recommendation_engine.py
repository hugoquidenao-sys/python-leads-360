"""
recommendations/recommendation_engine.py - Motor de recomendaciones de servicios

Mapea señales y dolores detectados a servicios contables específicos.
Prioriza servicios según relevancia para el perfil de cada empresa.

Servicios disponibles:
  - Contabilidad mensual
  - Remuneraciones
  - Tributación
  - Outsourcing contable
  - Constitución de empresas
  - Gestión administrativa
"""
from dataclasses import dataclass

from config import AVAILABLE_SERVICES


# ── Modelo ───────────────────────────────────────────────────────────────────────

@dataclass
class Recommendation:
    service:   str
    priority:  int
    rationale: str

    def to_dict(self) -> dict:
        return {
            "service":   self.service,
            "priority":  self.priority,
            "rationale": self.rationale,
        }


# ── Mapeo dolor → servicio ───────────────────────────────────────────────────────

PAIN_TO_SERVICE: dict[str, list[tuple[str, str]]] = {
    "IVA": [
        ("Tributación", "Gestión de IVA y declaraciones mensuales F29"),
        ("Contabilidad mensual", "Registro contable de operaciones de venta"),
    ],
    "conciliación bancaria": [
        ("Contabilidad mensual", "Conciliación bancaria y registro de transacciones"),
        ("Outsourcing contable", "Externalización completa del proceso contable"),
    ],
    "remuneraciones": [
        ("Remuneraciones", "Liquidaciones, cotizaciones y gestión de contratos"),
    ],
    "outsourcing": [
        ("Outsourcing contable", "Servicio integral de contabilidad externalizada"),
    ],
    "constitución": [
        ("Constitución de empresas", "Formalización y constitución de sociedad"),
    ],
    "tributaria": [
        ("Tributación", "Asesoría tributaria y planificación fiscal"),
        ("Contabilidad mensual", "Contabilidad al día para cumplimiento tributario"),
    ],
    "obligaciones tributarias": [
        ("Tributación", "Gestión de F29, F22 y declaraciones juradas"),
        ("Contabilidad mensual", "Contabilidad mensual para cumplimiento SII"),
    ],
    "informalidad": [
        ("Constitución de empresas", "Formalización de la actividad empresarial"),
        ("Contabilidad mensual", "Implementación de contabilidad formal"),
    ],
    "laboral": [
        ("Remuneraciones", "Gestión completa de remuneraciones y contratos"),
        ("Gestión administrativa", "Apoyo en procesos administrativos de RRHH"),
    ],
    "DTE": [
        ("Tributación", "Implementación y gestión de facturación electrónica DTE"),
        ("Gestión administrativa", "Gestión documental y administrativo-contable"),
    ],
}

# Servicios de fallback si no se mapean dolores específicos
FALLBACK_SERVICES = [
    Recommendation("Contabilidad mensual", 1, "Servicio base para cualquier empresa"),
    Recommendation("Tributación", 2, "Cumplimiento tributario mensual y anual"),
]


# ── Motor principal ──────────────────────────────────────────────────────────────

def generate_recommendations(
    pain_points: list[dict],
    signals:     list[dict],
    score:       int,
) -> list[dict]:
    """
    Genera recomendaciones de servicios basadas en el perfil del lead.

    Args:
        pain_points: lista de {pain, severity, evidence}
        signals:     lista de {signal, score, evidence}
        score:       score calculado del lead

    Returns:
        Lista ordenada de {service, priority, rationale}
    """
    service_map: dict[str, str] = {}   # service → rationale

    # ── Mapear dolores a servicios ─────────────────────────────────────────────
    for pain in pain_points:
        pain_text = pain["pain"].lower()
        severity  = pain.get("severity", "low")

        for keyword, service_list in PAIN_TO_SERVICE.items():
            if keyword in pain_text:
                for service, rationale in service_list:
                    if service not in service_map:
                        service_map[service] = rationale

    # ── Reglas basadas en señales ──────────────────────────────────────────────
    signal_names = {s["signal"] for s in signals}

    if "Múltiples sucursales o puntos de venta" in signal_names:
        service_map.setdefault(
            "Outsourcing contable",
            "Empresa multilocal requiere contabilidad centralizada"
        )

    if "Publicación de vacantes o empleos" in signal_names:
        service_map.setdefault(
            "Remuneraciones",
            "Empresa en crecimiento con gestión activa de personal"
        )

    if "Señales de crecimiento" in signal_names:
        service_map.setdefault(
            "Gestión administrativa",
            "Apoyo administrativo para acompañar el crecimiento"
        )

    if "Empresa posiblemente no formalizada" in " ".join(
        p["pain"] for p in pain_points
    ):
        service_map.setdefault(
            "Constitución de empresas",
            "Empresa con indicios de informalidad que requiere formalización"
        )

    # ── Fallback si no hay recomendaciones ────────────────────────────────────
    if not service_map:
        return [r.to_dict() for r in FALLBACK_SERVICES]

    # ── Priorizar por relevancia y score ──────────────────────────────────────
    ordered = _prioritize(service_map, score)
    return [r.to_dict() for r in ordered]


def _prioritize(service_map: dict[str, str], score: int) -> list[Recommendation]:
    """Ordena servicios por prioridad estratégica."""
    priority_order = [
        "Contabilidad mensual",
        "Tributación",
        "Remuneraciones",
        "Outsourcing contable",
        "Gestión administrativa",
        "Constitución de empresas",
    ]

    recs: list[Recommendation] = []
    for i, service in enumerate(priority_order, 1):
        if service in service_map:
            recs.append(Recommendation(
                service=service,
                priority=i,
                rationale=service_map[service],
            ))

    # Añadir cualquier servicio no contemplado en el orden por defecto
    for service, rationale in service_map.items():
        if not any(r.service == service for r in recs):
            recs.append(Recommendation(
                service=service,
                priority=len(recs) + 1,
                rationale=rationale,
            ))

    return recs
