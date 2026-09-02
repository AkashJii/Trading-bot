import telebot
from flask import Flask
import threading
import os
import requests
import pandas as pd

TOKEN = '8665827387:AAEDbbZSPvJ_z6wGJHCN7CvuBYoGsi3Fv9A'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

active_paper_trades = {}

@app.route('/')
def index():
    return "Akash Fixed Paper Trading Bot Active Hai!"

def analyze_market_and_setup():
    try:
        url = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=250"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not isinstance(data, list):
            return None, None, "API Error", None, None, None, None

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df['close'] = df['close'].astype(float)
        
        current_price = df['close'].iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        if current_price > ema_200:
            trend = "BULLISH (UPTREND)"
            entry = round(current_price - 100, 2)
            sl = round(entry - 400, 2)  # Long ke liye SL neeche
            tp = round(entry + 800, 2)  # Long ke liye TP upar
            direction = "LONG"
        else:
            trend = "BEARISH (DOWNTREND)"
            entry = round(current_price + 100, 2)
            sl = round(entry + 400, 2)  # Short ke liye SL upar (+)
            tp = round(entry - 800, 2)  # Short ke liye TP neeche (-)
            direction = "SHORT"
            
        return current_price, ema_200, trend, entry, sl, tp, direction
    except Exception as e:
        return None, None, str(e), None, None, None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎯 **Akash Fixed Bot** active hai!\n\nCommands:\n/setup - Pro Setup dekho\n/paper - Virtual Trade start karo\n/result - P&L check karo")

@bot.message_handler(commands=['setup'])
def send_setup(message):
    bot.reply_to(message, "🔍 Market scan ho raha hai...")
    
    price, ema, trend, entry, sl, tp, direction = analyze_market_and_setup()
    
    if price and isinstance(ema, float):
        reply_text = f"""📊 **PRO QUANT SETUP (FIXED)** 📊
        
📈 **Trend:** {trend}
💰 **Live BTC Price:** ${price:,.2f}
⚓ **Lohe ka Farsh (200 EMA):** ${ema:,.2f}

🎯 **Direction:** {direction}
📍 **Entry Price:** ${entry:,.2f}
🛑 **Stop Loss:** ${sl:,.2f}
💰 **Take Profit Target:** ${tp:,.2f}

⚖️ **Risk/Reward:** 1:2 (Corrected & Verified) 🚀"""
        
        bot.reply_to(message, reply_text)
    else:
        bot.reply_to(message, "Bhai, market data fetch karne mein glitch aaya. Dobara /setup dabao!")

@bot.message_handler(commands=['paper'])
def start_paper_trade(message):
    price, ema, trend, entry, sl, tp, direction = analyze_market_and_setup()
    
    if price:
        trade_id = message.chat.id
        active_paper_trades[trade_id] = {
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "status": "RUNNING"
        }
        
        bot.reply_to(message, f"""📝 **PAPER TRADE RECORDED!** 
        
Virtual {direction} order logged at **${entry:,.2f}**.
SL: ${sl:,.2f} | TP: ${tp:,.2f}
Bot ab iska result track karega. `/result` dabakar status check kar sakte ho!""")
    else:
        bot.reply_to(message, "Paper trade shuru karne mein error aaya. Dobara try karo.")

@bot.message_handler(commands=['result'])
def check_paper_result(message):
    trade_id = message.chat.id
    if trade_id not in active_paper_trades:
        bot.reply_to(message, "Bhai, pehle `/paper` command se koi virtual trade shuru toh karo!")
        return
        
    trade = active_paper_trades[trade_id]
    
    url = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=5"
    try:
        res = requests.get(url, timeout=5).json()
        current_price = float(res[-1][4])
        
        entry = trade["entry"]
        sl = trade["sl"]
        tp = trade["tp"]
        direction = trade["direction"]
        
        result_msg = f"📊 **PAPER TRADE STATUS**\nLive Price: ${current_price:,.2f}\nEntry: ${entry:,.2f}\n\n"
        
        if direction == "LONG":
            if current_price >= tp:
                result_msg += "✅ **STATUS: TARGET HIT! (PROFIT 🎉)**"
            elif current_price <= sl:
                result_msg += "❌ **STATUS: STOP LOSS HIT!**"
            else:
                diff = current_price - entry
                result_msg += f"⏳ **STATUS: RUNNING** (P&L: ${diff:+.2f})"
        else: # SHORT
            if current_price <= tp:
                result_msg += "✅ **STATUS: TARGET HIT! (PROFIT 🎉)**"
            elif current_price >= sl:
                result_msg += "❌ **STATUS: STOP LOSS HIT!**"
            else:
                diff = entry - current_price
                result_msg += f"⏳ **STATUS: RUNNING** (P&L: ${diff:+.2f})"
                
        bot.reply_to(message, result_msg)
    except Exception as e:
        bot.reply_to(message, f"Result check karne mein error: {e}")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # Current price fetch karo check karne ke liye
    url = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=5"
    try:
        res = requests.get(url, timeout=5).json()
        current_price = float(res[-1][4])
        
        entry = trade["entry"]
        sl = trade["sl"]
        tp = trade["tp"]
        direction = trade["direction"]
        
        result_msg = f"📊 **PAPER TRADE STATUS**\nLive Price: ${current_price:,.2f}\nEntry: ${entry:,.2f}\n\n"
        
        if direction == "LONG":
            if current_price >= tp:
                result_msg += "✅ **STATUS: TARGET HIT! (PROFIT 🎉)**"
            elif current_price <= sl:
                result_msg += "❌ **STATUS: STOP LOSS HIT! (LESSON LEARNED 📚)**"
            else:
                diff = current_price - entry
                result_msg += f"⏳ **STATUS: RUNNING** (P&L: ${diff:+.2f})"
        else: # SHORT
            if current_price <= tp:
                result_msg += "✅ **STATUS: TARGET HIT! (PROFIT 🎉)**"
            elif current_price >= sl:
                result_msg += "❌ **STATUS: STOP LOSS HIT! (LESSON LEARNED 📚)**"
            else:
                diff = entry - current_price
                result_msg += f"⏳ **STATUS: RUNNING** (P&L: ${diff:+.2f})"
                
        bot.reply_to(message, result_msg)
    except Exception as e:
        bot.reply_to(message, f"Result check karne mein error: {e}")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
