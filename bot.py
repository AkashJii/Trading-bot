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
    return "Akash Pro Human-Logic Bot Active Hai!"

def analyze_market_and_setup():
    try:
        url = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=250"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not isinstance(data, list):
            return None, None, 50, "API Error", None, None, None, None

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        current_price = df['close'].iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        # RSI Calculation (14 period)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        if current_price > ema_200:
            trend = "BULLISH (UPTREND)"
            direction = "LONG"
            entry = round(ema_200 + 20, 2) if current_price > (ema_200 * 1.02) else round(current_price, 2)
            sl = round(df['low'].iloc[-5:].min() - 50, 2)
            risk = entry - sl
            tp = round(entry + (risk * 2), 2)
        else:
            trend = "BEARISH (DOWNTREND)"
            direction = "SHORT"
            entry = round(ema_200 - 20, 2) if current_price < (ema_200 * 0.98) else round(current_price, 2)
            sl = round(df['high'].iloc[-5:].max() + 50, 2)
            risk = sl - entry
            tp = round(entry - (risk * 2), 2)
            
        return current_price, ema_200, current_rsi, trend, entry, sl, tp, direction
    except Exception as e:
        return None, None, 50.0, str(e), None, None, None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎯 **Akash Pro Human-Logic Bot** active hai!\n\nCommands:\n/setup - Pro Pullback Setup\n/paper - Virtual Trade Start\n/result - Check Trade Status & P&L")

@bot.message_handler(commands=['setup'])
def send_setup(message):
    bot.reply_to(message, "🔍 Market structure, RSI aur Pullback levels analyze ho rahe hain...")
    
    price, ema, rsi, trend, entry, sl, tp, direction = analyze_market_and_setup()
    
    if price and isinstance(ema, float):
        warning = ""
        if rsi > 70:
            warning = "\n⚠️ **WARNING:** RSI Overbought (>70) hai! Chase mat karna, pullback ka wait karo."
        elif rsi < 30:
            warning = "\n⚠️ **WARNING:** RSI Oversold (<30) hai! Jaldbaazi mat karo."
            
        risk_pts = abs(entry - sl)
        reward_pts = abs(tp - entry)
        
        reply_text = f"""📊 **PRO HUMAN TRADER SETUP** 📊
        
📈 **Trend:** {trend}
💰 **Live BTC Price:** ${price:,.2f}
⚓ **Lohe ka Farsh (200 EMA):** ${ema:,.2f}
📉 **RSI (14):** {rsi:.2f}
{warning}

🎯 **Smart Direction:** {direction}
📍 **Planned Entry (Pullback Level):** ${entry:,.2f}
🛑 **Structure Stop Loss:** ${sl:,.2f} ({risk_pts:.2f} pts risk)
💰 **Take Profit Target (1:2):** ${tp:,.2f} ({reward_pts:.2f} pts reward)

🛡️ *Logic:* No blind chasing. Built with structure & RSI filter! 🚀"""
        
        bot.reply_to(message, reply_text)
    else:
        bot.reply_to(message, "Error fetching data. Try again!")

@bot.message_handler(commands=['paper'])
def start_paper_trade(message):
    price, ema, rsi, trend, entry, sl, tp, direction = analyze_market_and_setup()
    if price and isinstance(ema, float):
        trade_id = message.chat.id
        active_paper_trades[trade_id] = {"direction": direction, "entry": entry, "sl": sl, "tp": tp, "status": "RUNNING"}
        bot.reply_to(message, f"📝 **Smart Paper Trade Logged!** {direction} at ${entry:,.2f} (SL: ${sl:,.2f}, TP: ${tp:,.2f}). Use `/result` to track.")
    else:
        bot.reply_to(message, "Error starting paper trade.")

@bot.message_handler(commands=['result'])
def check_paper_result(message):
    trade_id = message.chat.id
    if trade_id not in active_paper_trades:
        bot.reply_to(message, "Pehle `/paper` se trade shuru karo!")
        return
    trade = active_paper_trades[trade_id]
    try:
        res = requests.get("https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=5", timeout=5).json()
        current_price = float(res[-1][4])
        entry, sl, tp, direction = trade["entry"], trade["sl"], trade["tp"], trade["direction"]
        
        res_msg = f"📊 **TRADE STATUS**\nLive: ${current_price:,.2f} | Entry: ${entry:,.2f}\n\n"
        if direction == "LONG":
            if current_price >= tp:
                res_msg += "✅ **TARGET HIT! (PROFIT 🎉)**"
            elif current_price <= sl:
                res_msg += "❌ **STOP LOSS HIT!**"
            else:
                res_msg += f"⏳ **RUNNING** (P&L: ${current_price - entry:+.2f})"
        else:
            if current_price <= tp:
                res_msg += "✅ **TARGET HIT! (PROFIT 🎉)**"
            elif current_price >= sl:
                res_msg += "❌ **STOP LOSS HIT!**"
            else:
                res_msg += f"⏳ **RUNNING** (P&L: ${entry - current_price:+.2f})"
        bot.reply_to(message, res_msg)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
