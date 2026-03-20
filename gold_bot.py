def analyze_setup(symbol, ticker):
    try:
        # 1. Fetch data for the 5-minute timeframe
        df = yf.download(ticker, period="2d", interval="5m", progress=False)
        if df.empty or len(df) < 50:
            print(f"DEBUG [{symbol}]: No data found.")
            return None

        # 2. Extract specific values to avoid 'Series' errors
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        third_row = df.iloc[-3]
        
        price = float(last_row['Close'])
        
        # EMA 50 for a more active "Intraday" trend (instead of the slow 200)
        df['EMA_50'] = ta.ema(df['Close'], length=50)
        ema = float(df['EMA_50'].iloc[-1])

        # 3. SMC Logic: Look for a Fair Value Gap (Institutional Footprint)
        # Bullish Gap: Current Low is higher than the High from 2 candles ago
        is_bullish_fvg = float(last_row['Low']) > float(third_row['High'])
        # Bearish Gap: Current High is lower than the Low from 2 candles ago
        is_bearish_fvg = float(last_row['High']) < float(third_row['Low'])

        now_gmt = datetime.now(GHANA_TZ).strftime('%H:%M')

        # --- SIGNAL TRIGGER ---
        if price > ema and is_bullish_fvg:
            return (f"🚀 *{symbol} BUY SIGNAL*\n"
                    f"💎 *Type:* SMC Institutional Entry\n"
                    f"📈 *Trend:* Bullish (Above EMA50)\n"
                    f"💰 *Entry:* {price:.2f}\n"
                    f"🛑 *SL:* {price - 5:.2f} | ✅ *TP:* {price + 10:.2f}\n"
                    f"⏰ {now_gmt} GMT")

        elif price < ema and is_bearish_fvg:
            return (f"📉 *{symbol} SELL SIGNAL*\n"
                    f"💎 *Type:* SMC Institutional Entry\n"
                    f"📈 *Trend:* Bearish (Below EMA50)\n"
                    f"💰 *Entry:* {price:.2f}\n"
                    f"🛑 *SL:* {price + 5:.2f} | ✅ *TP:* {price - 10:.2f}\n"
                    f"⏰ {now_gmt} GMT")
        
        # If no signal, we log it so you can see the bot is 'thinking'
        print(f"DEBUG [{symbol}]: Price at {price:.2f}, EMA at {ema:.2f}. No FVG detected yet.")

    except Exception as e:
        print(f"CRITICAL ERROR [{symbol}]: {e}")
    return None

