import requests
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta

# ------------------- SETTINGS -------------------
BOT_TOKEN = "8631230640:AAFgKCI5th8KSi5DhWjvNV3vWegF2Y6lTOg"   # Replace with your Telegram bot token
CHAT_ID = 5374524094 send_start_message = True
TRADINGECONOMICS_KEY = "674e7ba864f245e:fln2e3inbeultxt"
NEWS_WARNING_WINDOW_MINUTES = 60  # block trades for 60 min before news

# ------------------- FUNCTIONS -------------------
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    if send_start_message:
    send_message("Gold AI Bot Started Successfully 🚀")

def get_upcoming_news():
    url = f"https://api.tradingeconomics.com/calendar/country/united%20states?c={TRADINGECONOMICS_KEY}&importance=3"
    try:
        resp = requests.get(url)
        events = resp.json()
        upcoming = []
        now = datetime.utcnow()
        for event in events:
            event_time = datetime.strptime(event['date'], '%Y-%m-%dT%H:%M:%S')
            if now <= event_time <= now + timedelta(minutes=NEWS_WARNING_WINDOW_MINUTES):
                upcoming.append(f"{event_time.strftime('%H:%M')} - {event['event']}")
        return upcoming
    except:
        return []

# ------------------- MAIN LOOP -------------------
while True:
    try:
        # ----- 15-minute trend -----
        gold15 = yf.download("GC=F", period="1d", interval="15m")
        if gold15.empty:
            time.sleep(60)
            continue
        gold15.columns = gold15.columns.get_level_values(0)
        close15 = gold15["Close"]
        ma20 = close15.rolling(20).mean()
        trend = "BULLISH" if close15.iloc[-1] > ma20.iloc[-1] else "BEARISH"

        # ----- Support & Resistance -----
        resistance = gold15["High"].rolling(20).max().iloc[-1]
        support = gold15["Low"].rolling(20).min().iloc[-1]

        # ----- 5-minute entry -----
        gold5 = yf.download("GC=F", period="1d", interval="5m")
        if gold5.empty:
            time.sleep(60)
            continue
        gold5.columns = gold5.columns.get_level_values(0)
        price = float(gold5["Close"].iloc[-1])
        recent_high = float(gold5["High"].tail(10).max())
        recent_low = float(gold5["Low"].tail(10).min())

        # ----- Check upcoming news -----
        upcoming_news = get_upcoming_news()
        if upcoming_news:
            message = "⚠️ HIGH IMPACT NEWS IN NEXT 60 MINUTES\n"
            for e in upcoming_news:
                message += e + "\n"
            message += "Trading paused until news passes"
            send_message(message)

        else:
            # ----- Check liquidity sweep setups -----
            send_setup = False
            message = ""
            # Bullish setup
            if trend == "BULLISH" and price <= support + 1:
                entry = price
                sl = support - 2
                tp = entry + (entry - sl) * 1.5
                message = f"""
GOLD BUY SETUP

Entry: {entry:.2f}
Stop Loss: {sl:.2f}
Take Profit: {tp:.2f}

Reason: Support zone + Bullish trend + Liquidity sweep
"""
                send_setup = True
            # Bearish setup
            elif trend == "BEARISH" and price >= resistance - 1:
                entry = price
                sl = resistance + 2
                tp = entry - (sl - entry) * 1.5
                message = f"""
GOLD SELL SETUP

Entry: {entry:.2f}
Stop Loss: {sl:.2f}
Take Profit: {tp:.2f}

Reason: Resistance zone + Bearish trend + Liquidity sweep
"""
                send_setup = True

            # Send message only if a setup exists
            if send_setup:
                send_message(message)

    except Exception as e:
        print("Error:", e)

    # Wait 4 minutes before next check
    time.sleep(240)
