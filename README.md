# 🔍 Python Leads 360

> Herramienta de prospección inteligente para encontrar clientes potenciales de servicios contables, tributarios, de remuneraciones y outsourcing administrativo.

---

## ¿Qué hace?

Python Leads 360 automatiza la prospección comercial de una asesoría contable en 9 pasos:

1. **Descubrir** empresas por rubro y ciudad (Google Maps API)
2. **Scrapear** sus sitios web para extraer información clave
3. **Detectar** tecnologías (WordPress, WooCommerce, Shopify, etc.)
4. **Identificar** señales comerciales (sucursales, vacantes, ecommerce activo)
5. **Inferir** dolores de negocio contable/tributario
6. **Calcular** un score de oportunidad (0–100) y clasificar en COLD/WARM/HOT
7. **Recomendar** servicios específicos (contabilidad, remuneraciones, tributación, etc.)
8. **Exportar** un Excel con todos los leads formateado por clasificación
9. **Generar** con IA correos comerciales y propuestas personalizadas por empresa

---

## Stack técnico

| Herramienta | Uso |
|---|---|
| Python 3.12+ | Lenguaje principal |
| requests + BeautifulSoup4 | Scraping de sitios web |
| Playwright | Fallback para sitios JS-heavy |
| pandas + openpyxl | Exportación Excel |
| SQLite3 | Base de datos local |
| OpenAI GPT-4o-mini | Correos y propuestas comerciales |
| ReportLab | Exportación PDF |
| Loguru | Logging estructurado |
| Pydantic | Validación de datos |
| pytest | Tests unitarios |

---

## Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone https://github.com/tu-usuario/python-leads-360
cd python-leads-360
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate.bat     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar Playwright (opcional, para sitios JavaScript)

```bash
playwright install chromium
```

---

## Configuración

### Variables de entorno

```bash
cp .env.example .env
```

Editar `.env`:

```env
# Requerido para búsqueda de empresas
GOOGLE_MAPS_API_KEY=AIza...

# Requerido para generación de correos y propuestas
OPENAI_API_KEY=sk-...

# Opcionales
OPENAI_MODEL=gpt-4o-mini
MAX_COMPANIES_PER_SEARCH=20
SCRAPING_TIMEOUT=15
```

### Obtener API Keys

**Google Maps Places API:**
1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un proyecto → Habilita "Places API"
3. Genera una API Key → restricción de IP recomendada
4. Costo estimado: ~$17 USD por 1000 búsquedas (primer tier gratuito disponible)

