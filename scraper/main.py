import os
import logging
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from scraper.sources.github import fetch_github_trending
from scraper.sources.hackernews import fetch_hackernews
from scraper.sources.arxiv import fetch_arxiv
from scraper.sources.papers import fetch_papers_with_code
from scraper.summarizer import summarize_articles, pick_top_article

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def collect_and_save() -> None:
    log.info("수집 시작...")
    raw_articles = []

    for fetcher in [fetch_github_trending, fetch_hackernews, fetch_arxiv, fetch_papers_with_code]:
        try:
            articles = fetcher()
            raw_articles.extend(articles)
            log.info(f"{fetcher.__name__}: {len(articles)}개 수집")
        except Exception as e:
            log.error(f"{fetcher.__name__} 실패: {e}")

    if not raw_articles:
        log.warning("수집된 글이 없습니다.")
        return

    log.info(f"Gemini 요약 시작 ({len(raw_articles)}개)...")
    try:
        summarized = summarize_articles(raw_articles)
        summarized = pick_top_article(summarized)
    except Exception as e:
        log.error(f"요약 실패: {e}")
        return

    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/collect",
            json={"articles": summarized},
            timeout=30,
        )
        response.raise_for_status()
        log.info(f"저장 완료: {response.json()['saved']}개")
    except Exception as e:
        log.error(f"저장 실패: {e}")


def start_scheduler() -> BackgroundScheduler:
    hour1 = int(os.getenv("COLLECT_HOUR_1", "8"))
    hour2 = int(os.getenv("COLLECT_HOUR_2", "20"))

    scheduler = BackgroundScheduler()
    scheduler.add_job(collect_and_save, "cron", hour=hour1, minute=0, id="collect_morning")
    scheduler.add_job(collect_and_save, "cron", hour=hour2, minute=0, id="collect_evening")
    scheduler.start()
    log.info(f"스케줄러 시작: {hour1}시, {hour2}시 수집")
    return scheduler
