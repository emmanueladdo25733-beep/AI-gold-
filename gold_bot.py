import os
import requests
import pandas as pd
import time
import yfinance as yf

# ------------------- SETTINGS ------------------"   # Replace with your Telegram bot token
BOT_TOKEN= os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TRADINGECONOMICS_KEY = "674e7ba864f245e:fln2e3inbeultxt"
send_start_message = True
NEWS_WARNING_WINDOW_MINUTES = 60  # block trades for 60 min before news

# ------------------- FUNCTIONS -------------------
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text
        })
        print(response.text)
    except Exception as e:
        print("Error sending message:", e)

    last = data.iloc[-1]
    prev = data.iloc[-2]

    if last['High'] > prev['High'] and last['Close'] < prev['High']:
        return "SELL"

    if last['Low'] < prev['Low'] and last['Close'] > prev['Low']:
        return "BUY"

    return None
    def get_trend(data):

        ma20 = data['Close'].rolling(20).mean()
    ma50 = data['Close'].rolling(50).mean()

    if ma20.iloc[-1] > ma50.iloc[-1]:
        return "UP"

    if ma20.iloc[-1] < ma50.iloc[-1]:
        return "DOWN"

    return "RANGE"
    def check_gold_signals():

        pairs = {
        "XAUUSD": "GC=F",
        "XAUEUR": "XAUEUR=X"
    }

    for name, ticker in pairs.items():

        data = yf.download(ticker, period="7d", interval="5m")

        sweep = detect_liquidity_sweep(data)
        trend = get_trend(data)

        if sweep == "BUY" and trend == "UP":
            send_message(f"📈 {name} BUY setup detected")

        if sweep == "SELL" and trend == "DOWN":
            send_message(f"📉 {name} SELL setup detected")
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
        gold5 = yf.download("GC=F", period="7d", interval="5m", progress=False)
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
send_message("Bot test message - system running")
# Wait 4 minutes before next check
time.sleep(240)
