from dataclasses import dataclass
from typing import Literal

Source = Literal["github", "hn", "arxiv", "papers", "cvpr", "iccv", "eccv"]

@dataclass
class RawArticle:
    title: str
    source_url: str
    source: Source
    raw_text: str  # Gemini에 전달할 원문 텍스트
