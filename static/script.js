const track1 = () => document.querySelector(".ticker-track.first");
const track2 = () => document.querySelector(".ticker-track.second");

// === Utilidades ===
function iconForCategory(c){
  return { STOCK:"💼", INDEX:"💹", CRYPTO:"🪙", COMMODITY:"💰" }[c] || "";
}
function fmtPrice(v){
  if (v === null || v === undefined) return "—";
  const abs = Math.abs(v);
  return (abs >= 1000 || abs < 1) ? v.toFixed(4) : v.toFixed(2);
}
function fmtDelta(chg, pct){
  if (chg === null || pct === null) return {text:"—", cls:"flat"};
  const arrow = chg > 0 ? "▲" : chg < 0 ? "▼" : "•";
  const cls = chg > 0 ? "up" : chg < 0 ? "down" : "flat";
  const sign1 = chg > 0 ? "+" : "";
  const sign2 = pct > 0 ? "+" : "";
  return {text:`${arrow} ${sign1}${chg.toFixed(2)} (${sign2}${pct.toFixed(2)}%)`, cls};
}
function getCurrency(ticker){
  if (!ticker) return "USD";
  if (ticker.endsWith(".LS")) return "EUR";
  if (ticker.includes("-USD")) return "USD";
  return "USD";
}

// === Ticker superior ===
function buildHTML(items){
  return items.map(it=>{
    const d = fmtDelta(it.change, it.change_pct);
    return `
      <div class="item">
        <span class="cat cat-${it.category.toLowerCase()}">${iconForCategory(it.category)}</span>
        <span class="sym">${it.ticker}</span>
        <span class="price">${fmtPrice(it.price)}</span>
        <span class="delta ${d.cls}">${d.text}</span>
      </div>`;
  }).join("");
}
function adjustSpeed(){
  const width = track1().scrollWidth;
  const seconds = Math.max(10, Math.min(45, Math.round(width / 55)));
  document.documentElement.style.setProperty("--speed", `${seconds}s`);
}

// === Top 3 Gainers com gráficos ===
async function showTopGainers(items){
  const valid = items.filter(i => typeof i.change_pct === "number" && i.change_pct > 0);
  const top3 = [...valid].sort((a,b) => b.change_pct - a.change_pct).slice(0,3);
  const grid = document.getElementById("gainers-grid");
  grid.innerHTML = "";

  // Cria containers de gráficos
  top3.forEach(it=>{
    const id = it.ticker.replace(/[^a-zA-Z0-9]/g,"");
    const moeda = getCurrency(it.ticker);
    const card = document.createElement("div");
    card.className = "gainer-card";
    card.innerHTML = `
      <div class="g-head">
        <h3>${it.ticker}</h3>
        <small>${it.name || ""} • ${moeda}</small>
      </div>
      <div class="g-meta">
        <span class="g-pct">+${it.change_pct.toFixed(2)}%</span>
        <span>${fmtPrice(it.price)} ${moeda}</span>
      </div>
      <canvas id="chart-${id}" width="340" height="180"></canvas>
    `;
    grid.appendChild(card);
  });

  // Carrega e desenha cada gráfico separadamente
  for (const it of top3) {
    const id = it.ticker.replace(/[^a-zA-Z0-9]/g,"");
    const canvas = document.getElementById(`chart-${id}`);
    if (!canvas) continue;

    try {
      const res = await fetch(`/api/intraday/${encodeURIComponent(it.ticker)}`, {cache:"no-store"});
      const data = await res.json();
      if (!data.ok || !data.prices || data.prices.length < 2) continue;

      // Cada gráfico num contexto isolado
      const ctx = canvas.getContext("2d");
      new Chart(ctx, {
        type: "line",
        data: {
          labels: data.labels,
          datasets: [{
            data: data.prices,
            borderColor: "#00c853",
            backgroundColor: "rgba(0,200,83,0.15)",
            borderWidth: 2,
            fill: true,
            tension: 0.25,
            pointRadius: 0
          }]
        },
        options: {
          responsive: false,
          maintainAspectRatio: false,
          scales: { x: {display:false}, y:{display:false} },
          plugins: { legend:{display:false}, tooltip:{enabled:false} }
        }
      });
    } catch (e) {
      console.warn("Erro ao desenhar gráfico", it.ticker, e);
    }
  }
}

// === Carregar dados ===
async function loadQuotes(){
  try {
    const res = await fetch("/api/quotes", {cache:"no-store"});
    const data = await res.json();
    const items = data.items || [];

    // Atualiza ticker
    const html = buildHTML(items);
    track1().innerHTML = html;
    track2().innerHTML = html;
    setTimeout(adjustSpeed, 300);

    // Atualiza Top 3 Gainers
    await showTopGainers(items);
  } catch (err) {
    console.error("Erro a carregar cotações:", err);
  }
}

// === Inicialização ===
window.addEventListener("load", ()=>{
  loadQuotes();
  setInterval(loadQuotes, 90_000);
});
