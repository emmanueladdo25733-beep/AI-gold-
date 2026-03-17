import os
import requests
import pandas as pd
import time
import yfinance as yf
from datetime import datetime, timedelta

# ------------------- SETTINGS -------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TRADINGECONOMICS_KEY = "674e7ba864f245e:fln2e3inbeultxt"
NEWS_WARNING_WINDOW_MINUTES = 60 

# ------------------- FUNCTIONS -------------------

def send_message(text):
    """Simple function to send alerts to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text
        }
        response = requests.post(url, data=payload)
        print(f"Telegram response: {response.status_code}")
    except Exception as e:
        print(f"Error sending message: {e}")

def detect_liquidity_sweep(data):
    """Analyzes data to find BUY/SELL signals"""
    if data.empty or len(data) < 2:
        return None
        
    # Ensure we are looking at the right columns
    last = data.iloc[-1]
    prev = data.iloc[-2]

    if last['High'] > prev['High'] and last['Close'] < prev['High']:
        return "SELL"

    if last['Low'] < prev['Low'] and last['Close'] > prev['Low']:
        return "BUY"

    return None

def get_trend(data):
    """Calculates Moving Average trend"""
    if len(data) < 50:
        return "WAITING"
        
    ma20 = data['Close'].rolling(20).mean()
    ma50 = data['Close'].rolling(50).mean()

    if ma20.iloc[-1] > ma50.iloc[-1]:
        return "UP"
    elif ma20.iloc[-1] < ma50.iloc[-1]:
        return "DOWN"
    return "RANGE"

def get_upcoming_news():
    """Checks for high-impact US news"""
    url = f"https://api.tradingeconomics.com/calendar/country/united%20states?c={TRADINGECONOMICS_KEY}&importance=3"
    try:
        resp = requests.get(url, timeout=10)
        events = resp.json()
        upcoming = []
        now = datetime.utcnow()
        for event in events:
            # Adjust date parsing based on actual API response format
            event_time = datetime.strptime(event['date'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
            if now <= event_time <= now + timedelta(minutes=NEWS_WARNING_WINDOW_MINUTES):
                upcoming.append(f"{event_time.strftime('%H:%M')} - {event['event']}")
        return upcoming
    except Exception as e:
        print(f"News API Error: {e}")
        return []

# ------------------- MAIN LOOP -------------------

send_message("🚀 Bot is now LIVE on Railway")

while True:
    try:
        # ----- 15-minute trend -----
        gold15 = yf.download("GC=F", period="2d", interval="15m", progress=False)
        if gold15.empty:
            print("No data received for GC=F (15m)")
            time.sleep(60)
            continue
            
        # Fix for yfinance multi-index columns
        if isinstance(gold15.columns, pd.MultiIndex):
            gold15.columns = gold15.columns.get_level_values(0)

        close15 = gold15["Close"]
        ma20_15 = close15.rolling(20).mean()
        current_trend = "BULLISH" if close15.iloc[-1] > ma20_15.iloc[-1] else "BEARISH"

        # ----- Support & Resistance -----
        resistance = gold15["High"].rolling(20).max().iloc[-1]
        support = gold15["Low"].rolling(20).min().iloc[-1]

        # ----- 5-minute entry -----
        gold5 = yf.download("GC=F", period="2d", interval="5m", progress=False)
        if gold5.empty:
            time.sleep(60)
            continue
            
        if isinstance(gold5.columns, pd.MultiIndex):
            gold5.columns = gold5.columns.get_level_values(0)

        price = float(gold5["Close"].iloc[-1])
        
        # Check liquidity sweep on 5m
        sweep_signal = detect_liquidity_sweep(gold5)

        # ----- Check upcoming news -----
        upcoming_news = get_upcoming_news()
        if upcoming_news:
            news_msg = "⚠️ HIGH IMPACT NEWS DETECTED\n" + "\n".join(upcoming_news)
            send_message(news_msg)
            print("Trading paused due to news.")
        else:
            # ----- Logic for generating Trade Alerts -----
            # Bullish Setup
            if current_trend == "BULLISH" and price <= (support + 1):
                entry = price
                sl = support - 2
                tp = entry + (entry - sl) * 1.5
                msg = f"📈 GOLD BUY SETUP\n\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nTrend: Bullish"
                send_message(msg)

            # Bearish Setup
            elif current_trend == "BEARISH" and price >= (resistance - 1):
                entry = price
                sl = resistance + 2
                tp = entry - (sl - entry) * 1.5
                msg = f"📉 GOLD SELL SETUP\n\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nTrend: Bearish"
                send_message(msg)

    except Exception as e:
        print(f"Loop Error: {e}")

    # Wait 5 minutes before the next check
    print("Cycle complete. Waiting 300 seconds...")
    time.sleep(300)
