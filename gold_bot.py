import os
import requests
import pandas as pd
import time
import yfinance as yf
from datetime import datetime, timedelta

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
        print("Error:", e)

# ---------------- START MESSAGE ----------------
send_message("🚀 PRO Gold AI Bot is LIVE (XAUUSD & XAUEUR)")

# ---------------- SESSION FILTER ----------------
def is_trading_session():
    hour = datetime.utcnow().hour
    return 6 <= hour <= 21   # London + NY (optimized)

# ---------------- LIGHT NEWS FILTER ----------------
def is_news_time():
    try:
        url = "https://api.tradingeconomics.com/calendar?c=guest:guest&f=json"
        data = requests.get(url).json()

        now = datetime.utcnow()

        for event in data:
            if event.get("Importance") == 3:
                event_time = datetime.fromisoformat(event["Date"].replace("Z", ""))
                diff = abs((event_time - now).total_seconds()) / 60

                if diff < 20:  # only block 20 mins
                    return True
    except:
        return False

    return False

# ---------------- STRUCTURE LOGIC ----------------
def detect_structure(data):
    highs = data['High']
    lows = data['Low']

    if highs.iloc[-1] > highs.iloc[-3] and lows.iloc[-1] > lows.iloc[-3]:
        return "UP"
    elif highs.iloc[-1] < highs.iloc[-3] and lows.iloc[-1] < lows.iloc[-3]:
        return "DOWN"
    return "RANGE"

# ---------------- MAIN STRATEGY ----------------
def check_gold():

    if not is_trading_session():
        return

    if is_news_time():
        return

    pairs = {
        "XAUUSD": "GC=F",
        "XAUEUR": "GC=F"
    }

    for pair, ticker in pairs.items():

        data = yf.download(ticker, period="2d", interval="5m", progress=False)

        if data.empty:
            continue

        # Indicators
        data['MA20'] = data['Close'].rolling(20).mean()
        data['MA50'] = data['Close'].rolling(50).mean()

        trend = "UP" if data['MA20'].iloc[-1] > data['MA50'].iloc[-1] else "DOWN"

        structure = detect_structure(data)

        last = data.iloc[-1]
        prev = data.iloc[-2]

        signal = None

        # Liquidity sweep + confirmation
        if last['High'] > prev['High'] and last['Close'] < prev['High']:
            signal = "SELL"

        elif last['Low'] < prev['Low'] and last['Close'] > prev['Low']:
            signal = "BUY"

        # ---------------- FILTER ----------------
        if signal == "BUY" and trend != "UP":
            continue

        if signal == "SELL" and trend != "DOWN":
            continue

        if structure == "RANGE":
            continue

        # ---------------- COOLDOWN ----------------
        now = datetime.utcnow()

        if pair in last_signal_time:
            if now - last_signal_time[pair] < timedelta(minutes=COOLDOWN_MINUTES):
                continue

        # ---------------- EXECUTION ----------------
        entry = last['Close']

        if signal == "BUY":
            sl = last['Low']
            tp = entry + (entry - sl) * 2

        else:
            sl = last['High']
            tp = entry - (sl - entry) * 2

        last_signal_time[pair] = now

        send_message(
            f"{'📈' if signal=='BUY' else '📉'} {pair} {signal}\n"
            f"Entry: {entry:.2f}\n"
            f"SL: {sl:.2f}\n"
            f"TP: {tp:.2f}\n"
            f"Trend: {trend}\n"
            f"Structure: {structure}\n"
            f"Confidence: ⭐⭐⭐⭐"
        )

# ---------------- LOOP ----------------
while True:
    check_gold()
    time.sleep(300)
