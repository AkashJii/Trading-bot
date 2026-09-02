import telebot
from flask import Flask
import threading
import os
import requests
import pandas as pd

TOKEN = '8665827387:AAEDbbZSPvJ_z6wGJHCN7CvuBYoGsi3Fv9A'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "Akash Trend-Following Sniper Bot 24/7 Active Hai!"

def analyze_trend_and_setup():
    try:
        url = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=250"
        response = requests.get(url)
        data = response.json()
        
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df['close'] = df['close'].astype(float)
        
        current_price = df['close'].iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        # Trend Detection: Price EMA ke upar hai ya neeche?
        if current_price > ema_200:
            trend = "BULLISH"
            # LONG SETUP: Dip par buy karenge
            entry_price = round(current_price - 100)
            sl_price = entry_price - 500
            tp_price = entry_price + 1000
        else:
            trend = "BEARISH"
            # SHORT SETUP: Thoda bounce aane par sell karenge
            entry_price = round(current_price + 100)
            sl_price = entry_price + 500
            tp_price = entry_price - 1000
            
        return current_price, ema_200, trend, entry_price, sl_price, tp_price
    except Exception as e:
        return None, None, str(e), None, None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bhai, 'Akash Trend-Following Bot' active ho gaya hai! 🎯 /setup dabao.")

@bot.message_handler(commands=['setup'])
def send_setup(message):
    bot.reply_to(message, "Market trend scan ho raha hai, Long ya Short decide kar raha hoon... ⏳")
    
    current_price, ema_200, trend, entry, sl, tp = analyze_trend_and_setup()
    
    if current_price and isinstance(ema_200, float):
        if trend == "BULLISH":
            signal_title = "🟢 **LONG (BUY) SETUP -- UPTREND**"
            strategy_msg = "Market 200 EMA ke upar hai, trend bullish hai. Dip buy setup ready hai!"
        else:
            signal_title = "🔴 **SHORT (SELL) SETUP -- DOWNTREND**"
            strategy_msg = "Market 200 EMA ke neeche hai, trend bearish hai. Bounce sell setup ready hai!"

        reply_text = f"""{signal_title}
        
📊 **Trend Status:** {trend}
📈 **Live BTC Price:** ${current_price:,.2f}
⚓ **200 EMA Level:** ${ema_200:,.2f}

{strategy_msg}
🎯 **Entry Price:** ${entry:,.2f}
🛑 **Stop Loss (SL):** ${sl:,.2f}
💰 **Take Profit (TP):** ${tp:,.2f}

⚖️ **Risk/Reward:** 1:2
Trend is your friend! Delta mein feed karo. 🚀"""
        
        bot.reply_to(message, reply_text)
    else:
        bot.reply_to(message, f"Bhai, error aa gaya: {trend}")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
