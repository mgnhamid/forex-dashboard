# EUR/USD & Multi-Pair Forex Analyzer - v7.2 PRO ONLINE (Flask Version)
# Author: Abdelhamid & ChatGPT

from flask import Flask, render_template_string
import requests
from datetime import datetime, timedelta
import threading
import time

# === Config ===
API_KEY = "ff9edc6cb1b84603a8c993d85693f42d"
BASE_URL = "https://api.twelvedata.com/time_series"
SYMBOLS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]
INTERVAL = "15min"
LIMIT = 50

# === Telegram Config ===
TELEGRAM_TOKEN = "8370584987:AAEwMxokse8EGNRcFFsHxxOOqjUo-cQ8Rdo"
TELEGRAM_CHAT_ID = "1960098673"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=data)

app = Flask(__name__)

def fetch_candles(symbol):
    params = {
        "symbol": symbol,
        "interval": INTERVAL,
        "apikey": API_KEY,
        "outputsize": LIMIT
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    return data.get("values", [])

def get_direction(candles):
    closes = [float(c["close"]) for c in candles[::-1]]
    if closes[-1] > closes[0]:
        return "Uptrend"
    elif closes[-1] < closes[0]:
        return "Downtrend"
    else:
        return "Sideways"

def analyze_signal(candles):
    now_utc = datetime.utcnow()
    candles = [c for c in candles if datetime.strptime(c["datetime"], "%Y-%m-%d %H:%M:%S") <= now_utc]
    if not candles:
        return None
    last = candles[0]
    close = float(last["close"])
    open_ = float(last["open"])
    high = float(last["high"])
    low = float(last["low"])

    direction = get_direction(candles[:10])

    signal = None
    if direction == "Uptrend" and close > open_:
        signal = "BUY"
    elif direction == "Downtrend" and close < open_:
        signal = "SELL"

    if not signal:
        return None

    last_time = datetime.strptime(last["datetime"], "%Y-%m-%d %H:%M:%S")
    local_time = (last_time + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    next_candle_time = (last_time + timedelta(minutes=15, hours=1)).strftime("%Y-%m-%d %H:%M")

    return {
        "symbol": candles[0].get("symbol", "?"),
        "signal": signal,
        "entry": close,
        "sl": round(low if signal == "BUY" else high, 5),
        "tp": round(close + 0.002 if signal == "BUY" else close - 0.002, 5),
        "confidence": 100,
        "direction": direction,
        "time": local_time,
        "next_time": next_candle_time
    }

def auto_send_signals():
    sent = {}
    while True:
        for symbol in SYMBOLS:
            candles = fetch_candles(symbol)
            if candles:
                result = analyze_signal(candles)
                if result:
                    key = f"{symbol}_{result['time']}"
                    if key not in sent:
                        message = f"""
📊 <b>{symbol}</b>
🕒 Last Candle: {result['time']}
📆 Entry Candle: {result['next_time']}
📈 Direction: <b>{result['direction']}</b>
💡 Signal: <b>{result['signal']}</b>
🎯 Entry: {result['entry']}
🎯 TP: {result['tp']}
🛑 SL: {result['sl']}
✅ Confidence: {result['confidence']}%
                        """
                        send_telegram_message(message)
                        sent[key] = True
        time.sleep(60)

# Start the auto sender
threading.Thread(target=auto_send_signals, daemon=True).start()

@app.route("/")
def index():
    results = []
    for symbol in SYMBOLS:
        candles = fetch_candles(symbol)
        if candles:
            analysis = analyze_signal(candles)
            if analysis:
                analysis["symbol"] = symbol
                results.append(analysis)
    return render_template_string(TEMPLATE, results=results)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Forex Signal Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #121212; color: #fff; }
        .card { background-color: #1f1f1f; margin-bottom: 20px; }
    </style>
</head>
<body>
<div class="container py-5">
    <h2 class="mb-4">📊 Forex Signal Dashboard (15m)</h2>
    <button onclick="location.reload()" class="btn btn-outline-light mb-4">🔄 تحديث التوصيات</button>
    {% for r in results %}
    <div class="card p-3">
        <h4>{{ r.symbol }}</h4>
        <p>🕒 Time (last candle): {{ r.time }}</p>
        <p>📆 Suggested entry candle (upcoming): {{ r.next_time }}</p>
        <p>📈 Direction: <strong>{{ r.direction }}</strong></p>
        <p>💡 Signal: <strong>{{ r.signal }}</strong></p>
        <p>🎯 Entry: {{ r.entry }} | 🎯 TP: {{ r.tp }} | 🛑 SL: {{ r.sl }}</p>
        <p>✅ Confidence: {{ r.confidence }}%</p>
    </div>
    {% endfor %}
</div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)
<PASTE CODE FROM canvas here>
