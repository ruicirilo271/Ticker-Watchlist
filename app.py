import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, render_template

BASE_DIR = Path(__file__).parent
app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------- Utils ----------
CRYPTO_MAP = {
    "btc": "BTC-USD", "bitcoin": "BTC-USD",
    "eth": "ETH-USD", "ethereum": "ETH-USD",
    "sol": "SOL-USD", "solana": "SOL-USD",
    "ada": "ADA-USD", "cardano": "ADA-USD",
    "xrp": "XRP-USD", "ripple": "XRP-USD",
}

CAT_ORDER = ["STOCK", "INDEX", "CRYPTO", "COMMODITY"]

def load_watchlist() -> list[dict]:
    """
    Lê watchlist.json no formato:
    {
      "stocks": ["EDPR.LS", "VKTX", ...],
      "crypto": ["bitcoin", "solana", ...],
      "commodities": [],
      "indices": ["^PSI20", "^NDX"]
    }
    Devolve lista normalizada: [{category, ticker, name}]
    """
    wl_path = BASE_DIR / "watchlist.json"
    data = json.loads(wl_path.read_text(encoding="utf-8"))

    items: list[dict] = []

    # Stocks
    for sym in data.get("stocks", []):
        t = str(sym).strip()
        if t:
            items.append({"category": "STOCK", "ticker": t.upper(), "name": t.upper()})

    # Indices
    for sym in data.get("indices", []):
        t = str(sym).strip()
        if t:
            items.append({"category": "INDEX", "ticker": t, "name": t})

    # Commodities (se vierem já em formato Yahoo, usa direto)
    for sym in data.get("commodities", []):
        t = str(sym).strip()
        if t:
            items.append({"category": "COMMODITY", "ticker": t.upper(), "name": t.upper()})

    # Crypto (normaliza nomes → Yahoo)
    for c in data.get("crypto", []):
        k = str(c).strip().lower()
        t = CRYPTO_MAP.get(k, k.upper())
        # se não mapear, tenta "<SYMBOL>-USD" como fallback
        if "-USD" not in t and t.isalpha():
            t = f"{t.upper()}-USD"
        name = {"BTC-USD":"Bitcoin", "ETH-USD":"Ethereum", "SOL-USD":"Solana"}.get(t, k.capitalize())
        items.append({"category": "CRYPTO", "ticker": t, "name": name})

    # remover duplicados preservando ordem (ticker+cat)
    seen = set()
    unique = []
    for it in items:
        key = (it["category"], it["ticker"])
        if key not in seen:
            seen.add(key)
            unique.append(it)

    # ordenar por categoria “Bloomberg-like”
    cat_rank = {c: i for i, c in enumerate(CAT_ORDER)}
    unique.sort(key=lambda x: (cat_rank.get(x["category"], 99), x["ticker"]))
    return unique

def _extract_last(df, ticker):
    """Último preço 1m; se não houver, devolve None."""
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        col = ("Close", ticker)
        if col in df.columns:
            s = df[col].dropna()
            return float(s.iloc[-1]) if not s.empty else None
    elif "Close" in df.columns:
        s = df["Close"].dropna()
        return float(s.iloc[-1]) if not s.empty else None
    return None

def _extract_prev_close(df, ticker):
    """Fecho D-1 diário; se não houver, devolve None."""
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        col = ("Close", ticker)
        if col in df.columns:
            s = df[col].dropna()
            if len(s) >= 2: return float(s.iloc[-2])
            if len(s) == 1: return float(s.iloc[0])
    elif "Close" in df.columns:
        s = df["Close"].dropna()
        if len(s) >= 2: return float(s.iloc[-2])
        if len(s) == 1: return float(s.iloc[0])
    return None

def fetch_quotes(items: list[dict]) -> list[dict]:
    """
    Faz download em lote (1m e 1d) para TODOS os tickers.
    Calcula preço atual, variação e variação %.
    """
    syms = [it["ticker"] for it in items]

    try:
        df_1m = yf.download(
            tickers=syms, period="5d", interval="1m",
            auto_adjust=False, progress=False, threads=False
        )
    except Exception:
        df_1m = pd.DataFrame()

    try:
        df_1d = yf.download(
            tickers=syms, period="10d", interval="1d",
            auto_adjust=False, progress=False, threads=False
        )
    except Exception:
        df_1d = pd.DataFrame()

    result = []
    for it in items:
        t = it["ticker"]
        name = it["name"]
        cat = it["category"]

        last = _extract_last(df_1m, t)
        prev = _extract_prev_close(df_1d, t)

        # fallback: usar último 1d como "last" se 1m não existe
        if last is None and df_1d is not None and not df_1d.empty:
            if isinstance(df_1d.columns, pd.MultiIndex):
                col = ("Close", t)
                if col in df_1d.columns:
                    s = df_1d[col].dropna()
                    if not s.empty: last = float(s.iloc[-1])
            elif "Close" in df_1d.columns:
                s = df_1d["Close"].dropna()
                if not s.empty: last = float(s.iloc[-1])

        if last is None or prev is None or prev == 0:
            result.append({
                "category": cat, "ticker": t, "name": name,
                "price": None, "change": None, "change_pct": None
            })
            continue

        chg = last - prev
        chg_pct = (chg / prev) * 100.0

        # precisão: índices/cripto tendem a precisar de + casas decimais
        prec = 4 if (t.endswith("-USD") or t.startswith("^") or abs(last) < 1) else 2

        result.append({
            "category": cat,
            "ticker": t,
            "name": name,
            "price": round(float(last), prec),
            "change": round(float(chg), prec),
            "change_pct": round(float(chg_pct), 2),
        })

    return result

# ---------- Rotas ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/quotes")
def api_quotes():
    items = load_watchlist()
    quotes = fetch_quotes(items)
    return jsonify({
        "asof": datetime.now(timezone.utc).isoformat(),
        "items": quotes
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
