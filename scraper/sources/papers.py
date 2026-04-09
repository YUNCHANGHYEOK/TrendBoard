import httpx
from scraper.types import RawArticle

PAPERS_API = "https://paperswithcode.com/api/v1/papers/?ordering=-published&page_size=10"


def fetch_papers_with_code(limit: int = 10) -> list[RawArticle]:
    response = httpx.get(PAPERS_API, timeout=30)
    response.raise_for_status()
    results = response.json().get("results", [])

    articles: list[RawArticle] = []
    for item in results[:limit]:
        url = item.get("url_abs") or item.get("url_pdf")
        if not url:
            continue
        title = item.get("title", "").strip()
        abstract = item.get("abstract", "").replace("\n", " ").strip()

        articles.append(
            RawArticle(
                title=title,
                source_url=url,
                source="papers",
                raw_text=f"{title}\n{abstract}",
            )
        )
    return articles
