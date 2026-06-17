"""
database/sqlite_manager.py - Gestor SQLite para Python Leads 360

Tablas:
  companies      → empresas descubiertas
  analysis       → resultado del análisis web
  signals        → señales detectadas por empresa
  pain_points    → dolores detectados por empresa
  recommendations → servicios recomendados por empresa
"""
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from config import DATABASE_PATH
from utils.logger import logger


# ── Esquema ──────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    website     TEXT,
    phone       TEXT,
    address     TEXT,
    category    TEXT,
    city        TEXT,
    keyword     TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    UNIQUE(name, city)
);

CREATE TABLE IF NOT EXISTS analysis (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL REFERENCES companies(id),
    title           TEXT,
    meta_description TEXT,
    h1              TEXT,
    h2_list         TEXT,   -- JSON array
    emails          TEXT,   -- JSON array
    phones          TEXT,   -- JSON array
    social_links    TEXT,   -- JSON object
    copyright_year  TEXT,
    technologies    TEXT,   -- JSON array
    raw_text_snippet TEXT,
    scrape_ok       INTEGER DEFAULT 1,
    scrape_error    TEXT,
    scraped_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS signals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL REFERENCES companies(id),
    signal      TEXT NOT NULL,
    score       INTEGER DEFAULT 0,
    evidence    TEXT,
    detected_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pain_points (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL REFERENCES companies(id),
    pain        TEXT NOT NULL,
    severity    TEXT DEFAULT 'medium',  -- low / medium / high
    evidence    TEXT,
    detected_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL REFERENCES companies(id),
    service         TEXT NOT NULL,
    priority        INTEGER DEFAULT 1,
    rationale       TEXT,
    score           INTEGER DEFAULT 0,
    classification  TEXT DEFAULT 'COLD',
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ai_outputs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL REFERENCES companies(id),
    type        TEXT NOT NULL,  -- summary / email / proposal
    content     TEXT,
    generated_at TEXT DEFAULT (datetime('now'))
);
"""


# ── Contexto de conexión ────────────────────────────────────────────────────────

@contextmanager
def get_connection():
    """Context manager para conexiones SQLite."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"DB error: {e}")
        raise
    finally:
        conn.close()


# ── Inicialización ──────────────────────────────────────────────────────────────

def init_db() -> None:
    """Crea las tablas si no existen."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA)
    logger.debug("Base de datos inicializada correctamente")


# ── CRUD Companies ──────────────────────────────────────────────────────────────

def upsert_company(company: dict) -> int:
    """
    Inserta o actualiza una empresa. Retorna el ID.
    Compatible con todas las versiones de SQLite (no usa RETURNING).
    """
    insert_sql = """
    INSERT OR IGNORE INTO companies (name, website, phone, address, category, city, keyword)
    VALUES (:name, :website, :phone, :address, :category, :city, :keyword)
    """
    update_sql = """
    UPDATE companies SET
        website  = :website,
        phone    = :phone,
        address  = :address,
        category = :category,
        keyword  = :keyword
    WHERE name = :name AND city = :city
    """
    select_sql = "SELECT id FROM companies WHERE name = :name AND city = :city"

    with get_connection() as conn:
        cursor = conn.execute(insert_sql, company)
        if cursor.lastrowid and cursor.lastrowid > 0:
            # Fila nueva insertada
            return cursor.lastrowid
        # Empresa ya existía: actualizar y obtener ID
        conn.execute(update_sql, company)
        row = conn.execute(select_sql, company).fetchone()
        return row["id"] if row else 0


def get_companies(city: str | None = None, keyword: str | None = None) -> list[dict]:
    """Retorna lista de empresas con filtros opcionales."""
    sql = "SELECT * FROM companies WHERE 1=1"
    params: list = []
    if city:
        sql += " AND city = ?"
        params.append(city)
    if keyword:
        sql += " AND keyword = ?"
        params.append(keyword)
    sql += " ORDER BY id"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_company_by_id(company_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        return dict(row) if row else None


# ── CRUD Analysis ───────────────────────────────────────────────────────────────

def save_analysis(company_id: int, data: dict) -> None:
    """Guarda el análisis web de una empresa."""
    # Serializar listas/dicts a JSON
    sql = """
    INSERT INTO analysis
        (company_id, title, meta_description, h1, h2_list, emails, phones,
         social_links, copyright_year, technologies, raw_text_snippet, scrape_ok, scrape_error)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    with get_connection() as conn:
        conn.execute(sql, (
            company_id,
            data.get("title", ""),
            data.get("meta_description", ""),
            data.get("h1", ""),
            json.dumps(data.get("h2_list", []), ensure_ascii=False),
            json.dumps(data.get("emails", []), ensure_ascii=False),
            json.dumps(data.get("phones", []), ensure_ascii=False),
            json.dumps(data.get("social_links", {}), ensure_ascii=False),
            data.get("copyright_year", ""),
            json.dumps(data.get("technologies", []), ensure_ascii=False),
            data.get("raw_text_snippet", ""),
            1 if data.get("scrape_ok", True) else 0,
            data.get("scrape_error", ""),
        ))


def get_analysis(company_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analysis WHERE company_id=? ORDER BY id DESC LIMIT 1",
            (company_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        for field in ("h2_list", "emails", "phones", "technologies"):
            d[field] = json.loads(d.get(field) or "[]")
        d["social_links"] = json.loads(d.get("social_links") or "{}")
        return d


# ── CRUD Signals ────────────────────────────────────────────────────────────────

def save_signals(company_id: int, signals: list[dict]) -> None:
    """Guarda señales detectadas."""
    sql = "INSERT INTO signals (company_id, signal, score, evidence) VALUES (?,?,?,?)"
    with get_connection() as conn:
        conn.execute("DELETE FROM signals WHERE company_id=?", (company_id,))
        conn.executemany(sql, [
            (company_id, s["signal"], s.get("score", 0), s.get("evidence", ""))
            for s in signals
        ])


def get_signals(company_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM signals WHERE company_id=? ORDER BY score DESC", (company_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── CRUD Pain Points ────────────────────────────────────────────────────────────

def save_pain_points(company_id: int, pains: list[dict]) -> None:
    sql = "INSERT INTO pain_points (company_id, pain, severity, evidence) VALUES (?,?,?,?)"
    with get_connection() as conn:
        conn.execute("DELETE FROM pain_points WHERE company_id=?", (company_id,))
        conn.executemany(sql, [
            (company_id, p["pain"], p.get("severity", "medium"), p.get("evidence", ""))
            for p in pains
        ])


def get_pain_points(company_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM pain_points WHERE company_id=?", (company_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── CRUD Recommendations ────────────────────────────────────────────────────────

def save_recommendations(company_id: int, recs: list[dict], score: int, classification: str) -> None:
    sql = """
    INSERT INTO recommendations (company_id, service, priority, rationale, score, classification)
    VALUES (?,?,?,?,?,?)
    """
    with get_connection() as conn:
        conn.execute("DELETE FROM recommendations WHERE company_id=?", (company_id,))
        for i, r in enumerate(recs, 1):
            conn.execute(sql, (
                company_id, r["service"], i, r.get("rationale", ""), score, classification
            ))


def get_recommendations(company_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM recommendations WHERE company_id=? ORDER BY priority", (company_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── CRUD AI Outputs ─────────────────────────────────────────────────────────────

def save_ai_output(company_id: int, output_type: str, content: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO ai_outputs (company_id, type, content) VALUES (?,?,?)",
            (company_id, output_type, content)
        )


def get_ai_output(company_id: int, output_type: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT content FROM ai_outputs WHERE company_id=? AND type=? ORDER BY id DESC LIMIT 1",
            (company_id, output_type)
        ).fetchone()
        return row["content"] if row else None


# ── Vista consolidada para exportación ─────────────────────────────────────────

def get_full_leads(city: str | None = None, keyword: str | None = None) -> list[dict]:
    """
    Retorna vista consolidada de leads con toda la información para exportar.
    """
    companies = get_companies(city=city, keyword=keyword)
    leads = []
    for c in companies:
        cid = c["id"]
        analysis = get_analysis(cid) or {}
        signals  = get_signals(cid)
        pains    = get_pain_points(cid)
        recs     = get_recommendations(cid)

        leads.append({
            "company":              c,
            "analysis":             analysis,
            "signals":              signals,
            "pain_points":          pains,
            "recommendations":      recs,
            "score":                recs[0]["score"] if recs else 0,
            "classification":       recs[0]["classification"] if recs else "COLD",
        })
    return leads
