"""
ai/email_generator.py - Generación de correos comerciales personalizados con IA

Genera correos de prospección de máximo 200 palabras, adaptados
al perfil de cada empresa y sus necesidades específicas detectadas.
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


def generate_commercial_email(
    company: dict,
    pain_points: list[dict],
    recommendations: list[dict],
    sender_name:  str = "Equipo Comercial",
    sender_firm:  str = "Asesoría Contable",
) -> str:
    """
    Genera un correo comercial personalizado.

    Args:
        company:         dict con name, category, city, etc.
        pain_points:     lista de dolores detectados
        recommendations: lista de servicios recomendados
        sender_name:     nombre del remitente
        sender_firm:     nombre de la asesoría

    Returns:
        Correo comercial listo para enviar (≤200 palabras)
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY no configurada — omitiendo generación de correo")
        return "[Correo no disponible: configura OPENAI_API_KEY]"

    pains_text = "\n".join(f"- {p['pain']}" for p in pain_points[:4])
    services_text = ", ".join(r["service"] for r in recommendations[:3])

    prompt = f"""Eres un especialista en desarrollo comercial de una asesoría contable y tributaria chilena.

Genera un correo de prospección comercial personalizado para la siguiente empresa:

EMPRESA: {company.get('name', '')}
RUBRO: {company.get('category', '')}
CIUDAD: {company.get('city', '')}

NECESIDADES DETECTADAS:
{pains_text}

SERVICIOS A OFRECER: {services_text}

INSTRUCCIONES:
- Máximo 200 palabras
- Tono profesional pero cercano (tuteo o ustedeo según contexto)
- Menciona al menos UN dolor específico detectado sin revelar cómo lo sabes
- Incluye un llamado a la acción claro (llamada o reunión)
- Firma: {sender_name} | {sender_firm}
- NO uses placeholders como [nombre del contacto]
- Dirígete directamente al "Equipo de gestión" o "Gerencia"
- Usa español chileno natural

Genera SOLO el cuerpo del correo, sin asunto.
"""

    try:
        response = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        email_body = response.choices[0].message.content.strip()

        # Agregar asunto al inicio
        subject = _generate_subject(company["name"], recommendations)
        return f"Asunto: {subject}\n\n{email_body}"

    except Exception as e:
        logger.error(f"Error generando correo para {company.get('name', '')}: {e}")
        return f"[Error al generar correo: {e}]"


def _generate_subject(company_name: str, recommendations: list[dict]) -> str:
    """Genera un asunto de correo relevante."""
    if not OPENAI_API_KEY:
        return f"Propuesta de servicios contables para {company_name}"

    service = recommendations[0]["service"] if recommendations else "servicios contables"
    subjects = [
        f"Optimizamos la gestión contable de {company_name}",
        f"{service} a medida para {company_name}",
        f"¿Tiene todo en orden en {company_name}? Le contamos cómo podemos ayudar",
        f"Solución de {service.lower()} para {company_name}",
    ]
    return subjects[hash(company_name) % len(subjects)]
