import logging
import os
from collections import Counter
from functools import partial

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from backend.database import utc_now_sqlite
from backend.services import save_articles_batch, save_collection_run
from scraper.sources.news import fetch_huggingface_papers, fetch_pytorch_kr
from scraper.sources.vision import fetch_cvpr_papers, fetch_eccv_papers, fetch_iccv_papers
from scraper.summarizer import pick_top_article, summarize_articles

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SOURCE_LIMITS = {
    "cvpr": 1,
    "iccv": 1,
    "eccv": 1,
    "huggingface": 2,
    "pytorch_kr": 5,
}

SOURCE_FETCHERS = {
    "cvpr": partial(fetch_cvpr_papers, limit=SOURCE_LIMITS["cvpr"]),
    "iccv": partial(fetch_iccv_papers, limit=SOURCE_LIMITS["iccv"]),
    "eccv": partial(fetch_eccv_papers, limit=SOURCE_LIMITS["eccv"]),
    "huggingface": partial(fetch_huggingface_papers, limit=SOURCE_LIMITS["huggingface"]),
    "pytorch_kr": partial(fetch_pytorch_kr, limit=SOURCE_LIMITS["pytorch_kr"]),
}

"""


def collect_and_save() -> dict:
    started_at = utc_now_sqlite()
    log.info("수집을 시작합니다.")

    raw_articles = []
    source_results = _empty_source_results()
    fetch_errors: list[str] = []

    for source, fetcher in SOURCE_FETCHERS.items():
        try:
            articles = fetcher()
            raw_articles.extend(articles)
            source_results[source]["fetched"] = len(articles)
            log.info("%s 수집 완료: %s건", source, len(articles))
        except Exception as exc:
            source_results[source]["error"] = str(exc)
            fetch_errors.append(f"{source}: {exc}")
            log.exception("%s 수집 실패", source)

    if not raw_articles:
        error_summary = "; ".join(fetch_errors) if fetch_errors else "수집된 글이 없습니다."
        return _finalize_run(
            status="failed",
            started_at=started_at,
            saved_count=0,
            source_results=source_results,
            error_summary=error_summary,
            log_level="warning",
        )

    log.info("Gemini 요약을 시작합니다. 대상: %s건", len(raw_articles))
    try:
        summarized = summarize_articles(raw_articles)
        summarized = pick_top_article(summarized)
    except Exception as exc:
        return _finalize_run(
            status="failed",
            started_at=started_at,
            saved_count=0,
            source_results=source_results,
            error_summary=f"요약 실패: {exc}",
            log_level="error",
        )

    try:
        saved_count = save_articles_batch(summarized)
    except Exception as exc:
        return _finalize_run(
            status="failed",
            started_at=started_at,
            saved_count=0,
            source_results=source_results,
            error_summary=f"저장 실패: {exc}",
            log_level="error",
        )

    for source, count in Counter(article["source"] for article in summarized).items():
        source_results[source]["saved"] = count

    status = "partial" if fetch_errors else "success"
    error_summary = "; ".join(fetch_errors) if fetch_errors else None
    return _finalize_run(
        status=status,
        started_at=started_at,
        saved_count=saved_count,
        source_results=source_results,
        error_summary=error_summary,
        log_level="info",
    )


def start_scheduler() -> BackgroundScheduler:
    hour1 = int(os.getenv("COLLECT_HOUR_1", "8"))
    hour2 = int(os.getenv("COLLECT_HOUR_2", "20"))

    scheduler = BackgroundScheduler()
    scheduler.add_job(collect_and_save, "cron", hour=hour1, minute=0, id="collect_morning")
    scheduler.add_job(collect_and_save, "cron", hour=hour2, minute=0, id="collect_evening")
    scheduler.start()
    log.info("스케줄러를 시작합니다. 실행 시각: %s시, %s시", hour1, hour2)
    return scheduler


def _empty_source_results() -> dict:
    return {
        source: {"fetched": 0, "saved": 0, "error": None}
        for source in SOURCE_FETCHERS
    }


def _finalize_run(
    *,
    status: str,
    started_at: str,
    saved_count: int,
    source_results: dict,
    error_summary: str | None,
    log_level: str,
) -> dict:
    finished_at = utc_now_sqlite()
    save_collection_run(
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        saved_count=saved_count,
        source_results=source_results,
        error_summary=error_summary,
    )

    getattr(log, log_level)(
        "수집 실행 완료: status=%s saved=%s error=%s",
        status,
        saved_count,
        error_summary or "없음",
    )

    return {
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "saved_count": saved_count,
        "sources": source_results,
        "error_summary": error_summary,
    }
"""


