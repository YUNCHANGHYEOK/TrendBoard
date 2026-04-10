const SOURCE_LABELS = {
  github: "GitHub",
  cvpr: "CVPR",
  iccv: "ICCV",
  eccv: "ECCV",
  hn: "HN",
  arxiv: "arXiv",
  papers: "Papers",
  pytorch_kr: "PyTorch KR",
  hn_ai: "HN AI",
  huggingface: "HuggingFace",
};

const SOURCE_CLASS = {
  github: "source-github",
  cvpr: "source-cvpr",
  iccv: "source-iccv",
  eccv: "source-eccv",
  hn: "source-hn",
  arxiv: "source-arxiv",
  papers: "source-papers",
  pytorch_kr: "source-pytorch-kr",
  hn_ai: "source-hn-ai",
  huggingface: "source-huggingface",
};

const PAPER_META_LABELS = {
  cvpr: "CVPR 2025 발표 논문",
  iccv: "ICCV 2025 발표 논문",
  eccv: "ECCV 2024 발표 논문",
  arxiv: "arXiv 논문",
  papers: "추천 논문",
  huggingface: "HuggingFace 오늘의 논문",
};

let currentFilter = "all";
let isCollecting = false;

function parseUtcDate(dateStr) {
  if (!dateStr) {
    return null;
  }

  if (dateStr.includes("T")) {
    return new Date(dateStr);
  }

  return new Date(dateStr.replace(" ", "T") + "Z");
}

function timeAgo(dateStr) {
  const target = parseUtcDate(dateStr);
  if (!target || Number.isNaN(target.getTime())) {
    return "알 수 없음";
  }

  const diff = Math.max(0, (Date.now() - target.getTime()) / 1000);
  if (diff < 3600) {
    return `${Math.floor(diff / 60)}분 전`;
  }
  if (diff < 86400) {
    return `${Math.floor(diff / 3600)}시간 전`;
  }
  return `${Math.floor(diff / 86400)}일 전`;
}

function getPaperMetaLabel(article) {
  return PAPER_META_LABELS[article?.source] || null;
}

function createSourceTag(article) {
  const source = article?.source || "";
  const tag = document.createElement("span");
  tag.className = `source-tag ${SOURCE_CLASS[source] || "source-paper"}`;
  tag.textContent = SOURCE_LABELS[source] || "Source";
  return tag;
}

function createPaperMeta(article) {
  const label = getPaperMetaLabel(article);
  if (!label) {
    return null;
  }

  const meta = document.createElement("div");
  meta.className = "paper-meta";
  meta.textContent = label;
  return meta;
}

function createLink(url) {
  const link = document.createElement("a");
  link.className = "card-link";
  link.href = url;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = "원문 보기";
  return link;
}

function setRunNote(message, isError = false) {
  const note = document.getElementById("run-note");
  if (!message) {
    note.hidden = true;
    note.textContent = "";
    note.classList.remove("is-error");
    return;
  }

  note.hidden = false;
  note.textContent = message;
  note.classList.toggle("is-error", isError);
}

function renderTopPick(article) {
  const container = document.getElementById("top-pick-container");
  container.innerHTML = "";

  if (!article) {
    return;
  }

  const card = document.createElement("div");
  card.className = "top-pick";

  const label = document.createElement("div");
  label.className = "top-pick-label";
  label.textContent = "오늘의 TOP PICK";

  const title = document.createElement("div");
  title.className = "top-pick-title";
  title.textContent = article.title;

  const paperMeta = createPaperMeta(article);

  const summary = document.createElement("div");
  summary.className = "top-pick-summary";
  summary.textContent = article.summary_ko || "";

  const footer = document.createElement("div");
  footer.className = "top-pick-footer";
  footer.appendChild(createSourceTag(article));
  footer.appendChild(createLink(article.source_url));

  card.appendChild(label);
  card.appendChild(title);
  if (paperMeta) {
    card.appendChild(paperMeta);
  }
  card.appendChild(summary);
  card.appendChild(footer);
  container.appendChild(card);
}

function renderArticles(articles) {
  const container = document.getElementById("articles-container");
  container.innerHTML = "";

  if (!articles.length) {
    const empty = document.createElement("p");
    empty.className = "status";
    empty.innerHTML =
      "아직 수집된 글이 없습니다.<br>오전 8시와 오후 8시에 자동 수집됩니다.";
    container.appendChild(empty);
    return;
  }

  for (const article of articles) {
    const card = document.createElement("div");
    card.className = "card";

    const header = document.createElement("div");
    header.className = "card-header";
    header.appendChild(createSourceTag(article));

    const time = document.createElement("span");
    time.className = "card-time";
    time.textContent = timeAgo(article.collected_at);
    header.appendChild(time);

    const title = document.createElement("div");
    title.className = "card-title";
    title.textContent = article.title;

    const paperMeta = createPaperMeta(article);

    const summary = document.createElement("div");
    summary.className = "card-summary";
    summary.textContent = article.summary_ko || "";

    card.appendChild(header);
    card.appendChild(title);
    if (paperMeta) {
      card.appendChild(paperMeta);
    }
    card.appendChild(summary);
    card.appendChild(createLink(article.source_url));
    container.appendChild(card);
  }
}

