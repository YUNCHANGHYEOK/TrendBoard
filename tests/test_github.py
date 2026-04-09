from unittest.mock import MagicMock, patch
from scraper.sources.github import fetch_github_trending

SAMPLE_HTML = """
<html><body>
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/openai/whisper">openai / whisper</a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">Robust Speech Recognition via Large-Scale Weak Supervision</p>
</article>
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/microsoft/TypeScript">microsoft / TypeScript</a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">TypeScript is a superset of JavaScript</p>
</article>
</body></html>
"""


def _mock_response(html: str) -> MagicMock:
    m = MagicMock()
    m.text = html
    m.raise_for_status = MagicMock()
    return m


def test_fetch_returns_articles():
    with patch("scraper.sources.github.httpx.get", return_value=_mock_response(SAMPLE_HTML)):
        articles = fetch_github_trending()
    assert len(articles) == 2


def test_fetch_article_fields():
    with patch("scraper.sources.github.httpx.get", return_value=_mock_response(SAMPLE_HTML)):
        articles = fetch_github_trending()
    a = articles[0]
    assert a.title == "openai/whisper"
    assert a.source == "github"
    assert a.source_url == "https://github.com/openai/whisper"
    assert "Robust Speech Recognition" in a.raw_text


def test_fetch_skips_rows_without_link():
    broken_html = '<article class="Box-row"><p>no link here</p></article>'
    with patch("scraper.sources.github.httpx.get", return_value=_mock_response(broken_html)):
        articles = fetch_github_trending()
    assert articles == []
