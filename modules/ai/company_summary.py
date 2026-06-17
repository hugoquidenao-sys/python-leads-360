"""
ai/company_summary.py - Resumen ejecutivo de empresa usando OpenAI

Genera un resumen conciso (≤300 palabras) de la empresa basado
en el contenido de su sitio web.
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


def generate_company_summary(
    company_name: str,
    website_text:  str,
    title:         str = "",
    meta_desc:     str = "",
) -> str:
    """
    Genera un resumen ejecutivo de la empresa.

    Args:
        company_name:  Nombre de la empresa
        website_text:  Texto extraído del sitio web (snippet)
        title:         Título de la página
        meta_desc:     Meta descripción

    Returns:
        Resumen en texto plano (≤300 palabras)
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY no configurada — omitiendo resumen IA")
        return "[Resumen no disponible: configura OPENAI_API_KEY]"

    context = f"""
Empresa: {company_name}
Título del sitio: {title}
Descripción: {meta_desc}
Contenido del sitio web:
{website_text[:2000]}
""".strip()

    prompt = f"""Eres un analista de inteligencia comercial especializado en empresas chilenas.

Analiza la siguiente información de la empresa y genera un resumen ejecutivo de máximo 300 palabras.

El resumen debe incluir:
1. Rubro o industria principal
2. Tamaño estimado (micro, pequeña, mediana empresa)
3. Presencia digital y madurez tecnológica
4. Posibles necesidades contables o administrativas detectadas
5. Oportunidad comercial para una asesoría contable

Sé conciso, directo y profesional. Usa lenguaje de negocios en español chileno.

{context}
"""

    try:
        response = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Error generando resumen IA para {company_name}: {e}")
        return f"[Error al generar resumen: {e}]"
