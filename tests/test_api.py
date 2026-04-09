import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from backend.app import app
    return TestClient(app)


def test_get_articles_returns_list(client):
    response = client.get("/api/articles")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert isinstance(data["articles"], list)


def test_get_articles_filter_by_source_group(client):
    # seed an arxiv article
    client.post("/api/collect", json={"articles": [
        {"title": "AI Paper", "summary_ko": "요약", "source_url": "https://arxiv.org/abs/1", "source": "arxiv", "is_top_pick": False}
    ]})
    response = client.get("/api/articles?source_group=ai")
    assert response.status_code == 200
    data = response.json()
    assert all(a["source"] in ("arxiv", "papers") for a in data["articles"])


def test_collect_saves_article(client):
    payload = {
        "articles": [
            {
                "title": "Test Article",
                "summary_ko": "테스트 요약입니다.",
                "source_url": "https://example.com",
                "source": "hn",
                "is_top_pick": False,
            }
        ]
    }
    response = client.post("/api/collect", json=payload)
    assert response.status_code == 200
    assert response.json()["saved"] == 1

    # verify round-trip
    list_response = client.get("/api/articles")
    articles = list_response.json()["articles"]
    assert any(a["title"] == "Test Article" for a in articles)
