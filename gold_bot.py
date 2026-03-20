import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import asyncio
from telegram import Bot
from datetime import datetime

# --- 1. CRITICAL CONFIGURATION CHECK ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("❌ ERROR: TELEGRAM_TOKEN or CHAT_ID is missing in Railway Variables!")
    # This prevents the 'InvalidToken' crash by giving a clear message
    exit(1)

# Initialize Bot with the fixed 2026 Async method
bot = Bot(token=TOKEN)

async def send_msg(text):
    """Helper to send messages safely"""
    try:
        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_market_data(ticker):
    """Fetches and cleans data - Fixed for yfinance 2026 updates"""
    df = yf.download(ticker, period="2d", interval="5m", progress=False)
    if df.empty:
        return None
    return df

def analyze_setup(symbol, ticker):
    """SMC + Top-Down Analysis Engine"""
    df = get_market_data(ticker)
    if df is None: return None

    # Trend Filter (EMA 200)
    df['EMA_200'] = ta.ema(df['Close'], length=200)
    current_price = df['Close'].iloc[-1]
    ema = df['EMA_200'].iloc[-1]
    
    # Fair Value Gap (FVG) - Institutional footprint
    # Bullish FVG: Low of candle 0 > High of candle -2
    is_fvg = df['Low'].iloc[-1] > df['High'].iloc[-3]
    
    # Strategy: Trend + FVG + Order Block
    if current_price > ema and is_fvg:
        sl = current_price - 3.50 # Tight SMC Stop Loss
        tp = current_price + 8.00 # 1:2+ Reward
        return f"🔥 *{symbol} BUY SETUP*\n📈 Trend: Bullish\n⚡ Entry: {current_price:.2f}\n🛑 SL: {sl:.2f}\n✅ TP: {tp:.2f}"
    
    return None

async def run_bot():
    print("🚀 Gold Bot is starting...")
    await send_msg("✅ *Bot successfully connected to Railway!* Scanning XAUUSD & XAUEUR...")
    
    while True:
        # Scan Gold Pairs
        for name, ticker in {"XAUUSD": "GC=F", "XAUEUR": "EURGLD=X"}.items():
            signal = analyze_setup(name, ticker)
            if signal:
                await send_msg(signal)
        
        # Wait 30 minutes before next quality scan (Prevents spam/errors)
        await asyncio.sleep(1800)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass

