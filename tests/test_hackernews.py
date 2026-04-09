from unittest.mock import MagicMock, patch
from scraper.sources.hackernews import fetch_hackernews

SAMPLE_RESPONSE = {
    "hits": [
        {
            "title": "Show HN: I built an open-source LLM benchmark tool",
            "url": "https://example.com/llm-bench",
            "points": 342,
            "num_comments": 87,
        },
        {
            "title": "Ask HN: Best practices for RAG in production?",
            "url": None,
            "points": 210,
            "num_comments": 134,
            "objectID": "99999",
        },
    ]
}


def _mock_response(data: dict) -> MagicMock:
    m = MagicMock()
    m.json.return_value = data
    m.raise_for_status = MagicMock()
    return m


def test_fetch_returns_articles():
    with patch("scraper.sources.hackernews.httpx.get", return_value=_mock_response(SAMPLE_RESPONSE)):
        articles = fetch_hackernews()
    assert len(articles) == 2


def test_fetch_article_fields():
    with patch("scraper.sources.hackernews.httpx.get", return_value=_mock_response(SAMPLE_RESPONSE)):
        articles = fetch_hackernews()
    a = articles[0]
    assert a.title == "Show HN: I built an open-source LLM benchmark tool"
    assert a.source == "hn"
    assert a.source_url == "https://example.com/llm-bench"
    assert "342" in a.raw_text


def test_fetch_uses_hn_url_when_no_url():
    with patch("scraper.sources.hackernews.httpx.get", return_value=_mock_response(SAMPLE_RESPONSE)):
        articles = fetch_hackernews()
    a = articles[1]
    assert "news.ycombinator.com" in a.source_url
