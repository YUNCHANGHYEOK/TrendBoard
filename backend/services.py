from collections import OrderedDict

from backend.database import (
    get_latest_collection_run,
    init_db,
    record_collection_run,
    upsert_articles,
    utc_now_sqlite,
)


def save_articles_batch(articles: list[dict]) -> int:
    init_db()
    top_pick_count = sum(1 for article in articles if article.get("is_top_pick"))
    if top_pick_count > 1:
        raise ValueError("Only one top pick article is allowed per batch.")

    deduped_by_key: OrderedDict[tuple[str, str], dict] = OrderedDict()
    for article in articles:
        key = (article["source"], article["source_url"])
        deduped_by_key[key] = {
            "title": article["title"],
            "summary_ko": article["summary_ko"],
            "source_url": article["source_url"],
            "source": article["source"],
            "is_top_pick": bool(article.get("is_top_pick")),
        }

    return upsert_articles(list(deduped_by_key.values()), collected_at=utc_now_sqlite())


def save_collection_run(
    *,
    status: str,
    started_at: str,
    finished_at: str,
    saved_count: int,
    source_results: dict,
    error_summary: str | None,
) -> int:
    init_db()
    return record_collection_run(
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        saved_count=saved_count,
        source_results=source_results,
        error_summary=error_summary,
    )


def get_latest_collection_status() -> dict | None:
    init_db()
    return get_latest_collection_run()