def collect_and_save() -> dict:
    started_at = utc_now_sqlite()
    log.info("Collection run started.")

    raw_articles = []
    source_results = _empty_source_results()
    fetch_errors: list[str] = []

    for source, fetcher in SOURCE_FETCHERS.items():
        try:
            articles = fetcher()
            raw_articles.extend(articles)
            source_results[source]["fetched"] = len(articles)
            log.info("%s fetch completed: %s articles", source, len(articles))
        except Exception as exc:
            source_results[source]["error"] = str(exc)
            fetch_errors.append(f"{source}: {exc}")
            log.exception("%s fetch failed", source)

    if not raw_articles:
        error_summary = "; ".join(fetch_errors) if fetch_errors else "No articles were collected."
        return _finalize_run(
            status="failed",
            started_at=started_at,
            saved_count=0,
            source_results=source_results,
            error_summary=error_summary,
            log_level="warning",
        )

    log.info("Summarization started for %s articles", len(raw_articles))
    try:
        summarized = summarize_articles(raw_articles)
        summarized = pick_top_article(summarized)
    except Exception as exc:
        return _finalize_run(
            status="failed",
            started_at=started_at,
            saved_count=0,
            source_results=source_results,
            error_summary=f"Summarization failed: {exc}",
            log_level="error",
        )

    try:
        saved_count = save_articles_batch(summarized)
    except Exception as exc:
        return _finalize_run(
            status="failed",
            started_at=started_at,
            saved_count=0,
            source_results=source_results,
            error_summary=f"Persistence failed: {exc}",
            log_level="error",
        )

    for source, count in Counter(article["source"] for article in summarized).items():
        source_results[source]["saved"] = count

    status = "partial" if fetch_errors else "success"
    error_summary = "; ".join(fetch_errors) if fetch_errors else None
    return _finalize_run(
        status=status,
        started_at=started_at,
        saved_count=saved_count,
        source_results=source_results,
        error_summary=error_summary,
        log_level="info",
    )


def start_scheduler() -> BackgroundScheduler:
    hour1 = int(os.getenv("COLLECT_HOUR_1", "8"))
    hour2 = int(os.getenv("COLLECT_HOUR_2", "20"))

    scheduler = BackgroundScheduler()
    scheduler.add_job(collect_and_save, "cron", hour=hour1, minute=0, id="collect_morning")
    scheduler.add_job(collect_and_save, "cron", hour=hour2, minute=0, id="collect_evening")
    scheduler.start()
    log.info("Scheduler started. Run hours: %s and %s", hour1, hour2)
    return scheduler


def _empty_source_results() -> dict:
    return {
        source: {"fetched": 0, "saved": 0, "error": None}
        for source in SOURCE_FETCHERS
    }


def _finalize_run(
    *,
    status: str,
    started_at: str,
    saved_count: int,
    source_results: dict,
    error_summary: str | None,
    log_level: str,
) -> dict:
    finished_at = utc_now_sqlite()
    save_collection_run(
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        saved_count=saved_count,
        source_results=source_results,
        error_summary=error_summary,
    )

    getattr(log, log_level)(
        "Collection run finished: status=%s saved=%s error=%s",
        status,
        saved_count,
        error_summary or "none",
    )

    return {
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "saved_count": saved_count,
        "sources": source_results,
        "error_summary": error_summary,
    }
