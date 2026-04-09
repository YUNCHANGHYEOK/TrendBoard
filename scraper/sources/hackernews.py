import httpx
from scraper.types import RawArticle

HN_API = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=20"


def fetch_hackernews(limit: int = 15) -> list[RawArticle]:
    response = httpx.get(HN_API, timeout=30)
    response.raise_for_status()
    hits = response.json().get("hits", [])

    articles: list[RawArticle] = []
    for hit in hits[:limit]:
        title = hit.get("title", "")
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        points = hit.get("points", 0)
        comments = hit.get("num_comments", 0)

        articles.append(
            RawArticle(
                title=title,
                source_url=url,
                source="hn",
                raw_text=f"{title}\n추천수: {points}, 댓글: {comments}",
            )
        )
    return articles
