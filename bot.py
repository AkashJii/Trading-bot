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
    return "Akash Public Trend Sniper Bot 24/7 Active Hai!"

def analyze_trend_and_setup():
    try:
        url = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=250"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not isinstance(data, list):
            return None, None, "API Error", None, None, None

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df['close'] = df['close'].astype(float)
        
        current_price = df['close'].iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        if current_price > ema_200:
            trend = "BULLISH"
            entry_price = round(current_price - 100, 2)
            sl_price = round(entry_price - 500, 2)
            tp_price = round(entry_price + 1000, 2)
        else:
            trend = "BEARISH"
            entry_price = round(current_price + 100, 2)
            sl_price = round(entry_price + 500, 2)
            tp_price = round(entry_price - 1000, 2)
            
        return current_price, ema_200, trend, entry_price, sl_price, tp_price
    except Exception as e:
        return None, None, str(e), None, None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name or "Trader"
    bot.reply_to(message, f"Ram Ram {user_name} ji! 🎯 Main 'Akash Trend Sniper Bot' hoon. /setup dabakar live crypto setup nikal sakte ho.")

@bot.message_handler(commands=['setup'])
def send_setup(message):
    bot.reply_to(message, "Market scan ho raha hai, thoda wait karo... ⏳")
    
    current_price, ema_200, trend, entry, sl, tp = analyze_trend_and_setup()
    
    if current_price and isinstance(ema_200, float):
        if trend == "BULLISH":
            signal_title = "🟢 **LONG (BUY) SETUP -- UPTREND**"
            strategy_msg = "Market 200 EMA ke upar hai, trend bullish hai."
        else:
            signal_title = "🔴 **SHORT (SELL) SETUP -- DOWNTREND**"
            strategy_msg = "Market 200 EMA ke neeche hai, trend bearish hai."

        reply_text = f"""{signal_title}
        
📊 **Trend Status:** {trend}
📈 **Live BTC Price:** ${current_price:,.2f}
⚓ **200 EMA Level:** ${ema_200:,.2f}

{strategy_msg}
🎯 **Entry Price:** ${entry:,.2f}
🛑 **Stop Loss (SL):** ${sl:,.2f}
💰 **Take Profit (TP):** ${tp:,.2f}

⚖️ **Risk/Reward:** 1:2
Powered by Akash System 🚀"""
        
        bot.reply_to(message, reply_text)
    else:
        bot.reply_to(message, "Bhai, market data fetch karne mein chota sa glitch aaya. Dobara /setup bhejo!")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
