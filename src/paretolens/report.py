"""Write a single interactive HTML page for a Front (Plotly loaded from a CDN)."""
import html
import json
from pathlib import Path

import numpy as np

PLOTLY_CDN = "https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"


def _clean(a):
    return [[None if not np.isfinite(v) else float(v) for v in row] for row in np.asarray(a)]


def write_html(front, path, title="Pareto front explorer", weights=None):
    w = front._weights(weights) or [1.0] * len(front.names)
    data = {
        "names": front.names,
        "senses": front.senses,
        "units": front.units,
        "F": _clean(front.F),
        "N": _clean(front.normalised),
        "X": _clean(front.X) if front.X is not None else None,
        "varNames": front.var_names,
        "knee": front.knee(),
        "weights": [float(x) for x in w],
    }
    page = (TEMPLATE
            .replace("__TITLE__", html.escape(title))
            .replace("__PLOTLY__", PLOTLY_CDN)
            .replace("__DATA__", json.dumps(data)))
    Path(path).write_text(page, encoding="utf-8")
    return Path(path)


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script src="__PLOTLY__"></script>
<style>
:root{--bg:#f7f8fa;--card:#fff;--ink:#1c2430;--muted:#5d6b7c;--line:#e2e6eb;--accent:#0f766e;--knee:#d97706;--pick:#7c3aed;--grid:#eef0f3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1419;--card:#171d24;--ink:#e6eaef;--muted:#94a1b2;--line:#2a333d;--accent:#2dd4bf;--knee:#fbbf24;--pick:#a78bfa;--grid:#222a33}}
:root[data-theme="dark"]{--bg:#0f1419;--card:#171d24;--ink:#e6eaef;--muted:#94a1b2;--line:#2a333d;--accent:#2dd4bf;--knee:#fbbf24;--pick:#a78bfa;--grid:#222a33}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 20px}
.grid{display:grid;grid-template-columns:300px 1fr;gap:16px}
@media (max-width:860px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.card h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 12px}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 4px}
select{width:100%;padding:7px 8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);font:inherit}
.w{margin:10px 0}
.w .top{display:flex;justify-content:space-between;font-size:13px}
.w .top span:last-child{color:var(--muted);font-variant-numeric:tabular-nums}
input[type=range]{width:100%;accent-color:var(--accent)}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-top:14px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
#scatter,#parcoords{width:100%;height:440px}
#parcoords{height:380px}
table{width:100%;border-collapse:collapse;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600}
tr.sel td{background:color-mix(in srgb,var(--accent) 12%,transparent)}
tbody tr{cursor:pointer}
.tablewrap{overflow-x:auto}
.detail{font-size:13px}
.detail div{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding:4px 0}
.detail div span:last-child{font-variant-numeric:tabular-nums}
.stack{display:grid;gap:16px;align-content:start}
.foot{color:var(--muted);font-size:12px;margin-top:20px}
.foot a{color:var(--accent)}
</style>
</head>
<body>
<div class="wrap">
  <h1>__TITLE__</h1>
  <p class="sub" id="sub"></p>
  <div class="grid">
    <div class="stack">
      <div class="card">
        <h2>View</h2>
        <label for="xs">X axis</label><select id="xs"></select>
        <label for="ys">Y axis</label><select id="ys"></select>
        <label for="cs">Colour by</label><select id="cs"></select>
      </div>
      <div class="card">
        <h2>Your priorities</h2>
        <div id="weights"></div>
        <div class="legend">
          <span><span class="dot" style="background:var(--pick)"></span>Best for these weights</span>
          <span><span class="dot" style="background:var(--knee)"></span>Knee point</span>
        </div>
      </div>
      <div class="card">
        <h2 id="dtitle">Selected solution</h2>
        <div class="detail" id="detail"></div>
      </div>
    </div>
    <div class="stack">
      <div class="card"><div id="scatter"></div></div>
      <div class="card"><h2>All objectives at once</h2><div id="parcoords"></div></div>
      <div class="card"><h2>Top 10 for your priorities</h2><div class="tablewrap"><table id="tbl"></table></div></div>
    </div>
  </div>
  <p class="foot">Made with <a href="https://github.com/Thashmikab/paretolens">paretolens</a>. Scores use TOPSIS on min–max normalised objectives. The knee is the solution that bulges furthest towards the ideal point, where small gains in one objective start costing a lot in the others.</p>
</div>
<script>
const D = __DATA__;
const m = D.names.length, n = D.F.length;
let W = D.weights.slice(), sel = null, pinned = null;
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const fmt = v => v == null ? "–" : (Math.abs(v) >= 1e4 || (Math.abs(v) < 1e-2 && v !== 0)) ? v.toExponential(3) : (+v.toPrecision(5)).toLocaleString();
const lab = j => D.names[j] + (D.units[j] ? ` (${D.units[j]})` : "") + (D.senses[j] === "max" ? " ↑" : " ↓");

function topsis() {
  const s = W.reduce((a, b) => a + b, 0) || 1, w = W.map(v => v / s);
  return D.N.map(r => {
    let b = 0, x = 0;
    r.forEach((v, j) => { b += w[j] * v * v; x += w[j] * (1 - v) * (1 - v); });
    b = Math.sqrt(b); x = Math.sqrt(x);
    return x / (b + x + 1e-12);
  });
}

document.getElementById("sub").textContent =
  `${n} non-dominated solutions · ${m} objectives (↓ minimise, ↑ maximise)`;

