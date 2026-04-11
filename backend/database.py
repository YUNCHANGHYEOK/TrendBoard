import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "trendboard.db"
FALLBACK_DB_PATH = DB_PATH.with_name("trendboard.runtime.db")
DB_VERSION = 1

DEFAULT_SQLITE_JOURNAL_MODE = "MEMORY" if os.name == "nt" else "DELETE"
DEFAULT_SQLITE_TEMP_STORE = "MEMORY" if os.name == "nt" else "DEFAULT"
DEFAULT_SQLITE_BUSY_TIMEOUT_MS = 5000
ACTIVE_DB_PATH: Path | None = None


def utc_now_sqlite() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def to_api_datetime(value: str | None) -> str | None:
    if not value:
        return None
    if "T" in value:
        return value if value.endswith("Z") else f"{value}Z"
    return value.replace(" ", "T") + "Z"


def _configure_connection(conn: sqlite3.Connection) -> sqlite3.Connection:
    journal_mode = os.getenv("SQLITE_JOURNAL_MODE", DEFAULT_SQLITE_JOURNAL_MODE).strip().upper()
    temp_store = os.getenv("SQLITE_TEMP_STORE", DEFAULT_SQLITE_TEMP_STORE).strip().upper()
    busy_timeout = int(
        os.getenv("SQLITE_BUSY_TIMEOUT_MS", str(DEFAULT_SQLITE_BUSY_TIMEOUT_MS)).strip()
    )

    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {busy_timeout}")

    if journal_mode:
        conn.execute(f"PRAGMA journal_mode = {journal_mode}")
    if temp_store and temp_store != "DEFAULT":
        conn.execute(f"PRAGMA temp_store = {temp_store}")

    return conn


def _current_db_path() -> Path:
    return ACTIVE_DB_PATH or DB_PATH


def _activate_fallback_db() -> bool:
    global ACTIVE_DB_PATH
    if ACTIVE_DB_PATH is not None:
        return False

    ACTIVE_DB_PATH = FALLBACK_DB_PATH
    ACTIVE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return True


def _recreate_empty_db_file() -> bool:
    db_path = _current_db_path()
    if not db_path.exists():
        return False
    if db_path.stat().st_size != 0:
        return False

    try:
        db_path.unlink()
    except PermissionError:
        return _activate_fallback_db()
    return True


def get_conn() -> sqlite3.Connection:
    db_path = _current_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return _configure_connection(conn)


def _init_db_once() -> None:
    conn = get_conn()
    try:
        with conn:
            current_version = conn.execute("PRAGMA user_version").fetchone()[0]
            if current_version < DB_VERSION:
                _migrate_articles_table(conn)
                _create_collection_runs_table(conn)
                conn.execute(f"PRAGMA user_version = {DB_VERSION}")
            else:
                _create_articles_table(conn)
                _create_article_indexes(conn)
                _create_collection_runs_table(conn)
    finally:
        conn.close()


def init_db() -> None:
    _recreate_empty_db_file()
    try:
        _init_db_once()
    except sqlite3.OperationalError:
        if not _recreate_empty_db_file():
            raise
        _init_db_once()


def upsert_articles(articles: list[dict], collected_at: str | None = None) -> int:
    if not articles:
        return 0

    timestamp = collected_at or utc_now_sqlite()
    top_pick_count = sum(1 for article in articles if article.get("is_top_pick"))
    if top_pick_count > 1:
        raise ValueError("Only one top pick article is allowed per batch.")

    normalized_articles = []
    for article in articles:
        normalized_articles.append(
            {
                "title": article["title"],
                "summary_ko": article["summary_ko"],
                "source_url": article["source_url"],
                "source": article["source"],
                "is_top_pick": 1 if article.get("is_top_pick") else 0,
                "collected_at": timestamp,
            }
        )

    conn = get_conn()
    try:
        with conn:
            conn.execute("UPDATE articles SET is_top_pick = 0")
            conn.executemany(
                """
                INSERT INTO articles (title, summary_ko, source_url, source, is_top_pick, collected_at)
                VALUES (:title, :summary_ko, :source_url, :source, :is_top_pick, :collected_at)
                ON CONFLICT(source, source_url) DO UPDATE SET
                    title = excluded.title,
                    summary_ko = excluded.summary_ko,
                    is_top_pick = excluded.is_top_pick,
                    collected_at = excluded.collected_at
                """,
                normalized_articles,
            )
        return len(normalized_articles)
    finally:
        conn.close()


