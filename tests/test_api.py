import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_get_articles_returns_list():
    response = client.get("/api/articles")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert isinstance(data["articles"], list)


def test_get_articles_filter_by_source_group():
    response = client.get("/api/articles?source_group=ai")
    assert response.status_code == 200


def test_collect_saves_article():
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