**OpenAI:**
1. Ve a [platform.openai.com](https://platform.openai.com)
2. API Keys → Create new secret key
3. Costo estimado con GPT-4o-mini: ~$0.05 USD por 20 empresas procesadas

---

## Ejecución

### Modo interactivo (recomendado para empezar)

```bash
python main.py
```

El sistema te pedirá el rubro y la ciudad.

### Modo argumentos (para automatización)

```bash
# Búsqueda básica
python main.py --keyword "ferretería" --city "Santiago"

# Con límite de empresas
python main.py --keyword "restaurante" --city "Valparaíso" --limit 10

# Sin generación de IA (más rápido)
python main.py --keyword "clínica dental" --city "Concepción" --skip-ai

# Con nombre de tu asesoría en las propuestas
python main.py -k "constructora" -c "Santiago" --firm-name "López & Asociados Contadores"

# Solo Excel, sin PDFs
python main.py -k "hotel" -c "Antofagasta" --skip-pdf
```

### Ejecutar solo los tests

```bash
pytest tests/ -v
```

---

## Ejemplos de uso

### Búsqueda de ferreterías en Santiago

```
$ python main.py -k "ferretería" -c "Santiago" --limit 15

╔══════════════════════════════════════════════════════════╗
║         🔍  PYTHON LEADS 360  |  MVP v1.0               ║
║    Prospección inteligente para asesorías contables      ║
╚══════════════════════════════════════════════════════════╝

10:30:01 | INFO     | Iniciando búsqueda: 'ferretería' en 'Santiago'
10:30:02 | INFO     | ✓ 15 empresas a analizar

[1/15] → Ferretería San José Ltda.
  ETAPA 2 → Scraping del sitio web…
  ETAPA 3 → Detección de tecnologías…
    Tecnologías: WordPress, WooCommerce, Google Analytics
  ETAPA 4 → Detección de señales…
    6 señales detectadas
  ETAPA 5 → Detección de dolores…
    4 dolores detectados
  ETAPA 6 → Calculando score…
    Score: 78/100  →  HOT
  ETAPA 7 → Generando recomendaciones…
    3 servicios recomendados
  IA → Generando resumen ejecutivo…
  IA → Generando correo comercial…
  IA → Generando propuesta comercial…

...

═══════════════════════════════════════════════════
  ✅  ANÁLISIS COMPLETADO
═══════════════════════════════════════════════════
  Total leads analizados : 15
  🔴 HOT  (prioridad alta) : 4
  🟠 WARM (prioridad media): 7
  🔵 COLD (desarrollo)    : 4
  ⏱  Tiempo total         : 187.3s
  📊 Excel exportado      : outputs/leads.xlsx
═══════════════════════════════════════════════════
```

---

## Estructura del proyecto

```
python-leads-360/
├── main.py                    ← Orquestador principal y CLI
├── config.py                  ← Configuración central
├── requirements.txt
├── .env.example
├── README.md
│
├── data/                      ← Base de datos SQLite y logs
│   ├── leads360.db
│   └── logs/
│
├── outputs/                   ← Archivos generados
│   ├── leads.xlsx
│   └── propuesta_*.pdf
│
├── discovery/
│   └── google_maps.py         ← Búsqueda de empresas por rubro/ciudad
│
├── analyzer/
│   ├── website_scraper.py     ← Extracción de datos de sitios web
│   ├── tech_detector.py       ← Detección de tecnologías (WP, Shopify, etc.)
│   ├── signal_detector.py     ← Señales comerciales (sucursales, vacantes, etc.)
│   └── pain_detector.py       ← Dolores de negocio contable/tributario
│
├── scoring/
│   └── scoring_engine.py      ← Score 0-100 + clasificación COLD/WARM/HOT
│
├── recommendations/
│   └── recommendation_engine.py ← Servicios recomendados por perfil
│
├── ai/
│   ├── company_summary.py     ← Resumen ejecutivo de empresa (IA)
│   ├── email_generator.py     ← Correo comercial personalizado (IA)
│   └── proposal_generator.py  ← Propuesta comercial estructurada (IA)
│
├── exporters/
│   ├── excel_exporter.py      ← leads.xlsx con formato y colores
│   └── pdf_exporter.py        ← Propuestas PDF por empresa
│
├── database/
│   └── sqlite_manager.py      ← CRUD SQLite (sin ORM)
│
├── utils/
│   ├── logger.py              ← Configuración Loguru
│   └── helpers.py             ← Funciones utilitarias
│
└── tests/
    ├── test_discovery.py
    ├── test_website_scraper.py
    ├── test_signal_detector.py
    ├── test_pain_detector.py
    ├── test_scoring.py
    └── test_recommendation_engine.py
```

---

## Flujo de datos

```
Usuario
  │
  ▼
[Discovery] Google Maps API
  │ companies[]
  ▼
[Website Scraper] requests + BeautifulSoup
  │ WebsiteData
  ▼
[Tech Detector]                [Signal Detector]
  │ technologies[]               │ signals[]
  └─────────────┬────────────────┘
                ▼
          [Pain Detector]
                │ pain_points[]
                ▼
         [Scoring Engine]
                │ score + classification
                ▼
      [Recommendation Engine]
                │ recommended_services[]
                ▼
          [SQLite DB]
          /           \
[Excel Exporter]   [AI Pipeline]
 leads.xlsx        company_summary
                   email_generator
                   proposal_generator
                        │
                   [PDF Exporter]
                   propuesta_*.pdf
```

---

## Scoring

El score (0–100) se calcula con reglas determinísticas:

| Factor | Puntos |
|---|---|
| Sitio web activo | +10 |
| Correo corporativo | +15 |
| Plataforma ecommerce (WooCommerce, Shopify) | +18 |
| Múltiples sucursales detectadas | +15 |
| Publicación de vacantes | +12 |
| Señales de crecimiento | +12 |
| Redes sociales (múltiples) | +10 |
| Analytics configurado | +8 |
| Blog/noticias | +8 |
| Dolores HIGH (por cada uno) | +8 |
| Dolores MEDIUM (por cada uno) | +4 |
| Sin sitio web | -10 |
| Solo correo personal | -5 |
| Sitio desactualizado | -5 |

**Clasificación:**
- 🔴 **HOT**: score ≥ 65
- 🟠 **WARM**: score ≥ 35
- 🔵 **COLD**: score < 35

---

## Roadmap futuro

### v1.1
- [ ] Interfaz web con FastAPI + React
- [ ] Búsqueda masiva multi-rubro/multi-ciudad
- [ ] Integración con LinkedIn para datos de contacto
- [ ] Detección de nombre del contador/dueño desde LinkedIn

### v1.2
- [ ] CRM básico: estados de leads (contactado, propuesta enviada, cliente)
- [ ] Tracking de correos enviados
- [ ] Dashboard con métricas de conversión

### v1.3
- [ ] Integración con SII para verificar actividades económicas
- [ ] Scoring por historial de rut (morosidad SII)
- [ ] Alertas automáticas de leads HOT nuevos

### v2.0
- [ ] Multi-usuario / multi-asesoría
- [ ] Automatización de envío de correos
- [ ] Integración con WhatsApp Business API
- [ ] Reportes semanales automáticos

---

## Filosofía del proyecto

> **Python First** — Toda la lógica de negocio en Python puro (reglas + heurísticas).
> La IA se usa solo para generar texto (correos, propuestas, resúmenes).

- Rapidez sobre perfección
- Simplicidad sobre escalabilidad
- Valor comercial demostrable desde el día 1
- Un solo archivo por responsabilidad
- SQLite sobre PostgreSQL (para MVP)
- Sin frameworks pesados innecesarios

---

## Licencia

MIT — Úsalo libremente para tu asesoría contable.

---

*Desarrollado como MVP en menos de 30 días · Python Leads 360 v1.0*
