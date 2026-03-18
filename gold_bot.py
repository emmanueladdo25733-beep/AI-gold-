import os
import requests
import time
import yfinance as yf
from datetime import datetime, timedelta, timezone

# ---------------- SETTINGS ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

last_signal_time = {}
COOLDOWN_MINUTES = 30

# ---------------- TELEGRAM ----------------
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram Error:", e)

# ---------------- SAFE VALUE FUNCTION ----------------
def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except:
        return None

# ---------------- START MESSAGE ----------------
send_message("🚀 Gold AI Bot LIVE (Ultimate Stable)")

# ---------------- SESSION FILTER ----------------
def is_trading_session():
    hour = datetime.now(timezone.utc).hour
    return 6 <= hour <= 21

# ---------------- MAIN STRATEGY ----------------
def check_gold():

    if not is_trading_session():
        return

    pairs = {
        "XAUUSD": "GC=F",
        "XAUEUR": "GC=F"
    }

    for pair, ticker in pairs.items():

        try:
            data = yf.download(ticker, period="2d", interval="5m", progress=False)

            if data is None or data.empty:
                continue

            data = data.dropna()

            if len(data) < 50:
                continue

            # Indicators
            data['MA20'] = data['Close'].rolling(20).mean()
            data['MA50'] = data['Close'].rolling(50).mean()

            data = data.dropna()

            if len(data) < 50:
                continue

            last = data.iloc[-1]
            prev = data.iloc[-2]

            # SAFE extraction
            last_close = safe_float(last.get('Close'))
            last_high = safe_float(last.get('High'))
            last_low = safe_float(last.get('Low'))
            prev_high = safe_float(prev.get('High'))
            prev_low = safe_float(prev.get('Low'))
            ma20 = safe_float(data['MA20'].iloc[-1])
            ma50 = safe_float(data['MA50'].iloc[-1])

            # ❌ Skip if ANY value is bad
            if None in [last_close, last_high, last_low, prev_high, prev_low, ma20, ma50]:
                continue

            trend = "UP" if ma20 > ma50 else "DOWN"

            signal = None

            # Liquidity sweep
            if last_high > prev_high and last_close < prev_high:
                signal = "SELL"

            elif last_low < prev_low and last_close > prev_low:
                signal = "BUY"

            # Trend filter
            if signal == "BUY" and trend != "UP":
                continue

            if signal == "SELL" and trend != "DOWN":
                continue

            # Cooldown
            now = datetime.now(timezone.utc)

            if pair in last_signal_time:
                if now - last_signal_time[pair] < timedelta(minutes=COOLDOWN_MINUTES):
                    continue

            # Trade setup
            entry = last_close

            if signal == "BUY":
                sl = last_low
                tp = entry + (entry - sl) * 2
            elif signal == "SELL":
                sl = last_high
                tp = entry - (sl - entry) * 2
            else:
                continue

            last_signal_time[pair] = now

            send_message(
                f"{'📈' if signal=='BUY' else '📉'} {pair} {signal}\n"
                f"Entry: {entry:.2f}\n"
                f"SL: {sl:.2f}\n"
                f"TP: {tp:.2f}\n"
                f"Trend: {trend}"
            )

        except Exception as e:
            print("Loop Error:", e)

# ---------------- LOOP ----------------
while True:
    try:
        check_gold()
        time.sleep(300)
    except Exception as e:
        print("Main Loop Error:", e)
        time.sleep(60)
