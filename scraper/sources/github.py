import httpx
from bs4 import BeautifulSoup
from scraper.types import RawArticle


def fetch_github_trending(limit: int = 10) -> list[RawArticle]:
    response = httpx.get(
        "https://github.com/trending",
        headers={"Accept": "text/html", "User-Agent": "Mozilla/5.0"},
        follow_redirects=True,
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    articles: list[RawArticle] = []
    for row in soup.select("article.Box-row")[:limit]:
        link_tag = row.select_one("h2 a")
        if not link_tag:
            continue
        repo_path = link_tag["href"].strip().strip("/")
        title = repo_path.replace(" ", "")  # "owner/repo"
        url = f"https://github.com/{repo_path}"

        desc_tag = row.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        articles.append(
            RawArticle(
                title=title,
                source_url=url,
                source="github",
                raw_text=f"{title}\n{description}",
            )
        )
    return articles
