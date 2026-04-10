from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator

from backend.database import get_articles, init_db
from backend.services import get_latest_collection_status, save_articles_batch
from scraper.runtime import collect_and_save


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
FRONTEND_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class ArticleIn(BaseModel):
    title: str
    summary_ko: str
    source_url: str
    source: Literal["github", "hn", "arxiv", "papers", "cvpr", "iccv", "eccv", "pytorch_kr", "hn_ai", "huggingface"]
    is_top_pick: bool = False


class CollectPayload(BaseModel):
    articles: list[ArticleIn]

    @model_validator(mode="after")
    def validate_top_pick(self) -> "CollectPayload":
        top_pick_count = sum(1 for article in self.articles if article.is_top_pick)
        if top_pick_count > 1:
            raise ValueError("Only one top pick article is allowed per batch.")
        return self


@app.get("/api/articles")
def api_get_articles(source_group: str | None = None):
    articles = get_articles(source_group=source_group)
    return {"articles": articles}


@app.post("/api/collect")
def api_collect(payload: CollectPayload):
    data = [a.model_dump() for a in payload.articles]
    try:
        saved = save_articles_batch(data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"saved": saved}


@app.post("/api/collect/run")
def api_collect_run():
    return collect_and_save()


@app.get("/api/status")
def api_get_status():
    return {"last_run": get_latest_collection_status()}


@app.get("/")
def serve_index():
    path = FRONTEND_DIR / "app.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Frontend not yet built")
    return FileResponse(path)