def get_articles(source_group: str | None = None, limit: int = 50) -> list[dict]:
    source_filter = {
        "papers": ("cvpr", "iccv", "eccv", "arxiv", "papers", "huggingface"),
        "news": ("pytorch_kr", "hn_ai", "hn"),
    }
    conn = get_conn()
    try:
        if source_group and source_group in source_filter:
            placeholders = ",".join("?" * len(source_filter[source_group]))
            rows = conn.execute(
                f"""
                SELECT * FROM articles
                WHERE source IN ({placeholders})
                ORDER BY collected_at DESC, id DESC
                LIMIT ?
                """,
                (*source_filter[source_group], limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM articles
                ORDER BY collected_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def record_collection_run(
    *,
    status: str,
    started_at: str,
    finished_at: str,
    saved_count: int,
    source_results: dict,
    error_summary: str | None,
) -> int:
    conn = get_conn()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO collection_runs (
                    status,
                    started_at,
                    finished_at,
                    saved_count,
                    source_results,
                    error_summary
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    status,
                    started_at,
                    finished_at,
                    saved_count,
                    json.dumps(source_results, ensure_ascii=False),
                    error_summary,
                ),
            )
        return cursor.lastrowid
    finally:
        conn.close()


def get_latest_collection_run() -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM collection_runs
            ORDER BY finished_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    data = dict(row)
    data.pop("id", None)
    data.pop("created_at", None)
    data["started_at"] = to_api_datetime(data["started_at"])
    data["finished_at"] = to_api_datetime(data["finished_at"])
    data["sources"] = json.loads(data.pop("source_results") or "{}")
    return data


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _create_articles_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary_ko TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source TEXT NOT NULL,
            is_top_pick INTEGER NOT NULL DEFAULT 0 CHECK (is_top_pick IN (0, 1)),
            collected_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(source, source_url)
        )
        """
    )
    _create_article_indexes(conn)


def _create_article_indexes(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_articles_collected_at ON articles(collected_at DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_articles_is_top_pick ON articles(is_top_pick)"
    )


def _create_collection_runs_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS collection_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            saved_count INTEGER NOT NULL DEFAULT 0,
            source_results TEXT NOT NULL DEFAULT '{}',
            error_summary TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_collection_runs_finished_at ON collection_runs(finished_at DESC)"
    )


def _migrate_articles_table(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "articles"):
        _create_articles_table(conn)
        return

    conn.execute("ALTER TABLE articles RENAME TO articles_legacy")
    _create_articles_table(conn)
    conn.execute(
        """
        INSERT INTO articles (title, summary_ko, source_url, source, is_top_pick, collected_at)
        SELECT title, summary_ko, source_url, source, is_top_pick, collected_at
        FROM (
            SELECT
                id,
                title,
                summary_ko,
                source_url,
                source,
                is_top_pick,
                collected_at,
                ROW_NUMBER() OVER (
                    PARTITION BY source, source_url
                    ORDER BY collected_at DESC, id DESC
                ) AS row_num
            FROM articles_legacy
        )
        WHERE row_num = 1
        """
    )
    _normalize_top_pick(conn)
    conn.execute("DROP TABLE articles_legacy")


def _normalize_top_pick(conn: sqlite3.Connection) -> None:
    top_pick_row = conn.execute(
        """
        SELECT id
        FROM articles
        WHERE is_top_pick = 1
        ORDER BY collected_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    conn.execute("UPDATE articles SET is_top_pick = 0")
    if top_pick_row is not None:
        conn.execute(
            "UPDATE articles SET is_top_pick = 1 WHERE id = ?",
            (top_pick_row["id"],),
        )
