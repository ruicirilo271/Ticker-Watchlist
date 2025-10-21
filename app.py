from flask import Flask, render_template, jsonify
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf
from pathlib import Path
import json

app = Flask(__name__, static_folder="static", template_folder="templates")
BASE_DIR = Path(__file__).parent

# ==================== carregar watchlist ====================
def load_watchlist():
    wl_path = BASE_DIR / "watchlist.json"
    data = json.loads(wl_path.read_text(encoding="utf-8"))
    items = []
    def add(cat, lst):
        for t in lst:
            t = t.strip()
            if t:
                items.append({"category": cat, "ticker": t, "name": t})
    add("STOCK", data.get("stocks", []))
    add("INDEX", data.get("indices", []))
    add("COMMODITY", data.get("commodities", []))
    add("CRYPTO", data.get("crypto", []))
    return items

# ==================== preços ====================
def fetch_quotes(items):
    syms = [i["ticker"] for i in items]
    df = pd.DataFrame()
    try:
        df = yf.download(tickers=syms, period="2d", interval="1d", progress=False, threads=False)
    except Exception:
        pass

    out = []
    for it in items:
        t = it["ticker"]
        name = it["name"]
        cat = it["category"]
        price = prev = None
        try:
            if isinstance(df.columns, pd.MultiIndex):
                col = ("Close", t)
                if col in df.columns:
                    s = df[col].dropna()
                    if len(s) >= 1:
                        price = float(s.iloc[-1])
                    if len(s) >= 2:
                        prev = float(s.iloc[-2])
            elif "Close" in df.columns:
                s = df["Close"].dropna()
                if len(s) >= 1:
                    price = float(s.iloc[-1])
                if len(s) >= 2:
                    prev = float(s.iloc[-2])
        except Exception:
            pass

        change = change_pct = None
        if price and prev:
            change = price - prev
            change_pct = (change / prev) * 100.0

        out.append({
            "category": cat,
            "ticker": t,
            "name": name,
            "price": round(price, 4) if price else None,
            "change": round(change, 4) if change else None,
            "change_pct": round(change_pct, 2) if change_pct else None
        })
    return out


# ==================== endpoints ====================
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


@app.route("/api/intraday/<path:ticker>")
def api_intraday(ticker):
    """
    Gráfico intraday real — 1 dia, intervalos de 5 minutos
    """
    t = str(ticker).strip()
    try:
        df = yf.download(tickers=t, period="1d", interval="5m", progress=False, threads=False, prepost=True)
        if df.empty or "Close" not in df.columns:
            return jsonify({"ok": False, "error": "no data"})
        s = df["Close"].dropna()
        labels = [idx.strftime("%H:%M") for idx in s.index.to_pydatetime()]
        prices = [round(float(v), 4) for v in s.values]
        return jsonify({"ok": True, "labels": labels, "prices": prices})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
