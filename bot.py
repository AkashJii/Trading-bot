import telebot
from telebot import types
from flask import Flask
import threading
import os
import requests
import pandas as pd
import numpy as np
import hmac
import hashlib
import time
import json

TOKEN = '8665827387:AAEDbbZSPvJ_z6wGJHCN7CvuBYoGsi3Fv9A'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Direct Hardcoded Live Credentials (No Environment Variable Confusion)
DELTA_API_KEY = "TZw2k35xFfkFCJJcxTfWCSAllqSy7"
DELTA_API_SECRET = "EFmEL09TTZJQJk9VaVV5woeN4knWpxexLEljmkQIKcpfmkGochXursGd1viH"
DELTA_BASE_URL = "https://api.delta.exchange"

active_trades = {}

@app.route('/')
def index():
    return "Akash Live Quant Bot Active Hai!"

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_setup = types.KeyboardButton('📊 Get Setup')
    btn_paper = types.KeyboardButton('📝 Paper Trade')
    btn_auto = types.KeyboardButton('⚡ Auto Trade')
    btn_result = types.KeyboardButton('📈 Check Result')
    markup.add(btn_setup, btn_paper, btn_auto, btn_result)
    return markup

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()

def analyze_market_and_setup():
    try:
        url_1h = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=250"
        resp_1h = requests.get(url_1h, timeout=10).json()
        df_1h = pd.DataFrame(resp_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df_1h['close'] = df_1h['close'].astype(float)
        df_1h['high'] = df_1h['high'].astype(float)
        df_1h['low'] = df_1h['low'].astype(float)
        
        current_price = df_1h['close'].iloc[-1]
        ema_200 = df_1h['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        url_15m = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=100"
        resp_15m = requests.get(url_15m, timeout=10).json()
        df_15m = pd.DataFrame(resp_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df_15m['close'] = df_15m['close'].astype(float)
        df_15m['high'] = df_15m['high'].astype(float)
        df_15m['low'] = df_15m['low'].astype(float)
        
        atr = calculate_atr(df_15m).iloc[-1]
        
        delta_rsi = df_1h['close'].diff()
        gain = (delta_rsi.where(delta_rsi > 0, 0)).rolling(window=14).mean()
        loss = (-delta_rsi.where(delta_rsi < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        if current_price > ema_200:
            trend = "BULLISH (UPTREND)"
            direction = "LONG"
            entry = round(current_price, 2)
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

def place_delta_live_order(direction, entry, sl, tp):
    try:
        path = "/v2/orders"
        url = DELTA_BASE_URL + path
        timestamp = str(int(time.time()))
        
        payload = {
            "product_id": 27, # BTCUSD perpetual standard ID on Delta Live
            "size": 1,        
            "side": "buy" if direction == "LONG" else "sell",
            "order_type": "market",
            "stop_loss_price": str(sl),
            "take_profit_price": str(tp)
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        
        message_signature = timestamp + "POST" + path + payload_str
        signature = hmac.new(
            DELTA_API_SECRET.encode('utf-8'),
            message_signature.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'api-key': DELTA_API_KEY,
            'timestamp': timestamp,
            'signature': signature,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(url, data=payload_str, headers=headers, timeout=10)
        return response.status_code in [200, 201], response.json()
    except Exception as e:
        return False, str(e)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = get_main_keyboard()
    bot.reply_to(message, "⚡ **Akash Live Quant Bot** active hai!\n\nNeeche diye gaye buttons se control karein:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['📊 Get Setup', '/setup'])
def send_setup(message):
    bot.reply_to(message, "🔍 Scanning Live Market Setup...")
    price, ema, rsi, trend, entry, sl, tp, direction, atr = analyze_market_and_setup()
    
    if price and isinstance(ema, float):
        warning = "\n⚠️ **RSI Warning:** Overbought/Oversold zone!" if rsi > 70 or rsi < 30 else ""
        risk_pts = abs(entry - sl)
        reward_pts = abs(tp - entry)
        
        reply_text = f"""📊 **LIVE QUANT SETUP** 📊
        
📈 **Trend (1h):** {trend}
💰 **Live BTC Price:** ${price:,.2f}
⚓ **200 EMA:** ${ema:,.2f}
📉 **RSI (14):** {rsi:.2f}
🛡️ **ATR Buffer:** {atr:.2f}
{warning}

🎯 **Direction:** {direction}
📍 **Entry:** ${entry:,.2f}
🛑 **Stop Loss:** ${sl:,.2f} ({risk_pts:.2f} pts)
💰 **Take Profit:** ${tp:,.2f} ({reward_pts:.2f} pts)

🚀 *Status:* Ready for Live Execution!"""
        bot.reply_to(message, reply_text, reply_markup=get_main_keyboard())
    else:
        bot.reply_to(message, "Error fetching market data!", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text in ['📝 Paper Trade', '/paper'])
def start_paper_trade(message):
    price, ema, rsi, trend, entry, sl, tp, direction, atr = analyze_market_and_setup()
    if price and isinstance(ema, float):
        trade_id = message.chat.id
        active_trades[trade_id] = {"direction": direction, "entry": entry, "sl": sl, "tp": tp, "status": "RUNNING"}
        bot.reply_to(message, f"📝 **Paper Trade Logged!** {direction} at ${entry:,.2f}.", reply_markup=get_main_keyboard())
    else:
        bot.reply_to(message, "Error starting paper trade.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text in ['⚡ Auto Trade', '/autotrade'])
def execute_delta_autotrade(message):
    price, ema, rsi, trend, entry, sl, tp, direction, atr = analyze_market_and_setup()
    if not price:
        bot.reply_to(message, "Market data fetch error for auto-trade.", reply_markup=get_main_keyboard())
        return
        
    success, res_data = place_delta_live_order(direction, entry, sl, tp)
    
    if success:
        trade_id = message.chat.id
        active_trades[trade_id] = {"direction": direction, "entry": entry, "sl": sl, "tp": tp, "status": "RUNNING"}
        bot.reply_to(message, f"⚡ **Delta Live Order Executed!**\n\nSide: {direction}\nEntry: ${entry:,.2f}\nSL: ${sl:,.2f}\nTP: ${tp:,.2f}\n\nResponse: {res_data}", reply_markup=get_main_keyboard())
    else:
        bot.reply_to(message, f"❌ **Order Execution Failed:** {res_data}", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text in ['📈 Check Result', '/result'])
def check_paper_result(message):
    trade_id = message.chat.id
    if trade_id not in active_trades:
        bot.reply_to(message, "Pehle setup ya trade shuru karo!", reply_markup=get_main_keyboard())
        return
    trade = active_trades[trade_id]
    try:
        res = requests.get("https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=5", timeout=5).json()
        current_price = float(res[-1][4])
        entry, sl, tp, direction = trade["entry"], trade["sl"], trade["tp"], trade["direction"]
        
        res_msg = f"📊 **LIVE TRADE STATUS**\nLive: ${current_price:,.2f} | Entry: ${entry:,.2f}\n\n"
        if direction == "LONG":
            if current_price >= tp: res_msg += "✅ **TARGET HIT! (PROFIT 🎉)**"
            elif current_price <= sl: res_msg += "❌ **STOP LOSS HIT!**"
            else: res_msg += f"⏳ **RUNNING** (P&L: ${current_price - entry:+.2f})"
        else:
            if current_price <= sl: res_msg += "❌ **STOP LOSS HIT!**"
            elif current_price <= tp: res_msg += "✅ **TARGET HIT! (PROFIT 🎉)**"
            else: res_msg += f"⏳ **RUNNING** (P&L: ${entry - current_price:+.2f})"
        bot.reply_to(message, res_msg, reply_markup=get_main_keyboard())
    except Exception as e:
        bot.reply_to(message, f"Error: {e}", reply_markup=get_main_keyboard())

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
