from dataclasses import dataclass

@dataclass
class RawArticle:
    title: str
    source_url: str
    source: str  # "github" | "hn" | "arxiv" | "papers"
    raw_text: str  # Gemini에 전달할 원문 텍스트
