const form = document.getElementById("path-form");
const teamAInput = document.getElementById("team-a");
const teamBInput = document.getElementById("team-b");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const pathListEl = document.getElementById("path-list");
const swapBtn = document.getElementById("swap");

function setStatus(message, tone = "info") {
  if (!statusEl) return;
  const toneMap = {
    info: "text-slate-400",
    error: "text-rose-400",
    success: "text-emerald-300",
  };
  statusEl.textContent = message || "";
  statusEl.className = `text-sm ${toneMap[tone] ?? toneMap.info}`;
}

function renderPath(path, edges) {
  pathListEl.innerHTML = "";
  if (!path || !path.length) {
    resultsEl.classList.add("hidden");
    return;
  }

  // Update description with actual team names
  const fromTeam = teamAInput.value.trim();
  const toTeam = teamBInput.value.trim();
  const descEl = document.getElementById("results-description");
  if (descEl) {
    descEl.textContent = `Shortest chain of victories from ${fromTeam} to ${toTeam}`;
  }

  edges.forEach((edge, idx) => {
    const li = document.createElement("li");
    // Check if the label contains a year in parentheses (indicating a past season game)
    const isPastSeason = /\(\d{4}\)/.test(edge.label);
    const isFinalGame = idx === edges.length - 1;
    if (isFinalGame) {
        li.className = "rounded-lg border border-slate-800 bg-amber-500/90 px-3 py-2";
    }
    if (isPastSeason) {
      li.className = "rounded-lg border border-slate-700 bg-slate-900/40 px-3 py-2 opacity-75";
    }
    else {
      li.className = "rounded-lg border border-slate-800 bg-slate-900 px-3 py-2";
    }
    li.innerHTML = `
      <div class="flex items-center gap-3">
        ${edge.fromLogo ? `<img src="${edge.fromLogo}" alt="${edge.from}" class="h-10 w-10 flex-shrink-0 object-contain ${isPastSeason ? 'opacity-60' : ''}" />` : ''}
        <div class="flex-1 ${isPastSeason ? 'text-slate-400' : 'text-white'} text-center">${edge.label}</div>
        ${edge.toLogo ? `<img src="${edge.toLogo}" alt="${edge.to}" class="h-10 w-10 flex-shrink-0 object-contain ${isPastSeason ? 'opacity-60' : ''}" />` : ''}
      </div>
    `;
    pathListEl.appendChild(li);
  });

  resultsEl.classList.remove("hidden");
}

async function handleSubmit(event) {
  event.preventDefault();
  const from = teamAInput.value.trim();
  const to = teamBInput.value.trim();
  if (!from || !to) {
    setStatus("Pick two teams", "error");
    return;
  }

  setStatus("Searching for a path…", "info");
  resultsEl.classList.add("hidden");

  try {
    const res = await fetch("/api/path", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from, to }),
    });

    const data = await res.json();
    if (!res.ok) {
      setStatus(data.error || "No path found", "error");
      return;
    }

    renderPath(data.path, data.edges);
    setStatus(`Found a chain with ${data.edges.length} step(s).`, "success");
  } catch (err) {
    console.error(err);
    setStatus("Something went wrong. Try again.", "error");
  }}

function handleSwap() {
  const a = teamAInput.value;
  teamAInput.value = teamBInput.value;
  teamBInput.value = a;
}

form?.addEventListener("submit", handleSubmit);
swapBtn?.addEventListener("click", handleSwap);
