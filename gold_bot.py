import os
import requests
import pandas as pd
import time
import yfinance as yf
from datetime import datetime

# ---------------- SETTINGS ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

send_start_message = True
NEWS_WARNING_WINDOW_MINUTES = 60

last_signal = None

# ---------------- TELEGRAM ----------------
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Error:", e)

# ---------------- START MESSAGE ----------------
if send_start_message:
    send_message("🚀 Gold AI Bot is LIVE and scanning XAUUSD & XAUEUR")

# ---------------- SESSION FILTER ----------------
def is_trading_session():
    now = datetime.utcnow().hour

    # London + New York sessions (approx)
    if 7 <= now <= 20:
        return True
    return False

# ---------------- NEWS FILTER ----------------
def high_impact_news():
    try:
        url = "https://api.tradingeconomics.com/calendar?c=guest:guest&f=json"
        response = requests.get(url).json()

        now = datetime.utcnow()

        for event in response:
            if event.get("Importance") == 3:
                event_time = datetime.fromisoformat(event["Date"].replace("Z", ""))
                diff = abs((event_time - now).total_seconds()) / 60

                if diff < NEWS_WARNING_WINDOW_MINUTES:
                    return True
    except:
        return False

    return False

# ---------------- MAIN STRATEGY ----------------
def check_gold_signals():
    global last_signal

    if not is_trading_session():
        return

    if high_impact_news():
        return

    pairs = {
        "XAUUSD": "GC=F",
        "XAUEUR": "GC=F"
    }

    for pair_name, ticker in pairs.items():

        data = yf.download(ticker, period="2d", interval="5m", progress=False)

        if data.empty:
            continue

        # Indicators
        data['MA20'] = data['Close'].rolling(20).mean()
        data['MA50'] = data['Close'].rolling(50).mean()

        last = data.iloc[-1]
        prev = data.iloc[-2]

        trend = None

        if last['MA20'] > last['MA50']:
            trend = "UP"
        elif last['MA20'] < last['MA50']:
            trend = "DOWN"

        signal = None

        # Liquidity sweep
        if last['High'] > prev['High'] and last['Close'] < prev['High']:
            signal = "SELL"

        if last['Low'] < prev['Low'] and last['Close'] > prev['Low']:
            signal = "BUY"

        # ---------------- EXECUTION ----------------
        if signal == "BUY" and trend == "UP" and last_signal != f"{pair_name}_BUY":

            entry = last['Close']
            sl = last['Low']
            tp = entry + (entry - sl) * 2

            last_signal = f"{pair_name}_BUY"

            send_message(
                f"📈 {pair_name} BUY\n"
                f"Entry: {entry}\n"
                f"SL: {sl}\n"
                f"TP: {tp}\n"
                f"Session: London/NY\n"
                f"Confidence: ⭐⭐⭐⭐"
            )

        elif signal == "SELL" and trend == "DOWN" and last_signal != f"{pair_name}_SELL":

            entry = last['Close']
            sl = last['High']
            tp = entry - (sl - entry) * 2

            last_signal = f"{pair_name}_SELL"

            send_message(
                f"📉 {pair_name} SELL\n"
                f"Entry: {entry}\n"
                f"SL: {sl}\n"
                f"TP: {tp}\n"
                f"Session: London/NY\n"
                f"Confidence: ⭐⭐⭐⭐"
            )

# ---------------- LOOP ----------------
while True:
    check_gold_signals()
    time.sleep(300)  # 5 minutes
