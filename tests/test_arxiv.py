from unittest.mock import patch, MagicMock
from scraper.sources.arxiv import fetch_arxiv

SAMPLE_FEED = MagicMock()
SAMPLE_FEED.entries = [
    MagicMock(
        title="Efficient Transformers: A Survey",
        summary="We present a comprehensive survey of efficient transformer models...",
        link="https://arxiv.org/abs/2009.12345",
        tags=[MagicMock(term="cs.AI")],
    ),
    MagicMock(
        title="Another Paper",
        summary="Abstract of another paper.",
        link="https://arxiv.org/abs/2009.67890",
        tags=[MagicMock(term="cs.LG")],
    ),
]


def test_fetch_returns_articles():
    with patch("scraper.sources.arxiv.feedparser.parse", return_value=SAMPLE_FEED):
        articles = fetch_arxiv()
    assert len(articles) == 2


def test_fetch_article_fields():
    with patch("scraper.sources.arxiv.feedparser.parse", return_value=SAMPLE_FEED):
        articles = fetch_arxiv()
    a = articles[0]
    assert a.title == "Efficient Transformers: A Survey"
    assert a.source == "arxiv"
    assert "arxiv.org" in a.source_url
    assert "comprehensive survey" in a.raw_text
