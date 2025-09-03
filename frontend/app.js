// ===== CONFIG =====
const API = "http://127.0.0.1:8000";
const THEME_KEY = "vscan_theme";

// ===== STATE + REFS =====
let lastReport = null;
let currentFilter = "All";
let history = [];

const $ = (id) => document.getElementById(id);
const R = {
  url: $("url"),
  loading: $("loading"),
  summary: $("summary"),
  results: $("results"),
  filters: $("filters"),
  search: $("search"),
  toast: $("toast"),
  history: $("history"),
};

// ===== THEME HELPERS =====
function getTheme() {
  return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
}
function setTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  try { localStorage.setItem(THEME_KEY, t); } catch {}
  // Optional: update theme-color meta if present
  const m = document.getElementById("themeColor");
  if (m) m.setAttribute("content", t === "light" ? "#f5f7ff" : "#0c1224");
}
window.toggleTheme = function toggleTheme() {
  const next = getTheme() === "dark" ? "light" : "dark";
  setTheme(next);
  toast("Theme: " + next);
};

// ===== INIT (runs immediately) =====
(function init() {
  // Ensure html has a theme attribute
  if (!document.documentElement.hasAttribute("data-theme")) {
    document.documentElement.setAttribute("data-theme", "dark");
  }
  // Restore saved theme (or keep current attribute)
  let saved = null;
  try { saved = localStorage.getItem(THEME_KEY); } catch {}
  if (saved === "light" || saved === "dark") setTheme(saved);

  // History
  history = loadHistory();
  renderHistory();

  console.log("app.js v4 ready. Theme:", getTheme());
})();

