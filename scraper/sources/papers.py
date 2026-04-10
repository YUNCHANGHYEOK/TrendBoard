import httpx
from scraper.types import RawArticle

# paperswithcode.com API redirects to HuggingFace; use HF daily papers API instead.
HF_DAILY_PAPERS_API = "https://huggingface.co/api/daily_papers"


def fetch_papers_with_code(limit: int = 10) -> list[RawArticle]:
    response = httpx.get(HF_DAILY_PAPERS_API, timeout=30)
    response.raise_for_status()
    results = response.json()

    articles: list[RawArticle] = []
    for item in results[:limit]:
        paper = item.get("paper", {})
        paper_id = paper.get("id", "")
        if not paper_id:
            continue
        title = paper.get("title", "").strip()
        abstract = paper.get("summary", "").replace("\n", " ").strip()
        url = f"https://huggingface.co/papers/{paper_id}"

        articles.append(
            RawArticle(
                title=title,
                source_url=url,
                source="papers",
                raw_text=f"{title}\n{abstract}",
            )
        )
    return articles
