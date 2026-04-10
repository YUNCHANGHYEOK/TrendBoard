"""AI 뉴스·커뮤니티 소스 수집기

수집 대상
- pytorch_kr : discuss.pytorch.kr (Discourse API)
- hn_ai      : Hacker News AI/ML 상위 스토리 (Algolia 검색)
- huggingface: HuggingFace Daily Papers
"""

import httpx

from scraper.types import RawArticle

# ── 1. discuss.pytorch.kr (Discourse) ────────────────────────────────────────

PYTORCH_KR_LATEST = "https://discuss.pytorch.kr/latest.json?order=activity"
PYTORCH_KR_TOPIC_URL = "https://discuss.pytorch.kr/t/{slug}/{id}"


def fetch_pytorch_kr(limit: int = 5) -> list[RawArticle]:
    try:
        resp = httpx.get(PYTORCH_KR_LATEST, timeout=30)
        resp.raise_for_status()
    except Exception:
        return []

    topics = resp.json().get("topic_list", {}).get("topics", [])
    articles: list[RawArticle] = []

    for topic in topics:
        if topic.get("pinned") or topic.get("archived"):
            continue
        title = topic.get("title", "").strip()
        if not title:
            continue
        slug = topic.get("slug", "")
        topic_id = topic.get("id", "")
        url = PYTORCH_KR_TOPIC_URL.format(slug=slug, id=topic_id)
        excerpt = topic.get("excerpt", "") or ""
        posts_count = topic.get("posts_count", 0)
        views = topic.get("views", 0)

        raw_text = (
            f"커뮤니티: discuss.pytorch.kr\n"
            f"제목: {title}\n"
            f"댓글: {posts_count}개, 조회: {views}회"
        )
        if excerpt:
            raw_text += f"\n내용 미리보기: {excerpt}"

        articles.append(
            RawArticle(
                title=title,
                source_url=url,
                source="pytorch_kr",
                raw_text=raw_text,
            )
        )
        if len(articles) >= limit:
            break

    return articles


# ── 2. Hacker News AI/ML 필터 ─────────────────────────────────────────────────

HN_AI_SEARCH = (
    "https://hn.algolia.com/api/v1/search"
    "?query=AI+machine+learning+LLM&tags=story&hitsPerPage=30"
    "&numericFilters=points>10"
)


def fetch_hn_ai(limit: int = 5) -> list[RawArticle]:
    try:
        resp = httpx.get(HN_AI_SEARCH, timeout=30)
        resp.raise_for_status()
    except Exception:
        return []

    hits = resp.json().get("hits", [])
    AI_KEYWORDS = {
        "ai", "ml", "llm", "gpt", "model", "neural", "deep learning",
        "machine learning", "transformer", "diffusion", "openai", "anthropic",
        "gemini", "claude", "mistral", "llama", "pytorch", "tensorflow",
        "huggingface", "agent", "rag", "embedding", "inference",
    }

    articles: list[RawArticle] = []
    for hit in hits:
        title = hit.get("title", "").strip()
        if not title:
            continue
        lower = title.lower()
        if not any(kw in lower for kw in AI_KEYWORDS):
            continue

        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        points = hit.get("points", 0)
        comments = hit.get("num_comments", 0)

        articles.append(
            RawArticle(
                title=title,
                source_url=url,
                source="hn_ai",
                raw_text=f"{title}\n추천수: {points}, 댓글: {comments}",
            )
        )
        if len(articles) >= limit:
            break

    return articles


# ── 3. HuggingFace Daily Papers ───────────────────────────────────────────────

HF_DAILY_PAPERS_API = "https://huggingface.co/api/daily_papers"


def fetch_huggingface_papers(limit: int = 5) -> list[RawArticle]:
    try:
        resp = httpx.get(HF_DAILY_PAPERS_API, timeout=30)
        resp.raise_for_status()
    except Exception:
        return []

    results = resp.json()
    articles: list[RawArticle] = []

    for item in results:
        paper = item.get("paper", {})
        paper_id = paper.get("id", "")
        if not paper_id:
            continue
        title = paper.get("title", "").strip()
        if not title:
            continue
        abstract = paper.get("summary", "").replace("\n", " ").strip()
        url = f"https://huggingface.co/papers/{paper_id}"

        articles.append(
            RawArticle(
                title=title,
                source_url=url,
                source="huggingface",
                raw_text=f"{title}\n{abstract}",
            )
        )
        if len(articles) >= limit:
            break

    return articles
