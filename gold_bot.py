import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import asyncio
from telegram import Bot
from datetime import datetime
import pytz # Make sure to add 'pytz' to requirements.txt

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GHANA_TZ = pytz.timezone('Africa/Accra')

if not TOKEN or not CHAT_ID:
    print("❌ ERROR: Check Railway Variables!")
    exit(1)

bot = Bot(token=TOKEN)

async def send_msg(text):
    try:
        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
    except Exception as e:
        print(f"Telegram Error: {e}")

def analyze_setup(symbol, ticker):
    """SMC + Top-Down Analysis (Fixed for Series Ambiguity)"""
    try:
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        if df.empty or len(df) < 50: return None

        # Clean the data to get single float values
        close_price = float(df['Close'].iloc[-1].item())
        high_prev = float(df['High'].iloc[-3].item())
        low_curr = float(df['Low'].iloc[-1].item())
        
        # EMA for Trend
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        current_ema = float(df['EMA_200'].iloc[-1].item())

        # SMC Strategy: Trend + Fair Value Gap
        now_gmt = datetime.now(GHANA_TZ).strftime('%H:%M')
        
        # Bullish Setup
        if close_price > current_ema and low_curr > high_prev:
            sl = close_price - 4.0
            tp = close_price + 8.0
            return (f"🔥 *{symbol} BUY SETUP*\n"
                    f"📊 *Strategy:* SMC Trend + FVG\n"
                    f"💰 *Entry:* {close_price:.2f}\n"
                    f"🛑 *SL:* {sl:.2f} | ✅ *TP:* {tp:.2f}\n"
                    f"⏰ *Time:* {now_gmt} GMT")

        # Bearish Setup
        elif close_price < current_ema and high_prev > low_curr:
            sl = close_price + 4.0
            tp = close_price - 8.0
            return (f"🔥 *{symbol} SELL SETUP*\n"
                    f"📊 *Strategy:* SMC Trend + FVG\n"
                    f"💰 *Entry:* {close_price:.2f}\n"
                    f"🛑 *SL:* {sl:.2f} | ✅ *TP:* {tp:.2f}\n"
                    f"⏰ *Time:* {now_gmt} GMT")
                    
    except Exception as e:
        print(f"Analysis Error for {symbol}: {e}")
    return None

async def run_bot():
    await send_msg("🚀 *Gold Bot Online (GMT Timezone)*\nMonitoring XAUUSD & XAUEUR...")
    
    while True:
        # 1. Check for setups
        for name, ticker in {"XAUUSD": "GC=F", "XAUEUR": "EURGLD=X"}.items():
            signal = analyze_setup(name, ticker)
            if signal:
                await send_msg(signal)
        
        # 2. Heartbeat: If it's 8:00 AM GMT, send a status update
        now = datetime.now(GHANA_TZ)
        if now.hour == 8 and now.minute < 15:
            await send_msg("🌅 *Market Open:* Bot is scanning for London Session setups.")

        # Wait 15 minutes before next scan
        await asyncio.sleep(900)

if __name__ == "__main__":
    asyncio.run(run_bot())


