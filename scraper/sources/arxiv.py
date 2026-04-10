import feedparser
import httpx
from scraper.types import RawArticle

ARXIV_FEEDS = [
    "https://rss.arxiv.org/rss/cs.AI",
    "https://rss.arxiv.org/rss/cs.LG",
]


def fetch_arxiv(limit_per_feed: int = 8) -> list[RawArticle]:
    articles: list[RawArticle] = []
    seen_urls: set[str] = set()

    for feed_url in ARXIV_FEEDS:
        # feedparser uses urllib which fails on Windows due to SSL cert issues.
        # Fetch the raw content via httpx (verify=False) and parse from bytes.
        response = httpx.get(feed_url, timeout=30, verify=False)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        for entry in feed.entries[:limit_per_feed]:
            url = getattr(entry, "link", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = getattr(entry, "title", "").replace("\n", " ").strip()
            abstract = getattr(entry, "summary", "").replace("\n", " ").strip()

            articles.append(
                RawArticle(
                    title=title,
                    source_url=url,
                    source="arxiv",
                    raw_text=f"{title}\n{abstract}",
                )
            )
    return articles