// ===== GLOBAL UI FUNCTIONS (inline handlers call these) =====
window.runScan = async function runScan() {
  const url = R.url.value.trim();
  if (!url) return toast("Enter a URL");

  R.results.innerHTML = "";
  R.summary.classList.add("hidden");
  R.filters.classList.add("hidden");
  R.loading.classList.remove("hidden");
  lastReport = null;

  try {
    const res = await fetch(`${API}/scan`, {
      method: "POST",
      headers: { "Content-Type": "text/plain" }, // simple CORS (no preflight)
      body: JSON.stringify({ url }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data?.error) throw new Error(data?.error || `Scan failed (${res.status})`);

    lastReport = data;
    renderReport();

    addHistory({
      url: data.target,
      score: data.score,
      high: data.summary.high, medium: data.summary.medium, low: data.summary.low,
      ts: Date.now(), report: data
    });
  } catch (e) {
    console.error(e);
    toast(e.message || "Failed to scan");
  } finally {
    R.loading.classList.add("hidden");
  }
};

window.quick = function quick(u) { R.url.value = u; runScan(); };

window.setFilter = function setFilter(name) {
  currentFilter = name;
  document.querySelectorAll(".filter").forEach(b => b.classList.toggle("active", b.textContent.trim() === name));
  paintFindings(R.search.value.trim().toLowerCase());
};

window.searchFindings = function searchFindings(q) { paintFindings((q||"").trim().toLowerCase()); };

window.exportJSON = function exportJSON() {
  if (!lastReport) return toast("Run a scan first");
  const blob = new Blob([JSON.stringify(lastReport, null, 2)], { type: "application/json" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "scan-report.json"; a.click();
};

window.copyCurl = function copyCurl() {
  const u = R.url.value.trim(); if (!u) return toast("Enter a URL");
  const cmd = `curl -s ${API}/scan -H "Content-Type: text/plain" -d "{\\"url\\":\\"${u}\\"}"`;
  if (navigator.clipboard) navigator.clipboard.writeText(cmd).then(()=>toast("cURL copied")).catch(()=>prompt("Copy cURL:", cmd));
  else prompt("Copy cURL:", cmd);
};

window.handleImport = function handleImport(e) {
  const f = e.target.files?.[0]; if (!f) return;
  const r = new FileReader();
  r.onload = () => { try { lastReport = JSON.parse(r.result); renderReport(); toast("Imported report"); } catch { toast("Invalid JSON"); } };
  r.readAsText(f); e.target.value = "";
};

window.setAllGroups = function setAllGroups(open) { document.querySelectorAll(".group").forEach(g => g.classList.toggle("open", open)); };

window.clearHistory = function clearHistory() { history = []; saveHistory(); renderHistory(); toast("History cleared"); };

window.maybeToggleGroup = function maybeToggleGroup(e) {
  const hdr = e.target.closest(".group-header"); if (!hdr) return;
  const id = hdr.dataset.target; const el = document.getElementById(id); if (el) el.classList.toggle("open");
};

// ===== RENDER =====
function renderReport() {
  const rep = lastReport; if (!rep) return;
  const sev = rep.summary;
  R.summary.innerHTML = `
    <div class="card">
      <h2 class="m0">Summary for ${escapeHtml(rep.target)}</h2>
      <div class="badges">
        <span class="badge high">High: ${sev.high}</span>
        <span class="badge med">Medium: ${sev.medium}</span>
        <span class="badge low">Low: ${sev.low}</span>
        <span class="badge score">Risk Score: ${rep.score}/100</span>
      </div>
      <div class="progress"><div class="bar" style="width:${Math.min(rep.score,100)}%"></div></div>
    </div>`;
  R.summary.classList.remove("hidden");
  R.filters.classList.remove("hidden");
  paintFindings(R.search.value.trim().toLowerCase());
}

function paintFindings(q="") {
  const rep = lastReport; if (!rep) return;
  R.results.innerHTML = "";

  (rep.results || []).forEach((group, idx) => {
    const list = (group.findings || []).filter(f =>
      (currentFilter === "All" || f.severity === currentFilter) &&
      (!q || onText(f).includes(q))
    );
    const count = list.length;
    const gid = `g${idx}`;
    const openClass = idx === 0 ? "open" : "";

    R.results.innerHTML += `
      <div class="group ${openClass}" id="${gid}">
        <div class="group-header" data-target="${gid}">
          <div class="group-title">${escapeHtml(group.category)}</div>
          <div class="group-count">${count} finding${count===1?"":"s"} ▾</div>
        </div>
        <div class="group-body">
          ${count ? list.map(f => findingCard(f)).join("") : `<div class="hint">No items match filters.</div>`}
        </div>
      </div>`;
  });

  if (!R.results.innerHTML.trim()) R.results.innerHTML = `<div class="card"><em>No ${currentFilter} findings.</em></div>`;
}

function findingCard(f) {
  const sevClass = f.severity === "High" ? "pill high" : f.severity === "Medium" ? "pill med" : "pill low";
  return `
    <div class="finding">
      <span class="${sevClass}">${f.severity}</span>
      <div class="finding-body">
        <div class="finding-title">${escapeHtml(f.title || "")}</div>
        <div class="finding-detail">${escapeHtml(f.detail || "")}</div>
        <div class="finding-meta">Category: ${escapeHtml(f.category || "")}</div>
      </div>
    </div>`;
}

// ===== HISTORY =====
function loadHistory(){ try { return JSON.parse(localStorage.getItem("vscan_history") || "[]"); } catch { return []; } }
function saveHistory(){ localStorage.setItem("vscan_history", JSON.stringify(history.slice(0,25))); }
function addHistory(item){ history.unshift(item); saveHistory(); renderHistory(); }
function renderHistory(){
  R.history.innerHTML = history.length ? "" : `<div class="hint">No scans yet.</div>`;
  history.slice(0,25).forEach((it,i)=>{
    const sev = `H:${it.high} M:${it.medium} L:${it.low}`;
    R.history.innerHTML += `
      <div class="history-item">
        <div class="history-url" title="${escapeHtml(it.url)}">${escapeHtml(it.url)}</div>
        <div class="row">
          <span class="badge score" title="Risk score">${it.score}</span>
          <span class="badge" title="Severity counts">${sev}</span>
          <button class="ghost sm" onclick="quick('${escapeAttr(it.url)}')">Re-run</button>
          <button class="ghost sm" onclick="loadSaved(${i})">View</button>
        </div>
      </div>`;
  });
}
window.loadSaved = function loadSaved(i){
  const item = history[i]; if (!item || !item.report) return toast("No saved report");
  lastReport = item.report; renderReport(); toast("Loaded saved report");
};

// ===== UTIL =====
function escapeHtml(s=""){ return s.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
function escapeAttr(s=""){ return s.replace(/"/g, '&quot;'); }
function onText(f){ return `${f.severity} ${f.title||""} ${f.detail||""} ${f.category||""}`.toLowerCase(); }
function toast(msg){
  R.toast.textContent = msg;
  R.toast.classList.remove("hidden");
  clearTimeout(toast._t); toast._t = setTimeout(()=>R.toast.classList.add("hidden"),1600);
}
