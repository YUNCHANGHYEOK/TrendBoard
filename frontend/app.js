/*
const SOURCE_LABELS = {
  github: "GitHub",
  cvpr: "CVPR",
  iccv: "ICCV",
  eccv: "ECCV",
  hn: "HN",
  arxiv: "arXiv",
  papers: "Papers",
};

const SOURCE_CLASS = {
  github: "source-github",
  cvpr: "source-cvpr",
  iccv: "source-iccv",
  eccv: "source-eccv",
  hn: "source-hn",
  arxiv: "source-arxiv",
  papers: "source-papers",
};

let currentFilter = "all";
let isCollecting = false;
const PAPER_META_LABELS = {
  cvpr: "CVPR 2025 발표 논문",
  iccv: "ICCV 2025 발표 논문",
  eccv: "ECCV 2024 발표 논문",
  arxiv: "arXiv 논문",
  papers: "추천 논문",
};
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

function createSourceTag(article) {
  const tag = document.createElement("span");
  tag.className = `source-tag ${SOURCE_CLASS[article.source]}`;
  tag.textContent = SOURCE_LABELS[article.source] || article.source;
  return tag;
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

  const summary = document.createElement("div");
  summary.className = "top-pick-summary";
  summary.textContent = article.summary_ko;

  const footer = document.createElement("div");
  footer.className = "top-pick-footer";
  footer.appendChild(createSourceTag(article));
  footer.appendChild(createLink(article.source_url));

  card.appendChild(label);
  card.appendChild(title);
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
    empty.innerHTML = "아직 수집된 글이 없습니다.<br>오전 8시와 오후 8시에 자동 수집됩니다.";
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

    const summary = document.createElement("div");
    summary.className = "card-summary";
    summary.textContent = article.summary_ko;

    card.appendChild(header);
    card.appendChild(title);
    card.appendChild(summary);
    card.appendChild(createLink(article.source_url));
    container.appendChild(card);
  }
}

function updateLastUpdated(lastRun, articles) {
  const label = document.getElementById("last-updated");

  if (lastRun?.finished_at) {
    const prefix = lastRun.status === "failed" ? "마지막 실행" : "마지막 수집";
    label.textContent = `${prefix}: ${timeAgo(lastRun.finished_at)}`;
    return;
  }

  if (articles.length) {
    label.textContent = `마지막 수집: ${timeAgo(articles[0].collected_at)}`;
    return;
  }

  label.textContent = "아직 수집 기록이 없습니다.";
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

async function loadArticles() {
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
  } catch (error) {
    const container = document.getElementById("articles-container");
    container.innerHTML = '<p class="status">데이터를 불러오지 못했습니다.</p>';
  }
}

function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll(".filter-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === filter);
  });
  loadArticles();
}

document.querySelectorAll(".filter-btn").forEach((button) => {
  button.addEventListener("click", () => {
    setFilter(button.dataset.filter);
  });
});

loadArticles();
*/

const SOURCE_LABELS = {
  github: "GitHub",
  cvpr: "CVPR",
  iccv: "ICCV",
  eccv: "ECCV",
  hn: "HN",
  arxiv: "arXiv",
  papers: "Papers",
};

const SOURCE_CLASS = {
  github: "source-github",
  cvpr: "source-cvpr",
  iccv: "source-iccv",
  eccv: "source-eccv",
  hn: "source-hn",
  arxiv: "source-arxiv",
  papers: "source-papers",
};

let currentFilter = "all";

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
    return "\uC54C \uC218 \uC5C6\uC74C";
  }

  const diff = Math.max(0, (Date.now() - target.getTime()) / 1000);
  if (diff < 3600) {
    return `${Math.floor(diff / 60)}\uBD84 \uC804`;
  }
  if (diff < 86400) {
    return `${Math.floor(diff / 3600)}\uC2DC\uAC04 \uC804`;
  }
  return `${Math.floor(diff / 86400)}\uC77C \uC804`;
}