const opt = (id, def) => {
  const el = document.getElementById(id);
  D.names.forEach((nm, j) => el.add(new Option(lab(j), j)));
  if (id === "cs") el.add(new Option("Score for your priorities", "score"));
  el.value = def; el.onchange = draw;
};
opt("xs", 0); opt("ys", Math.min(1, m - 1)); opt("cs", m > 2 ? 2 : "score");

const wbox = document.getElementById("weights");
D.names.forEach((nm, j) => {
  const d = document.createElement("div"); d.className = "w";
  d.innerHTML = `<div class="top"><span>${nm}</span><span id="wv${j}">${W[j].toFixed(2)}</span></div>
  <input type="range" min="0" max="1" step="0.05" value="${W[j]}" aria-label="weight for ${nm}">`;
  d.querySelector("input").oninput = e => { W[j] = +e.target.value; document.getElementById("wv" + j).textContent = W[j].toFixed(2); draw(); };
  wbox.appendChild(d);
});

function detail(i, score) {
  sel = i;
  const t = i === D.knee ? "Knee point" : "Solution";
  document.getElementById("dtitle").textContent = `${t} #${i}`;
  let h = D.names.map((nm, j) => `<div><span>${lab(j)}</span><span>${fmt(D.F[i][j])}</span></div>`).join("");
  h += `<div><span>Score</span><span>${score[i].toFixed(3)}</span></div>`;
  if (D.X) {
    const k = Math.min(8, D.varNames.length);
    h += D.varNames.slice(0, k).map((nm, j) => `<div><span>${nm}</span><span>${fmt(D.X[i][j])}</span></div>`).join("");
    if (D.varNames.length > k) h += `<div><span>+ ${D.varNames.length - k} more variables</span><span></span></div>`;
  }
  document.getElementById("detail").innerHTML = h;
}

function draw() {
  const score = topsis();
  const best = score.indexOf(Math.max(...score));
  const xj = +xs.value, yj = +ys.value, cv = cs.value;
  const color = cv === "score" ? score : D.F.map(r => r[+cv]);
  const ink = css("--ink"), grid = css("--grid"), muted = css("--muted");
  const base = { paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { color: ink, size: 12 }, margin: { l: 70, r: 20, t: 10, b: 55 } };
  const ax = t => ({ title: { text: t }, gridcolor: grid, zerolinecolor: grid, linecolor: grid });
  const hover = D.F.map((r, i) => `#${i}<br>` + D.names.map((nm, j) => `${nm}: ${fmt(r[j])}`).join("<br>") + `<br>score: ${score[i].toFixed(3)}`);
  const mark = (i, c, sym, name) => ({ x: [D.F[i][xj]], y: [D.F[i][yj]], mode: "markers", name, hoverinfo: "skip",
    marker: { size: 20, color: c, symbol: sym, line: { color: c, width: 3 } } });
  Plotly.react("scatter", [
    { x: D.F.map(r => r[xj]), y: D.F.map(r => r[yj]), mode: "markers", type: "scattergl", text: hover, hoverinfo: "text", name: "solutions",
      marker: { size: 8, color, colorscale: "Viridis", reversescale: cv !== "score" && D.senses[+cv] === "min", showscale: true,
        colorbar: { title: { text: cv === "score" ? "score" : D.names[+cv], side: "right" }, thickness: 12 } } },
    mark(D.knee, css("--knee"), "circle-open", "knee"),
    mark(best, css("--pick"), "diamond-open", "best for weights"),
  ], { ...base, xaxis: ax(lab(xj)), yaxis: ax(lab(yj)), showlegend: false }, { responsive: true, displaylogo: false });
  const sc = document.getElementById("scatter");
  if (!sc._hooked) { sc._hooked = true; sc.on("plotly_click", e => { if (e.points[0].curveNumber === 0) { const s = topsis(); pinned = e.points[0].pointIndex; detail(e.points[0].pointIndex, s); table(s); } }); }

  Plotly.react("parcoords", [{ type: "parcoords",
    line: { color: score, colorscale: "Viridis", showscale: false },
    labelfont: { color: ink }, tickfont: { color: muted }, rangefont: { color: muted },
    dimensions: D.names.map((nm, j) => ({ label: lab(j), values: D.F.map(r => r[j]) })) }],
    { ...base, margin: { l: 60, r: 60, t: 40, b: 20 } }, { responsive: true, displaylogo: false });

  detail(pinned ?? best, score);
  table(score);
}

function table(score) {
  const order = score.map((s, i) => i).sort((a, b) => score[b] - score[a]).slice(0, 10);
  let h = `<thead><tr><th>#</th>${D.names.map((nm, j) => `<th>${lab(j)}</th>`).join("")}<th>score</th></tr></thead><tbody>`;
  h += order.map(i => `<tr data-i="${i}" class="${i === sel ? "sel" : ""}"><td>${i}${i === D.knee ? " · knee" : ""}</td>${D.F[i].map(v => `<td>${fmt(v)}</td>`).join("")}<td>${score[i].toFixed(3)}</td></tr>`).join("");
  const t = document.getElementById("tbl"); t.innerHTML = h + "</tbody>";
  t.querySelectorAll("tbody tr").forEach(r => r.onclick = () => { pinned = +r.dataset.i; detail(pinned, score); table(score); });
}

const xs = document.getElementById("xs"), ys = document.getElementById("ys"), cs = document.getElementById("cs");
draw();
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
</script>
</body>
</html>
"""
