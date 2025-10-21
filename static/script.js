async function loadTopGainers() {
  const res = await fetch("/api/quotes");
  const data = await res.json();
  const all = data.items || [];

  // 🔹 Ordena por variação percentual
  const top = all
    .filter(i => i.change_pct > 0)
    .sort((a, b) => b.change_pct - a.change_pct)
    .slice(0, 3);

  const container = document.getElementById("top-gainers");
  container.innerHTML = "";

  for (const t of top) {
    const card = document.createElement("div");
    card.className = "chart-card";

    const header = document.createElement("h2");
    header.innerHTML = `${t.name} (${t.ticker}) <span class="chg">+${t.change_pct.toFixed(2)}%</span>`;
    card.appendChild(header);

    const price = document.createElement("div");
    price.className = "price";
    price.innerHTML = `${t.price} <small class="currency">${t.currency || ""}</small>`;
    card.appendChild(price);

    const canvas = document.createElement("canvas");
    card.appendChild(canvas);
    container.appendChild(card);

    // 🔹 Carrega gráfico intraday
    try {
      const intradayRes = await fetch(`/api/intraday/${t.ticker}`);
      const intradayData = await intradayRes.json();
      if (!intradayData.ok) continue;

      new Chart(canvas, {
        type: "line",
        data: {
          labels: intradayData.labels,
          datasets: [{
            data: intradayData.prices,
            borderColor: "#00e676",
            backgroundColor: "rgba(0,230,118,0.15)",
            fill: true,
            tension: 0.3,
            borderWidth: 2
          }]
        },
        options: {
          scales: { x: { display: false }, y: { display: false } },
          plugins: { legend: { display: false } },
          elements: { point: { radius: 0 } },
        }
      });
    } catch (err) {
      console.error("Erro ao gerar gráfico:", err);
    }
  }
}

async function loadTicker() {
  const res = await fetch("/api/quotes");
  const data = await res.json();
  const items = data.items || [];

  const track1 = document.querySelector(".ticker-track.first");
  const track2 = document.querySelector(".ticker-track.second");

  const html = items.map(it => `
    <div class="item">
      <span class="sym">${it.ticker}</span>
      <span class="name">${it.name}</span>
      <span class="price">${it.price} <small class="currency">${it.currency || ""}</small></span>
      <span class="delta ${it.change > 0 ? "up" : it.change < 0 ? "down" : "flat"}">
        ${(it.change > 0 ? "▲" : it.change < 0 ? "▼" : "•")} ${it.change_pct.toFixed(2)}%
      </span>
    </div>
  `).join("");

  track1.innerHTML = html;
  track2.innerHTML = html;
}

// Inicializa
window.addEventListener("load", () => {
  loadTicker();
  loadTopGainers();
  setInterval(loadTicker, 90_000);
  setInterval(loadTopGainers, 180_000);
});
