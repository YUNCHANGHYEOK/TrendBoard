import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "trendboard.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary_ko TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source TEXT NOT NULL,
                is_top_pick INTEGER DEFAULT 0,
                collected_at DATETIME NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def insert_articles(articles: list[dict]) -> int:
    with get_conn() as conn:
        conn.executemany(
            """
            INSERT INTO articles (title, summary_ko, source_url, source, is_top_pick)
            VALUES (:title, :summary_ko, :source_url, :source, :is_top_pick)
            """,
            articles,
        )
        conn.commit()
    return len(articles)


def get_articles(source_group: str | None = None, limit: int = 50) -> list[dict]:
    source_filter = {
        "ai": ("arxiv", "papers"),
        "dev": ("github", "hn"),
    }
    with get_conn() as conn:
        if source_group and source_group in source_filter:
            placeholders = ",".join("?" * len(source_filter[source_group]))
            rows = conn.execute(
                f"SELECT * FROM articles WHERE source IN ({placeholders}) ORDER BY collected_at DESC LIMIT ?",
                (*source_filter[source_group], limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM articles ORDER BY collected_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(row) for row in rows]
