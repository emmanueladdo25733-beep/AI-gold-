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
        print("Telegram Error:", e)

# ---------------- START MESSAGE ----------------
send_message("🚀 PRO Gold AI Bot is LIVE (Stable Version)")

# ---------------- SESSION FILTER ----------------
def is_trading_session():
    hour = datetime.utcnow().hour
    return 6 <= hour <= 21

# ---------------- NEWS FILTER (SAFE) ----------------
def is_news_time():
    try:
        url = "https://api.tradingeconomics.com/calendar?c=guest:guest&f=json"
        data = requests.get(url, timeout=5).json()

        now = datetime.utcnow()

        for event in data:
            if event.get("Importance") == 3 and "Date" in event:
                try:
                    event_time = datetime.fromisoformat(event["Date"].replace("Z", ""))
                    diff = abs((event_time - now).total_seconds()) / 60

                    if diff < 20:
                        return True
                except:
                    continue
    except:
        return False

    return False

# ---------------- STRUCTURE ----------------
def detect_structure(data):
    if len(data) < 5:
        return "RANGE"

    try:
        highs = data['High']
        lows = data['Low']

        if highs.iloc[-1] > highs.iloc[-3] and lows.iloc[-1] > lows.iloc[-3]:
            return "UP"
        elif highs.iloc[-1] < highs.iloc[-3] and lows.iloc[-1] < lows.iloc[-3]:
            return "DOWN"
    except:
        return "RANGE"

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

        try:
            data = yf.download(ticker, period="2d", interval="5m", progress=False)

            if data is None or data.empty or len(data) < 50:
                continue

            # Indicators
            data['MA20'] = data['Close'].rolling(20).mean()
            data['MA50'] = data['Close'].rolling(50).mean()

            last = data.iloc[-1]
            prev = data.iloc[-2]

            trend = "UP" if last['MA20'] > last['MA50'] else "DOWN"
            structure = detect_structure(data)

            signal = None

            # Liquidity sweep
            if last['High'] > prev['High'] and last['Close'] < prev['High']:
                signal = "SELL"

            elif last['Low'] < prev['Low'] and last['Close'] > prev['Low']:
                signal = "BUY"

            # Filters
            if signal == "BUY" and trend != "UP":
                continue

            if signal == "SELL" and trend != "DOWN":
                continue

            if structure == "RANGE":
                continue

            # Cooldown
            now = datetime.utcnow()

            if pair in last_signal_time:
                if now - last_signal_time[pair] < timedelta(minutes=COOLDOWN_MINUTES):
                    continue

            # Trade setup
            entry = float(last['Close'])

            if signal == "BUY":
                sl = float(last['Low'])
                tp = entry + (entry - sl) * 2
            else:
                sl = float(last['High'])
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
