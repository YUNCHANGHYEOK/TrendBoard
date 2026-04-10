import os
from typing import Iterable

import google.generativeai as genai
import httpx

from scraper.types import RawArticle

SUMMARY_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

DEV_SUMMARY_PROMPT = """You are writing a short Korean briefing for a tech dashboard.
Write 2-3 concise Korean sentences.
Keep repository and product names in English when natural.
Do not add facts that are not present in the source text.

Title: {title}
Source: {source}
Text:
{text}

Korean summary:"""

PAPER_SUMMARY_PROMPT = """You are translating and condensing a research abstract for a Korean dashboard.
Write 2-3 natural Korean sentences.
Do not mention the title, authors, affiliations, or conference name.
Translate only the abstract content.
Return only the Korean abstract summary.

Abstract:
{abstract}

Korean abstract summary:"""

TOP_PICK_PROMPT = """Choose the single most notable item for a Korean AI and developer dashboard.
Prioritize broad impact, novelty, and current relevance.
Return only the item number.

{items}"""

PAPER_SOURCES = {"cvpr", "iccv", "eccv", "arxiv", "papers"}

SOURCE_PRIORITY = {
    "cvpr": 5,
    "iccv": 5,
    "eccv": 5,
    "arxiv": 4,
    "papers": 4,
    "github": 3,
    "hn": 2,
}


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _clip_text(value: str, limit: int = 220) -> str:
    text = _clean_text(value)
    if len(text) <= limit:
        return text

    clipped = text[: limit - 1].rstrip(" ,.;:")
    return f"{clipped}..."


def _get_labeled_line(raw_text: str, label: str) -> str:
    prefix = f"{label}:"
    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return ""


def _paper_abstract_text(article: RawArticle) -> str:
    abstract = _get_labeled_line(article.raw_text, "Abstract")
    if abstract:
        return abstract

    lines = [line.strip() for line in article.raw_text.splitlines() if line.strip()]
    filtered_lines: list[str] = []
    for line in lines:
        if line == article.title:
            continue
        if line.startswith(("Conference:", "Title:", "Authors:", "Abstract:")):
            continue
        filtered_lines.append(line)

    return _clean_text(" ".join(filtered_lines))


def _generic_description(article: RawArticle) -> str:
    lines = [line.strip() for line in article.raw_text.splitlines() if line.strip()]
    filtered_lines: list[str] = []
    for line in lines:
        if line == article.title:
            continue
        if line.startswith(("Conference:", "Title:", "Authors:", "Abstract:")):
            continue
        filtered_lines.append(line)

    return _clean_text(" ".join(filtered_lines))


def _public_translate_enabled() -> bool:
    return os.getenv("PUBLIC_TRANSLATE_FALLBACK", "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }


def _chunk_text(value: str, limit: int = 1400) -> list[str]:
    words = value.split()
    if not words:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for word in words:
        extra = len(word) if not current else len(word) + 1
        if current and current_length + extra > limit:
            chunks.append(" ".join(current))
            current = [word]
            current_length = len(word)
            continue

        current.append(word)
        current_length += extra

    if current:
        chunks.append(" ".join(current))

    return chunks


def _translate_text_to_korean(text: str) -> str:
    if not text or not _public_translate_enabled():
        return ""

    translated_parts: list[str] = []
    for chunk in _chunk_text(text):
        response = httpx.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "en",
                "tl": "ko",
                "dt": "t",
                "q": chunk,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        translated = "".join(
            part[0]
            for part in data[0]
            if isinstance(part, list) and part and isinstance(part[0], str)
        )
        if translated:
            translated_parts.append(translated.strip())

    return _clean_text(" ".join(translated_parts))


def _get_model() -> genai.GenerativeModel:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(SUMMARY_MODEL_NAME)


def _extract_response_text(response: object) -> str:
    return _clean_text(getattr(response, "text", ""))


def _summary_prompt_for(article: RawArticle) -> str:
    if article.source in PAPER_SOURCES:
        abstract = _paper_abstract_text(article) or article.raw_text
        return PAPER_SUMMARY_PROMPT.format(abstract=_clip_text(abstract, limit=4000))

    return DEV_SUMMARY_PROMPT.format(
        title=article.title,
        source=article.source,
        text=_clip_text(article.raw_text, limit=4000),
    )


def _paper_fallback_summary(article: RawArticle) -> str:
    abstract = _paper_abstract_text(article)
    if abstract:
        try:
            translated = _translate_text_to_korean(abstract)
        except Exception:
            translated = ""

        if translated:
            return _clip_text(translated, limit=320)

        return _clip_text(abstract, limit=320)
    return "초록을 불러오지 못했습니다."


def _fallback_summary(article: RawArticle) -> str:
    if article.source == "github":
        description = _generic_description(article)
        if description:
            return " ".join(
                [
                    "GitHub Trending에서 포착된 저장소입니다.",
                    f"핵심은 {_clip_text(description, limit=220)}",
                ]
            )
        return "GitHub Trending에서 포착된 저장소입니다."

    description = _generic_description(article)
    if description:
        return " ".join(
            [
                f"{article.source.upper()}에서 수집한 항목입니다.",
                _clip_text(description, limit=220),
            ]
        )

    return f"{article.source.upper()}에서 수집한 항목입니다."


def summarize_articles(raw_articles: list[RawArticle]) -> list[dict]:
    if not raw_articles:
        return []

    try:
        model = _get_model()
    except Exception:
        model = None

    results: list[dict] = []
    for article in raw_articles:
        summary = ""
        if model is not None:
            try:
                response = model.generate_content(_summary_prompt_for(article))
                summary = _extract_response_text(response)
            except Exception:
                summary = ""

        if article.source in PAPER_SOURCES:
            summary_text = summary or _paper_fallback_summary(article)
        else:
            summary_text = summary or _fallback_summary(article)

        results.append(
            {
                "title": article.title,
                "summary_ko": summary_text,
                "source_url": article.source_url,
                "source": article.source,
                "is_top_pick": False,
            }
        )

    return results


def _fallback_top_pick_index(articles: Iterable[dict]) -> int:
    best_score = -1
    best_index = 0
    keywords = (
        "benchmark",
        "dataset",
        "diffusion",
        "segmentation",
        "multimodal",
        "3d",
        "video",
        "robot",
        "agent",
        "reasoning",
        "vision",
    )

    for index, article in enumerate(articles):
        title = article.get("title", "")
        summary = article.get("summary_ko", "")
        lowered = f"{title} {summary}".lower()
        score = SOURCE_PRIORITY.get(article.get("source", ""), 1) * 100
        score += min(len(summary), 120)
        score += sum(12 for keyword in keywords if keyword in lowered)
        score += max(0, 10 - index)
        if score > best_score:
            best_score = score
            best_index = index

    return best_index


def pick_top_article(articles: list[dict]) -> list[dict]:
    if not articles:
        return articles

    for article in articles:
        article["is_top_pick"] = False

    selected_index: int | None = None
    try:
        model = _get_model()
    except Exception:
        model = None

    if model is not None:
        items = "\n".join(
            f"{index + 1}. [{article['source'].upper()}] {article['title']}"
            for index, article in enumerate(articles)
        )
        try:
            response = model.generate_content(TOP_PICK_PROMPT.format(items=items))
            selected_index = int(_extract_response_text(response)) - 1
        except Exception:
            selected_index = None

    if selected_index is None or not 0 <= selected_index < len(articles):
        selected_index = _fallback_top_pick_index(articles)

    articles[selected_index]["is_top_pick"] = True
    return articles
