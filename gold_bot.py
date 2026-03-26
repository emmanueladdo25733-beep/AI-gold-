from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

@app.route('/webhook', methods=['POST'])
def webhook():
    # This is what TradingView sends to Railway
    data = request.json
    if data:
        # Format the message for your Telegram
        msg = f"🔥 TRADINGVIEW SIGNAL\n\n{data.get('message', 'New Trade Alert!')}"
        send_telegram(msg)
        return 'Success', 200
    return 'No data', 400

if __name__ == "__main__":
    # Railway provides the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
