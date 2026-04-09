import os
import google.generativeai as genai
from scraper.types import RawArticle

SUMMARIZE_PROMPT = """다음 내용을 한국어로 3-4문장으로 요약해주세요.
원문에 없는 내용은 절대 추가하지 마세요.

제목: {title}
내용: {text}

요약:"""

TOP_PICK_PROMPT = """다음 글들 중 AI/개발 분야에서 오늘 가장 중요하고 주목할 만한 것을 하나 골라주세요.
숫자만 답해주세요 (예: 1).

{items}"""


def _get_model() -> genai.GenerativeModel:
    api_key = os.environ.get("GEMINI_API_KEY", "test-key")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


def summarize_articles(raw_articles: list[RawArticle]) -> list[dict]:
    model = _get_model()
    results = []
    for article in raw_articles:
        prompt = SUMMARIZE_PROMPT.format(title=article.title, text=article.raw_text[:2000])
        response = model.generate_content(prompt)
        results.append(
            {
                "title": article.title,
                "summary_ko": response.text.strip(),
                "source_url": article.source_url,
                "source": article.source,
                "is_top_pick": False,
            }
        )
    return results


def pick_top_article(articles: list[dict]) -> list[dict]:
    if not articles:
        return articles
    model = _get_model()
    items = "\n".join(f"{i+1}. [{a['source'].upper()}] {a['title']}" for i, a in enumerate(articles))
    prompt = TOP_PICK_PROMPT.format(items=items)
    response = model.generate_content(prompt)
    try:
        idx = int(response.text.strip()) - 1
        idx = max(0, min(idx, len(articles) - 1))
    except ValueError:
        idx = 0
    articles[idx]["is_top_pick"] = True
    return articles
