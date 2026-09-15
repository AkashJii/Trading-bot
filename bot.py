import telebot
from flask import Flask
import threading
import os
import requests
import pandas as pd
import numpy as np

TOKEN = '8665827387:AAEDbbZSPvJ_z6wGJHCN7CvuBYoGsi3Fv9A'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

active_paper_trades = {}

@app.route('/')
def index():
    return "Akash Pro Quant Algo Bot Active Hai!"

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()

def analyze_market_and_setup():
    try:
        # 1-Hour Data for Macro Trend & 200 EMA (Lohe ka Farsh)
        url_1h = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=250"
        resp_1h = requests.get(url_1h, timeout=10).json()
        df_1h = pd.DataFrame(resp_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df_1h['close'] = df_1h['close'].astype(float)
        df_1h['high'] = df_1h['high'].astype(float)
        df_1h['low'] = df_1h['low'].astype(float)
        
        current_price = df_1h['close'].iloc[-1]
        ema_200 = df_1h['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        # 15-Minute Data for Micro Trend & ATR Buffer
        url_15m = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=100"
        resp_15m = requests.get(url_15m, timeout=10).json()
        df_15m = pd.DataFrame(resp_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df_15m['close'] = df_15m['close'].astype(float)
        df_15m['high'] = df_15m['high'].astype(float)
        df_15m['low'] = df_15m['low'].astype(float)
        
        atr = calculate_atr(df_15m).iloc[-1]
        
        # RSI Calculation (14 period on 1h)
        delta = df_1h['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        # Multi-Timeframe Alignment Logic
        if current_price > ema_200:
            trend = "BULLISH (UPTREND)"
            direction = "LONG"
            entry = round(current_price, 2)
            # ATR Based Dynamic Stop Loss to prevent noise hunting
            sl = round(df_15m['low'].iloc[-5:].min() - (atr * 0.5), 2)
            risk = entry - sl
            tp = round(entry + (risk * 2), 2)
        else:
            trend = "BEARISH (DOWNTREND)"
            direction = "SHORT"
            entry = round(current_price, 2)
            sl = round(df_15m['high'].iloc[-5:].max() + (atr * 0.5), 2)
            risk = sl - entry
            tp = round(entry - (risk * 2), 2)
            
        return current_price, ema_200, current_rsi, trend, entry, sl, tp, direction, atr
    except Exception as e:
        return None, None, 50.0, str(e), None, None, None, None, 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎯 **Akash Pro Quant Algo Bot** active hai!\n\nCommands:\n/setup - Multi-Timeframe Pro Setup\n/paper - Virtual Trade Start\n/result - Check Trade Status & P&L")

@bot.message_handler(commands=['setup'])
def send_setup(message):
    bot.reply_to(message, "🔍 1h & 15m Multi-Timeframe, ATR aur RSI data analyze ho raha hai...")
    
    price, ema, rsi, trend, entry, sl, tp, direction, atr = analyze_market_and_setup()
    
    if price and isinstance(ema, float):
        warning = ""
        if rsi > 70:
            warning = "\n⚠️ **WARNING:** RSI Overbought (>70) hai! Pullback ka dhyan rakhein."
        elif rsi < 30:
            warning = "\n⚠️ **WARNING:** RSI Oversold (<30) hai! Jaldbaazi mat karein."
            
        risk_pts = abs(entry - sl)
        reward_pts = abs(tp - entry)
        
        reply_text = f"""📊 **PRO QUANT ALGO SETUP (MULTI-TF)** 📊
        
📈 **Trend (1h):** {trend}
💰 **Live BTC Price:** ${price:,.2f}
⚓ **Lohe ka Farsh (200 EMA):** ${ema:,.2f}
📉 **RSI (14):** {rsi:.2f}
🛡️ **ATR Buffer (Volatility):** {atr:.2f}
{warning}

🎯 **Smart Direction:** {direction}
📍 **Planned Entry:** ${entry:,.2f}
🛑 **ATR Dynamic Stop Loss:** ${sl:,.2f} ({risk_pts:.2f} pts risk)
💰 **Take Profit Target (1:2):** ${tp:,.2f} ({reward_pts:.2f} pts reward)

🚀 *Algo Status:* Optimized with Multi-Timeframe & ATR filters!"""
        
        bot.reply_to(message, reply_text)
    else:
        bot.reply_to(message, "Error fetching data. Try again!")

@bot.message_handler(commands=['paper'])
def start_paper_trade(message):
    price, ema, rsi, trend, entry, sl, tp, direction, atr = analyze_market_and_setup()
    if price and isinstance(ema, float):
        trade_id = message.chat.id
        active_paper_trades[trade_id] = {"direction": direction, "entry": entry, "sl": sl, "tp": tp, "status": "RUNNING"}
        bot.reply_to(message, f"📝 **Algo Paper Trade Logged!** {direction} at ${entry:,.2f} (SL: ${sl:,.2f}, TP: ${tp:,.2f}). Use `/result` to track.")
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
        
        res_msg = f"📊 **ALGO TRADE STATUS**\nLive: ${current_price:,.2f} | Entry: ${entry:,.2f}\n\n"
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
