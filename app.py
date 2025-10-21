from flask import Flask, jsonify, render_template
import yfinance as yf
import pandas as pd
import datetime

app = Flask(__name__)

# 🔹 Categorias base
CATEGORIES = {
    "STOCK": ["ABBV", "DCGO", "IMDX", "EDPR.LS", "EGL.LS", "NOS.LS", "SMC"],
    "INDEX": ["^NDX", "^PSI20"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "COMMODITY": ["GC=F", "ZC=F"]
}

@app.route("/")
def index():
    return render_template("index.html")

# 🔹 Endpoint principal
@app.route("/api/quotes")
def quotes():
    syms = [s for lst in CATEGORIES.values() for s in lst]
    df = yf.download(tickers=syms, period="2d", interval="1d", progress=False, threads=False)
    items = []

    for cat, tickers in CATEGORIES.items():
        for sym in tickers:
            try:
                info = yf.Ticker(sym).info
                name = info.get("shortName") or sym
                price = round(info.get("regularMarketPrice") or info.get("previousClose"), 4)
                change = round(info.get("regularMarketChange") or 0, 4)
                change_pct = round(info.get("regularMarketChangePercent") or 0, 2)
                currency = info.get("currency", "—")

                items.append({
                    "category": cat,
                    "ticker": sym,
                    "name": name,
                    "price": price,
                    "change": change,
                    "change_pct": change_pct,
                    "currency": currency
                })
            except Exception:
                continue

    items = [i for i in items if i["price"] is not None]
    return jsonify({"asof": datetime.datetime.utcnow().isoformat(), "items": items})

# 🔹 Endpoint para gráficos intraday
@app.route("/api/intraday/<symbol>")
def intraday(symbol):
    try:
        df = yf.download(tickers=symbol, period="1d", interval="5m", progress=False, threads=False, prepost=True)
        if df.empty:
            return jsonify({"ok": False, "msg": "Sem dados"}), 404
        df = df.reset_index()
        prices = [round(float(v), 4) for v in df["Close"].values]
        times = [t.strftime("%H:%M") for t in df["Datetime"]]
        return jsonify({"ok": True, "labels": times, "prices": prices})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
