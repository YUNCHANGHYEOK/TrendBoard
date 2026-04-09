from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from backend.database import init_db, insert_articles, get_articles


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
FRONTEND_DIR.mkdir(exist_ok=True)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class ArticleIn(BaseModel):
    title: str
    summary_ko: str
    source_url: str
    source: str
    is_top_pick: bool = False


class CollectPayload(BaseModel):
    articles: list[ArticleIn]


@app.get("/api/articles")
def api_get_articles(source_group: str | None = None):
    articles = get_articles(source_group=source_group)
    return {"articles": articles}


@app.post("/api/collect")
def api_collect(payload: CollectPayload):
    data = [a.model_dump() for a in payload.articles]
    saved = insert_articles(data)
    return {"saved": saved}


@app.get("/")
def serve_index():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / "index.html")
