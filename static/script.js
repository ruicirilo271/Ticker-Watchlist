const track1 = () => document.querySelector(".ticker-track.first");
const track2 = () => document.querySelector(".ticker-track.second");
const wrap = () => document.querySelector(".ticker-wrap");

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
  return {text: `${arrow} ${sign1}${chg.toFixed(2)} (${sign2}${pct.toFixed(2)}%)`, cls};
}
function catClass(cat){
  switch(cat){
    case "STOCK": return "cat cat-stock";
    case "CRYPTO": return "cat cat-crypto";
    case "INDEX": return "cat cat-index";
    case "COMMODITY": return "cat cat-commodity";
    default: return "cat";
  }
}
function buildHTML(items){
  return items.map(it=>{
    const d = fmtDelta(it.change, it.change_pct);
    return `
      <div class="item">
        <span class="${catClass(it.category)}">[${it.category}]</span>
        <span class="sym">${it.ticker}</span>
        <span class="name">${it.name || ""}</span>
        <span class="price">${fmtPrice(it.price)}</span>
        <span class="delta ${d.cls}">${d.text}</span>
      </div>
    `;
  }).join("");
}
function adjustSpeed(){
  // velocidade proporcional ao comprimento do conteúdo
  const width = track1().scrollWidth;
  const seconds = Math.max(25, Math.min(90, Math.round(width / 28)));
  document.documentElement.style.setProperty("--speed", `${seconds}s`);
}
async function loadQuotes(){
  try{
    const res = await fetch("/api/quotes", {cache:"no-store"});
    if(!res.ok) throw new Error("Falha /api/quotes");
    const data = await res.json();
    const items = data.items || [];
    const html = buildHTML(items);
    track1().innerHTML = html;
    track2().innerHTML = html; // pista espelhada
    adjustSpeed();
  }catch(e){
    console.error("Erro a carregar cotações:", e);
  }
}
// evita empilhar pedidos quando a aba não está visível
document.addEventListener("visibilitychange", ()=>{
  if(document.visibilityState === "visible") loadQuotes();
});
window.addEventListener("load", ()=>{
  loadQuotes();
  setInterval(loadQuotes, 10_000); // 10s
});