function updateLastUpdated(lastRun, articles) {
  const label = document.getElementById("last-updated");

  if (lastRun?.finished_at) {
    let prefix = "마지막 수집";
    if (lastRun.status === "failed") {
      prefix = "마지막 실행 실패";
    } else if (lastRun.status === "partial") {
      prefix = "마지막 부분 수집";
    }

    label.textContent = `${prefix}: ${timeAgo(lastRun.finished_at)}`;
    return;
  }

  if (articles.length) {
    label.textContent = `마지막 수집: ${timeAgo(articles[0].collected_at)}`;
    return;
  }

  label.textContent = "아직 수집 기록이 없습니다.";
}

function renderRunState(lastRun) {
  if (!lastRun?.error_summary) {
    setRunNote("");
    return;
  }

  let prefix = "최근 실행 메모";
  if (lastRun.status === "failed") {
    prefix = "최근 실행 오류";
  } else if (lastRun.status === "partial") {
    prefix = "최근 부분 수집";
  }

  setRunNote(`${prefix}: ${lastRun.error_summary}`, lastRun.status === "failed");
}

async function fetchStatus() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return data.last_run || null;
  } catch (error) {
    return null;
  }
}

async function loadArticles({ preserveRunNote = false } = {}) {
  const url =
    currentFilter === "all"
      ? "/api/articles"
      : `/api/articles?source_group=${currentFilter}`;

  try {
    const [articlesResponse, lastRun] = await Promise.all([
      fetch(url),
      fetchStatus(),
    ]);

    if (!articlesResponse.ok) {
      throw new Error("Failed to load articles");
    }

    const data = await articlesResponse.json();
    const articles = data.articles || [];
    const topPick = articles.find((article) => article.is_top_pick);
    const rest = articles.filter((article) => !article.is_top_pick);

    renderTopPick(topPick);
    document.getElementById("rest-label").style.display = rest.length ? "block" : "none";
    renderArticles(rest);
    updateLastUpdated(lastRun, articles);
    if (!preserveRunNote) {
      renderRunState(lastRun);
    }
    return { articles, lastRun };
  } catch (error) {
    const container = document.getElementById("articles-container");
    container.innerHTML = '<p class="status">데이터를 불러오지 못했습니다.</p>';
    document.getElementById("rest-label").style.display = "none";
    renderTopPick(null);
    if (!preserveRunNote) {
      setRunNote("데이터 로드에 실패했습니다. 서버 상태를 확인해주세요.", true);
    }
    return { articles: [], lastRun: null };
  }
}

function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll(".filter-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === filter);
  });
  loadArticles();
}

function setCollectButtonState(isBusy) {
  const button = document.getElementById("collect-now-btn");
  button.disabled = isBusy;
  button.textContent = isBusy ? "수집 중..." : "지금 수집";
}

async function runCollection() {
  if (isCollecting) {
    return;
  }

  isCollecting = true;
  setCollectButtonState(true);
  setRunNote("최신 데이터를 수집하고 있습니다. 시간이 조금 걸릴 수 있어요.");

  try {
    const response = await fetch("/api/collect/run", { method: "POST" });
    if (!response.ok) {
      throw new Error("Failed to run collection");
    }

    const result = await response.json();
    await loadArticles({ preserveRunNote: true });

    if (result.status === "failed") {
      setRunNote(
        `수집 실패: ${result.error_summary || "원인을 확인해주세요."}`,
        true
      );
      return;
    }

    if (result.status === "partial") {
      const suffix = result.error_summary ? ` ${result.error_summary}` : "";
      setRunNote(
        `부분 수집 완료: ${result.saved_count}개 항목을 저장했습니다.${suffix}`
      );
      return;
    }

    setRunNote(`수집 완료: ${result.saved_count}개 항목을 저장했습니다.`);
  } catch (error) {
    setRunNote("수집 실행에 실패했습니다. 잠시 후 다시 시도해주세요.", true);
  } finally {
    isCollecting = false;
    setCollectButtonState(false);
  }
}

document.querySelectorAll(".filter-btn").forEach((button) => {
  button.addEventListener("click", () => {
    setFilter(button.dataset.filter);
  });
});

document.getElementById("collect-now-btn").addEventListener("click", runCollection);

loadArticles();
