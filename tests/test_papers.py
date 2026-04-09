from unittest.mock import MagicMock, patch
from scraper.sources.papers import fetch_papers_with_code

SAMPLE_RESPONSE = {
    "results": [
        {
            "title": "LoRA: Low-Rank Adaptation of Large Language Models",
            "abstract": "We propose a method to adapt large language models efficiently...",
            "url_abs": "https://arxiv.org/abs/2106.09685",
            "url_pdf": "https://arxiv.org/pdf/2106.09685",
        },
        {
            "title": "Mamba: Linear-Time Sequence Modeling",
            "abstract": "Foundation models based on attention suffer from quadratic complexity...",
            "url_abs": "https://arxiv.org/abs/2312.00752",
            "url_pdf": None,
        },
    ]
}


def _mock_response(data: dict) -> MagicMock:
    m = MagicMock()
    m.json.return_value = data
    m.raise_for_status = MagicMock()
    return m


def test_fetch_returns_articles():
    with patch("scraper.sources.papers.httpx.get", return_value=_mock_response(SAMPLE_RESPONSE)):
        articles = fetch_papers_with_code()
    assert len(articles) == 2


def test_fetch_article_fields():
    with patch("scraper.sources.papers.httpx.get", return_value=_mock_response(SAMPLE_RESPONSE)):
        articles = fetch_papers_with_code()
    a = articles[0]
    assert a.title == "LoRA: Low-Rank Adaptation of Large Language Models"
    assert a.source == "papers"
    assert "arxiv.org" in a.source_url
    assert "efficiently" in a.raw_text


def test_fetch_skips_entries_without_url():
    no_url = {"results": [{"title": "Paper", "abstract": "Abstract", "url_abs": None, "url_pdf": None}]}
    with patch("scraper.sources.papers.httpx.get", return_value=_mock_response(no_url)):
        articles = fetch_papers_with_code()
    assert articles == []
