from dataclasses import dataclass
from typing import Literal
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from scraper.types import RawArticle

CVF_BASE_URL = "https://openaccess.thecvf.com"
ECCV_BASE_URL = "https://eccv.ecva.net"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(frozen=True)
class ConferenceConfig:
    source: Literal["cvpr", "iccv", "eccv"]
    label: str
    year: int
    listing_url: str


CONFERENCES: dict[str, ConferenceConfig] = {
    "cvpr": ConferenceConfig(
        source="cvpr",
        label="CVPR",
        year=2025,
        listing_url="https://openaccess.thecvf.com/CVPR2025?day=all",
    ),
    "iccv": ConferenceConfig(
        source="iccv",
        label="ICCV",
        year=2025,
        listing_url="https://openaccess.thecvf.com/ICCV2025?day=all",
    ),
    "eccv": ConferenceConfig(
        source="eccv",
        label="ECCV",
        year=2024,
        listing_url="https://eccv.ecva.net/virtual/2024/papers.html",
    ),
}


def _get_html(url: str) -> str:
    response = httpx.get(
        url,
        headers=REQUEST_HEADERS,
        follow_redirects=True,
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _parse_cvf_listing(html: str, limit: int) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    entries: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not href.endswith("_paper.html"):
            continue

        paper_url = urljoin(CVF_BASE_URL, href)
        if paper_url in seen_urls:
            continue

        title = _clean_text(link.get_text(" ", strip=True))
        if not title:
            continue

        seen_urls.add(paper_url)
        entries.append({"title": title, "paper_url": paper_url})
        if len(entries) >= limit:
            break

    return entries


def _parse_eccv_listing(html: str, limit: int) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    entries: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    skip_titles = {
        "Skip to yearly menu bar",
        "Skip to main content",
        "Create Profile",
        "Reset Password",
        "My Stuff",
        "Login",
        "Getting Started",
        "Schedule",
        "Keynotes",
        "Orals",
        "Papers",
        "Paper Awards",
        "Workshops",
        "Tutorials",
        "Sponsors",
        "Organizers",
        "Help",
        "Visualization",
    }

    for link in soup.find_all("a", href=True):
        href = link["href"]
        paper_url = urljoin(ECCV_BASE_URL, href)
        if "/virtual/2024/" not in paper_url:
            continue
        if not any(part in paper_url for part in ("/poster/", "/oral/", "/spotlight/")):
            continue

        title = _clean_text(link.get_text(" ", strip=True))
        if not title or title in skip_titles or len(title) < 12:
            continue
        if paper_url in seen_urls:
            continue

        seen_urls.add(paper_url)
        entries.append({"title": title, "paper_url": paper_url})
        if len(entries) >= limit:
            break

    return entries


def _extract_authors(html: str, title: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    authors_node = soup.select_one("#authors")
    if authors_node is not None:
        authors = _clean_text(authors_node.get_text(" ", strip=True))
        if authors:
            return authors

    lines = [_clean_text(line) for line in soup.get_text("\n").splitlines()]
    lines = [line for line in lines if line]
    title_line = _clean_text(title)

    for index, line in enumerate(lines):
        normalized = line.removeprefix("# ").strip()
        if normalized != title_line:
            continue

        for candidate in lines[index + 1 : index + 8]:
            lowered = candidate.lower()
            if lowered in {"abstract", "poster", "oral", "spotlight"}:
                continue
            if lowered.startswith("related material"):
                break
            if lowered.startswith("strong "):
                continue
            if "paper pdf" in lowered or "project page" in lowered:
                continue
            if "proceedings of the ieee/cvf" in lowered:
                continue
            return candidate.replace(" · ", ", ")

    return ""


def _extract_abstract(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    abstract_node = soup.select_one("#abstract")
    if abstract_node is not None:
        abstract = _clean_text(abstract_node.get_text(" ", strip=True))
        if abstract:
            return abstract

    lines = [_clean_text(line) for line in soup.get_text("\n").splitlines()]
    lines = [line for line in lines if line]
    start_index = next(
        (index for index, line in enumerate(lines) if line.lower() == "abstract"),
        None,
    )
    if start_index is None:
        return ""

    abstract_lines: list[str] = []
    stop_prefixes = (
        "related material",
        "[bibtex]",
        "bibtex",
        "show more",
        "chat is not available",
        "successful page load",
    )

    for line in lines[start_index + 1 :]:
        lowered = line.lower()
        if any(lowered.startswith(prefix) for prefix in stop_prefixes):
            break
        abstract_lines.append(line)

    return _clean_text(" ".join(abstract_lines))


def _build_raw_text(config: ConferenceConfig, title: str, authors: str, abstract: str) -> str:
    parts = [f"Conference: {config.label} {config.year}", f"Title: {title}"]
    if authors:
        parts.append(f"Authors: {authors}")
    if abstract:
        parts.append(f"Abstract: {abstract}")
    return "\n".join(parts)


import logging as _logging
_vlog = _logging.getLogger(__name__)


def _fetch_conference_papers(source: Literal["cvpr", "iccv", "eccv"], limit: int) -> list[RawArticle]:
    config = CONFERENCES[source]
    try:
        listing_html = _get_html(config.listing_url)
    except Exception as exc:
        _vlog.warning(f"{config.label} listing 페이지 접속 실패, 건너뜀: {exc}")
        return []

    if source in {"cvpr", "iccv"}:
        entries = _parse_cvf_listing(listing_html, limit)
    else:
        entries = _parse_eccv_listing(listing_html, limit)

    articles: list[RawArticle] = []
    for entry in entries:
        authors = ""
        abstract = ""
        try:
            detail_html = _get_html(entry["paper_url"])
            authors = _extract_authors(detail_html, entry["title"])
            abstract = _extract_abstract(detail_html)
        except Exception:
            # Keep the listing result even if the detail page is temporarily unavailable.
            pass

        articles.append(
            RawArticle(
                title=entry["title"],
                source_url=entry["paper_url"],
                source=config.source,
                raw_text=_build_raw_text(config, entry["title"], authors, abstract),
            )
        )

    return articles


def fetch_cvpr_papers(limit: int = 8) -> list[RawArticle]:
    return _fetch_conference_papers("cvpr", limit)


def fetch_iccv_papers(limit: int = 8) -> list[RawArticle]:
    return _fetch_conference_papers("iccv", limit)


def fetch_eccv_papers(limit: int = 8) -> list[RawArticle]:
    return _fetch_conference_papers("eccv", limit)
