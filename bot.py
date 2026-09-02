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
    return "Akash Structural Pro Bot Active Hai!"

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
        
        # Structural Logic based on 200 EMA (Lohe ka Farsh)
        if current_price > ema_200:
            trend = "BULLISH (UPTREND)"
            direction = "LONG"
            entry = round(current_price, 2)
            # Long mein SL 200 EMA ke thoda niche safe zone mein hoga
            sl = round(ema_200 - 50, 2)
            risk = entry - sl
            tp = round(entry + (risk * 2), 2)  # Strict 1:2 R:R
        else:
            trend = "BEARISH (DOWNTREND)"
            direction = "SHORT"
            entry = round(current_price, 2)
            # Short mein SL 200 EMA ke thoda upar resistance ke upar hoga
            sl = round(ema_200 + 50, 2)
            risk = sl - entry
            tp = round(entry - (risk * 2), 2)  # Strict 1:2 R:R
            
        return current_price, ema_200, trend, entry, sl, tp, direction
    except Exception as e:
        return None, None, str(e), None, None, None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎯 **Akash Structural Bot** active hai!\n\nCommands:\n/setup - Structural Pro Setup\n/paper - Virtual Trade")

@bot.message_handler(commands=['setup'])
def send_setup(message):
    bot.reply_to(message, "🔍 Market structure aur 200 EMA scan ho raha hai...")
    
    price, ema, trend, entry, sl, tp, direction = analyze_market_and_setup()
    
    if price and isinstance(ema, float):
        risk_pts = abs(entry - sl)
        reward_pts = abs(tp - entry)
        
        reply_text = f"""📊 **STRUCTURAL PRO SETUP** 📊
        
📈 **Trend:** {trend}
💰 **Live BTC Price:** ${price:,.2f}
⚓ **Lohe ka Farsh (200 EMA):** ${ema:,.2f}

🎯 **Direction:** {direction}
📍 **Entry Price:** ${entry:,.2f}
🛑 **Stop Loss (EMA Structure):** ${sl:,.2f} ({risk_pts:.2f} pts risk)
💰 **Take Profit (1:2 Target):** ${tp:,.2f} ({reward_pts:.2f} pts reward)

⚖️ **Logic:** SL strictly 200 EMA ke structure ke hisab se set hai! 🚀"""
        
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
        
        bot.reply_to(message, f"""📝 **STRUCTURAL PAPER TRADE LOGGED!** 
        
Virtual {direction} at **${entry:,.2f}**.
SL: ${sl:,.2f} | TP: ${tp:,.2f}
Check status using `/result`. Let's see how the market respects the structure!""")
    else:
        bot.reply_to(message, "Error starting paper trade.")

@bot.message_handler(commands=['result'])
def check_paper_result(message):
    trade_id = message.chat.id
    if trade_id not in active_paper_trades:
        bot.reply_to(message, "Bhai, pehle `/paper` se trade shuru karo!")
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
        
        result_msg = f"📊 **TRADE STATUS**\nLive Price: ${current_price:,.2f}\nEntry: ${entry:,.2f}\n\n"
        
        if direction == "LONG":
            if current_price >= tp:
                result_msg += "✅ **STATUS: TARGET HIT! (PROFIT 🎉)**"
            elif current_price <= sl:
                result_msg += "❌ **STATUS: STOP LOSS HIT!**"
            else:
                diff = current_price - entry
                result_msg += f"⏳ **STATUS: RUNNING** (P&L: ${diff:+.2f})"
        else:
            if current_price <= tp:
                result_msg += "✅ **STATUS: TARGET HIT! (PROFIT 🎉)**"
            elif current_price >= sl:
                result_msg += "❌ **STATUS: STOP LOSS HIT!**"
            else:
                diff = entry - current_price
                result_msg += f"⏳ **STATUS: RUNNING** (P&L: ${diff:+.2f})"
                
        bot.reply_to(message, result_msg)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
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