function isPaperSource(article) {
  return ["cvpr", "iccv", "eccv", "arxiv", "papers"].includes(article?.source);
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
  link.textContent = "\uC6D0\uBB38 \uBCF4\uAE30";
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
  label.textContent = "\uC624\uB298\uC758 TOP PICK";

  const title = document.createElement("div");
  title.className = "top-pick-title";
  title.textContent = article.title;

  const paperMeta = createPaperMeta(article);
  const summary = document.createElement("div");
  summary.className = "top-pick-summary";
  summary.textContent = article.summary_ko;

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
      "\uC544\uC9C1 \uC218\uC9D1\uB41C \uAE00\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.<br>\uC624\uC804 8\uC2DC\uC640 \uC624\uD6C4 8\uC2DC\uC5D0 \uC790\uB3D9 \uC218\uC9D1\uB429\uB2C8\uB2E4.";
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
    summary.textContent = article.summary_ko;

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
    let prefix = "\uB9C8\uC9C0\uB9C9 \uC218\uC9D1";
    if (lastRun.status === "failed") {
      prefix = "\uB9C8\uC9C0\uB9C9 \uC2E4\uD589 \uC2E4\uD328";
    } else if (lastRun.status === "partial") {
      prefix = "\uB9C8\uC9C0\uB9C9 \uBD80\uBD84 \uC218\uC9D1";
    }

    label.textContent = `${prefix}: ${timeAgo(lastRun.finished_at)}`;
    return;
  }

  if (articles.length) {
    label.textContent = `\uB9C8\uC9C0\uB9C9 \uC218\uC9D1: ${timeAgo(articles[0].collected_at)}`;
    return;
  }

  label.textContent = "\uC544\uC9C1 \uC218\uC9D1 \uAE30\uB85D\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.";
}

function renderRunState(lastRun) {
  if (!lastRun?.error_summary) {
    setRunNote("");
    return;
  }

  let prefix = "\uCD5C\uADFC \uC2E4\uD589 \uBA54\uBAA8";
  if (lastRun.status === "failed") {
    prefix = "\uCD5C\uADFC \uC2E4\uD589 \uC624\uB958";
  } else if (lastRun.status === "partial") {
    prefix = "\uCD5C\uADFC \uBD80\uBD84 \uC218\uC9D1";
  }

  setRunNote(
    `${prefix}: ${lastRun.error_summary}`,
    lastRun.status === "failed"
  );
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
    container.innerHTML =
      '<p class="status">\uB370\uC774\uD130\uB97C \uBD88\uB7EC\uC624\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.</p>';
    document.getElementById("rest-label").style.display = "none";
    renderTopPick(null);
    if (!preserveRunNote) {
      setRunNote(
        "\uB370\uC774\uD130 \uB85C\uB4DC\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4. \uC11C\uBC84 \uC0C1\uD0DC\uB97C \uD655\uC778\uD574\uC8FC\uC138\uC694.",
        true
      );
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
  button.textContent = isBusy
    ? "\uC218\uC9D1 \uC911..."
    : "\uC9C0\uAE08 \uC218\uC9D1";
}

async function runCollection() {
  if (isCollecting) {
    return;
  }

  isCollecting = true;
  setCollectButtonState(true);
  setRunNote(
    "\uCD5C\uC2E0 \uB370\uC774\uD130\uB97C \uC218\uC9D1\uD558\uACE0 \uC788\uC2B5\uB2C8\uB2E4. \uC2DC\uAC04\uC774 \uC870\uAE08 \uAC78\uB9B4 \uC218 \uC788\uC5B4\uC694."
  );

  try {
    const response = await fetch("/api/collect/run", { method: "POST" });
    if (!response.ok) {
      throw new Error("Failed to run collection");
    }

    const result = await response.json();
    await loadArticles({ preserveRunNote: true });

    if (result.status === "failed") {
      setRunNote(
        `\uC218\uC9D1 \uC2E4\uD328: ${result.error_summary || "\uC6D0\uC778\uC744 \uD655\uC778\uD574\uC8FC\uC138\uC694."}`,
        true
      );
      return;
    }

    if (result.status === "partial") {
      const suffix = result.error_summary ? ` ${result.error_summary}` : "";
      setRunNote(
        `\uBD80\uBD84 \uC218\uC9D1 \uC644\uB8CC: ${result.saved_count}개 \uD56D\uBAA9\uC744 \uC800\uC7A5\uD588\uC2B5\uB2C8\uB2E4.${suffix}`
      );
      return;
    }

    setRunNote(
      `\uC218\uC9D1 \uC644\uB8CC: ${result.saved_count}\uAC1C \uD56D\uBAA9\uC744 \uC800\uC7A5\uD588\uC2B5\uB2C8\uB2E4.`
    );
  } catch (error) {
    setRunNote(
      "\uC218\uC9D1 \uC2E4\uD589\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4. \uC7A0\uC2DC \uD6C4 \uB2E4\uC2DC \uC2DC\uB3C4\uD574\uC8FC\uC138\uC694.",
      true
    );
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
