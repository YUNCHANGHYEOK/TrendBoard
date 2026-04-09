from unittest.mock import MagicMock, patch
from scraper.types import RawArticle
from scraper.summarizer import summarize_articles, pick_top_article


RAW_ARTICLES = [
    RawArticle(
        title="LoRA paper",
        source_url="https://arxiv.org/abs/2106.09685",
        source="arxiv",
        raw_text="LoRA paper\nWe propose low-rank adaptation...",
    ),
    RawArticle(
        title="TypeScript v5.8",
        source_url="https://github.com/microsoft/TypeScript",
        source="github",
        raw_text="TypeScript v5.8\nNew conditional type inference...",
    ),
]


def _mock_gemini(summary_text: str):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = summary_text
    mock_model.generate_content.return_value = mock_response
    return mock_model


def test_summarize_articles_returns_summaries():
    mock_model = _mock_gemini("이것은 한국어 요약입니다.")
    with patch("scraper.summarizer.genai.GenerativeModel", return_value=mock_model):
        with patch("scraper.summarizer.genai.configure"):
            results = summarize_articles(RAW_ARTICLES)
    assert len(results) == 2
    assert results[0]["summary_ko"] == "이것은 한국어 요약입니다."
    assert results[0]["title"] == "LoRA paper"
    assert results[0]["source"] == "arxiv"
    assert results[0]["is_top_pick"] is False


def test_summarize_articles_preserves_source_url():
    mock_model = _mock_gemini("요약")
    with patch("scraper.summarizer.genai.GenerativeModel", return_value=mock_model):
        with patch("scraper.summarizer.genai.configure"):
            results = summarize_articles(RAW_ARTICLES)
    assert results[0]["source_url"] == "https://arxiv.org/abs/2106.09685"


def test_pick_top_article_marks_one_as_top():
    mock_model = _mock_gemini("1")  # 첫 번째 선택
    with patch("scraper.summarizer.genai.GenerativeModel", return_value=mock_model):
        with patch("scraper.summarizer.genai.configure"):
            articles = [
                {"title": "A", "summary_ko": "요약A", "source_url": "https://a.com", "source": "hn", "is_top_pick": False},
                {"title": "B", "summary_ko": "요약B", "source_url": "https://b.com", "source": "arxiv", "is_top_pick": False},
            ]
            result = pick_top_article(articles)
    top_picks = [a for a in result if a["is_top_pick"]]
    assert len(top_picks) == 1
