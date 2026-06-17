"""
main.py - Python Leads 360
Herramienta de prospección inteligente para asesorías contables.

Uso:
    python main.py
    python main.py --keyword "ferretería" --city "Santiago" --limit 10
    python main.py --keyword "restaurante" --city "Valparaíso" --skip-ai
"""
import argparse
import sys
import time
from pathlib import Path

from utils.logger import logger
from config import SCRAPING_DELAY, MAX_COMPANIES_PER_SEARCH
from database.sqlite_manager import (
    init_db, upsert_company, save_analysis, save_signals,
    save_pain_points, save_recommendations, save_ai_output,
    get_full_leads, get_company_by_id,
)
from discovery.google_maps import search_companies
from analyzer.website_scraper import scrape_website
from analyzer.tech_detector import detect_technologies
from analyzer.signal_detector import detect_signals
from analyzer.pain_detector import detect_pains
from scoring.scoring_engine import calculate_score
from recommendations.recommendation_engine import generate_recommendations
from exporters.excel_exporter import export_leads_excel
from exporters.pdf_exporter import export_proposal_pdf


# ── Banner ────────────────────────────────────────────────────────────────────────

BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║         🔍  PYTHON LEADS 360  |  MVP v1.0               ║
║    Prospección inteligente para asesorías contables      ║
╚══════════════════════════════════════════════════════════╝
"""


# ── Argparse ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Python Leads 360 - Prospección contable inteligente"
    )
    parser.add_argument("--keyword", "-k", type=str, default=None,
                        help="Rubro a buscar (ej: 'ferretería')")
    parser.add_argument("--city",    "-c", type=str, default=None,
                        help="Ciudad donde buscar (ej: 'Santiago')")
    parser.add_argument("--limit",   "-l", type=int, default=MAX_COMPANIES_PER_SEARCH,
                        help="Máximo de empresas a procesar")
    parser.add_argument("--skip-ai", action="store_true",
                        help="Omitir generación de correos y propuestas IA")
    parser.add_argument("--skip-pdf", action="store_true",
                        help="Omitir exportación de PDFs individuales")
    parser.add_argument("--firm-name", type=str, default="Asesoría Contable & Tributaria",
                        help="Nombre de tu asesoría para las propuestas")
    return parser.parse_args()


# ── Flujo principal ───────────────────────────────────────────────────────────────

def run(keyword: str, city: str, limit: int, skip_ai: bool, skip_pdf: bool, firm_name: str):
    start_time = time.time()

    print(BANNER)
    logger.info(f"Iniciando búsqueda: '{keyword}' en '{city}' — límite: {limit}")

    # 0. Inicializar base de datos
    init_db()

    # ── ETAPA 1: Descubrimiento ───────────────────────────────────────────────
    logger.info("=" * 55)
    logger.info("ETAPA 1/8 → Descubrimiento de empresas")
    logger.info("=" * 55)

    companies = search_companies(keyword, city)
    companies = companies[:limit]

    if not companies:
        logger.error("No se encontraron empresas. Verifica tu GOOGLE_MAPS_API_KEY o el rubro/ciudad.")
        sys.exit(1)

    logger.info(f"✓ {len(companies)} empresas a analizar")

    # ── ETAPAS 2-7: Análisis por empresa ─────────────────────────────────────
    processed = 0
    for idx, company in enumerate(companies, 1):
        # upsert garantiza que la empresa esté en DB y retorna su ID
        cid = upsert_company(company)
        company["id"] = cid   # enriquecer dict para uso posterior
        company_name = company.get("name", f"Empresa #{idx}")

        logger.info(f"\n[{idx}/{len(companies)}] → {company_name}")
        logger.info("-" * 50)

        # ETAPA 2: Scraping web
        logger.info("  ETAPA 2 → Scraping del sitio web…")
        website_url = company.get("website", "")
        website_data = scrape_website(website_url) if website_url else _empty_website_data(website_url)
        save_analysis(cid, website_data.to_dict())

        # ETAPA 3: Detección de tecnologías
        logger.info("  ETAPA 3 → Detección de tecnologías…")
        raw_html = _get_raw_html(website_url)
        technologies = detect_technologies(raw_html)
        if technologies:
            logger.info(f"    Tecnologías: {', '.join(technologies)}")

        # ETAPA 4: Señales comerciales
        logger.info("  ETAPA 4 → Detección de señales…")
        signals = detect_signals(website_data.to_dict(), technologies)
        save_signals(cid, signals)
        logger.info(f"    {len(signals)} señales detectadas")

        # ETAPA 5: Dolores de negocio
        logger.info("  ETAPA 5 → Detección de dolores…")
        pains = detect_pains(website_data.to_dict(), technologies, signals)
        save_pain_points(cid, pains)
        logger.info(f"    {len(pains)} dolores detectados")

        # ETAPA 6: Scoring
        logger.info("  ETAPA 6 → Calculando score…")
        score, classification = calculate_score(signals, pains, technologies)
        logger.info(f"    Score: {score}/100  →  {classification}")

        # ETAPA 7: Recomendaciones
        logger.info("  ETAPA 7 → Generando recomendaciones…")
        recommendations = generate_recommendations(pains, signals, score)
        save_recommendations(cid, recommendations, score, classification)
        logger.info(f"    {len(recommendations)} servicios recomendados")

        # ── ETAPA IA (opcional) ───────────────────────────────────────────────
        if not skip_ai:
            _run_ai_pipeline(cid, company, website_data, pains, recommendations, score, classification, firm_name)

        processed += 1
        time.sleep(SCRAPING_DELAY)

    # ── ETAPA 8: Exportación Excel ────────────────────────────────────────────
    logger.info("\n" + "=" * 55)
    logger.info("ETAPA 8/8 → Exportando resultados a Excel…")
    logger.info("=" * 55)

    leads = get_full_leads(city=city, keyword=keyword)
    excel_path = export_leads_excel(leads)

    # ── ETAPA 9: PDFs (opcional) ──────────────────────────────────────────────
    if not skip_pdf and not skip_ai:
        _export_pdfs(leads, firm_name)

    # ── Resumen final ─────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    _print_summary(leads, excel_path, elapsed)


# ── Funciones auxiliares ──────────────────────────────────────────────────────────

def _empty_website_data(url: str):
    """Retorna WebsiteData vacío cuando no hay URL."""
    from analyzer.website_scraper import WebsiteData
    return WebsiteData(
        url=url,
        scrape_ok=False,
        scrape_error="Sin URL proporcionada"
    )


def _get_raw_html(url: str) -> str:
    """Descarga HTML crudo para detección de tecnologías."""
    if not url:
        return ""
    try:
        import requests
        from config import DEFAULT_HEADERS, SCRAPING_TIMEOUT
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=SCRAPING_TIMEOUT,
                            verify=False, allow_redirects=True)
        return resp.text
    except Exception:
        return ""


def _website_field(website_data, field: str, default: str = "") -> str:
    """Accede a un campo de WebsiteData ya sea objeto o dict."""
    if isinstance(website_data, dict):
        return website_data.get(field, default)
    return getattr(website_data, field, default)


def _run_ai_pipeline(cid, company, website_data, pains, recommendations, score, classification, firm_name):
    """Ejecuta la pipeline de generación IA."""
    try:
        from ai.company_summary import generate_company_summary
        from ai.email_generator import generate_commercial_email
        from ai.proposal_generator import generate_proposal

        logger.info("  IA → Generando resumen ejecutivo…")
        summary = generate_company_summary(
            company_name=company.get("name", ""),
            website_text=_website_field(website_data, "raw_text_snippet"),
            title=_website_field(website_data, "title"),
            meta_desc=_website_field(website_data, "meta_description"),
        )
        save_ai_output(cid, "summary", summary)

        logger.info("  IA → Generando correo comercial…")
        email = generate_commercial_email(
            company, pains, recommendations, firm_name=firm_name
        )
        save_ai_output(cid, "email", email)

        logger.info("  IA → Generando propuesta comercial…")
        proposal = generate_proposal(
            company, pains, recommendations, score, classification, firm_name=firm_name
        )
        save_ai_output(cid, "proposal", proposal)

    except Exception as e:
        logger.error(f"Error en pipeline IA: {e}")


def _export_pdfs(leads: list[dict], firm_name: str):
    """Exporta PDFs para leads HOT y WARM."""
    from database.sqlite_manager import get_ai_output

    logger.info("\nExportando PDFs para leads HOT y WARM…")
    pdf_count = 0
    for lead in leads:
        cls = lead.get("classification", "COLD")
        if cls not in ("HOT", "WARM"):
            continue

        cid = lead["company"]["id"]
        proposal = get_ai_output(cid, "proposal")
        email    = get_ai_output(cid, "email")

        if proposal:
            export_proposal_pdf(
                company=lead["company"],
                proposal_text=proposal,
                score=lead.get("score", 0),
                classification=cls,
                email_text=email or "",
                firm_name=firm_name,
            )
            pdf_count += 1

    logger.info(f"✓ {pdf_count} PDFs generados")


def _print_summary(leads: list[dict], excel_path, elapsed: float):
    """Imprime resumen final en consola."""
    hot  = sum(1 for l in leads if l.get("classification") == "HOT")
    warm = sum(1 for l in leads if l.get("classification") == "WARM")
    cold = sum(1 for l in leads if l.get("classification") == "COLD")

    print("\n" + "=" * 55)
    print("  ✅  ANÁLISIS COMPLETADO")
    print("=" * 55)
    print(f"  Total leads analizados : {len(leads)}")
    print(f"  🔴 HOT  (prioridad alta) : {hot}")
    print(f"  🟠 WARM (prioridad media): {warm}")
    print(f"  🔵 COLD (desarrollo)    : {cold}")
    print(f"  ⏱  Tiempo total         : {elapsed:.1f}s")
    if excel_path:
        print(f"  📊 Excel exportado      : {excel_path}")
    print("=" * 55 + "\n")


# ── Entry point ───────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # Modo interactivo si no se pasan argumentos
    keyword = args.keyword
    city    = args.city

    if not keyword:
        print(BANNER)
        print("  Ingresa los datos de búsqueda:\n")
        keyword = input("  Rubro (ej: ferretería, restaurante, clínica): ").strip()
        if not keyword:
            print("  ⚠️  Debes ingresar un rubro.")
            sys.exit(1)

    if not city:
        city = input("  Ciudad (ej: Santiago, Valparaíso): ").strip()
        if not city:
            print("  ⚠️  Debes ingresar una ciudad.")
            sys.exit(1)

    run(
        keyword=keyword,
        city=city,
        limit=args.limit,
        skip_ai=args.skip_ai,
        skip_pdf=args.skip_pdf,
        firm_name=args.firm_name,
    )


if __name__ == "__main__":
    main()
