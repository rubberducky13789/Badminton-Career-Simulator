const updateButton = document.querySelector("#update-button");
const updateIcon = document.querySelector("#update-icon");
const updateLabel = document.querySelector("#update-label");
const statusText = document.querySelector("#status-text");
const statusDot = document.querySelector("#status-dot");
const searchInput = document.querySelector("#search-input");
const categorySelect = document.querySelector("#category-select");
const rankingBody = document.querySelector("#ranking-body");
const resultCount = document.querySelector("#result-count");
const emptyState = document.querySelector("#empty-state");

let rankings = [];

function normalize(value) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .match(/[a-z0-9]+/g)?.join(" ") || "";
}

function setStatus(message, state = "ready") {
  statusText.textContent = message;
  statusDot.dataset.state = state;
}

function addCell(row, value, className = "") {
  const cell = document.createElement("td");
  cell.textContent = value || "—";
  if (className) cell.className = className;
  row.appendChild(cell);
}

function renderRankings() {
  const queryTokens = new Set(normalize(searchInput.value).split(" ").filter(Boolean));
  const category = categorySelect.value;
  const filtered = rankings.filter((ranking) => {
    if (category && ranking.category !== category) return false;
    const nameTokens = new Set(normalize(ranking.name).split(" ").filter(Boolean));
    return [...queryTokens].every((token) => nameTokens.has(token));
  });

  const fragment = document.createDocumentFragment();
  filtered.forEach((ranking) => {
    const row = document.createElement("tr");
    addCell(row, ranking.category);
    addCell(row, ranking.rank, "number rank");
    addCell(row, ranking.name, "player-name");
    addCell(row, ranking.country);
    addCell(row, ranking.points, "number");
    addCell(row, ranking.movement, "number");
    fragment.appendChild(row);
  });

  rankingBody.replaceChildren(fragment);
  resultCount.textContent = filtered.length.toLocaleString();
  emptyState.hidden = filtered.length !== 0;
}

async function loadRankings() {
  const response = await fetch("/api/rankings");
  if (!response.ok) throw new Error("Could not load the stored ranking files.");
  const data = await response.json();
  rankings = data.rankings;
  renderRankings();
  return data.count;
}

async function updateRankings() {
  updateButton.disabled = true;
  updateButton.classList.add("is-loading");
  updateIcon.classList.add("spin");
  updateLabel.textContent = "Updating...";
  setStatus("Updating rankings...", "loading");

  try {
    const response = await fetch("/api/update", { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The update failed.");

    await loadRankings();
    setStatus(
      `Updated ${data.completed_at} · ${data.changes} ranking changes detected`,
      "success",
    );
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    updateButton.disabled = false;
    updateButton.classList.remove("is-loading");
    updateIcon.classList.remove("spin");
    updateLabel.textContent = "Update Rankings";
  }
}

updateButton.addEventListener("click", updateRankings);
searchInput.addEventListener("input", renderRankings);
categorySelect.addEventListener("change", renderRankings);

loadRankings()
  .then((count) => setStatus(`Loaded ${count.toLocaleString()} rankings`, "ready"))
  .catch((error) => setStatus(error.message, "error"));
