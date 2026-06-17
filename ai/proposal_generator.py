"""
ai/proposal_generator.py - Generación de propuestas comerciales con IA

Genera propuestas de una página, estructuradas y personalizadas,
para presentar a cada prospect.
"""
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from utils.logger import logger


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def generate_proposal(
    company:         dict,
    pain_points:     list[dict],
    recommendations: list[dict],
    score:           int,
    classification:  str,
    firm_name:       str = "Asesoría Contable & Tributaria",
) -> str:
    """
    Genera una propuesta comercial personalizada (una página).

    Args:
        company:         dict con datos de la empresa
        pain_points:     lista de dolores detectados
        recommendations: servicios recomendados
        score:           score del lead
        classification:  COLD / WARM / HOT
        firm_name:       nombre de la asesoría

    Returns:
        Propuesta en texto plano lista para exportar a PDF
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY no configurada — omitiendo propuesta IA")
        return "[Propuesta no disponible: configura OPENAI_API_KEY]"

    pains_text = "\n".join(
        f"- {p['pain']} (severidad: {p.get('severity', 'media')})"
        for p in pain_points[:5]
    )
    services_text = "\n".join(
        f"{i}. {r['service']}: {r.get('rationale', '')}"
        for i, r in enumerate(recommendations[:4], 1)
    )

    urgency = {
        "HOT": "alta prioridad: empresa con necesidades inmediatas",
        "WARM": "prioridad media: empresa con necesidades detectadas",
        "COLD": "oportunidad a desarrollar: empresa con potencial a mediano plazo",
    }.get(classification, "media")

    prompt = f"""Eres un especialista en redacción de propuestas comerciales para una asesoría contable chilena.

Genera una propuesta comercial profesional de UNA PÁGINA para:

EMPRESA PROSPECTO: {company.get('name', '')}
RUBRO: {company.get('category', '')}
CIUDAD: {company.get('city', '')}
PERFIL: {urgency}

NECESIDADES IDENTIFICADAS:
{pains_text}

SERVICIOS PROPUESTOS:
{services_text}

ASESORÍA QUE PRESENTA: {firm_name}

ESTRUCTURA DE LA PROPUESTA (respeta este orden):
1. ENCABEZADO: fecha actual, empresa destinataria
2. RESUMEN EJECUTIVO (2-3 oraciones de por qué los contactamos)
3. SITUACIÓN DETECTADA (necesidades sin revelar cómo las detectamos)
4. NUESTRA PROPUESTA (servicios con descripción breve de cada uno)
5. ¿POR QUÉ ELEGIRNOS? (3 puntos diferenciadores breves)
6. PRÓXIMOS PASOS (llamado a la acción claro)
7. DATOS DE CONTACTO (marca con [COMPLETAR])

INSTRUCCIONES:
- Máximo 600 palabras en total
- Tono profesional y confiable
- Usa español chileno correcto
- Sin precios (se discuten en reunión)
- Formato: usa títulos en MAYÚSCULAS para cada sección

Genera SOLO el texto de la propuesta.
"""

    try:
        response = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Error generando propuesta para {company.get('name', '')}: {e}")
        return f"[Error al generar propuesta: {e}]"
