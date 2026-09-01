import telebot
from flask import Flask
import threading
import os
import requests

# Tumhara token
TOKEN = '8665827387:AAEDbbZSPvJ_z6wGJHCN7CvuBYoGsi3Fv9A'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Render ko zinda rakhne ke liye
@app.route('/')
def index():
    return "Akash set and forget bot 24/7 Zinda Hai!"

# Live BTC price nikalne ka function
def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        return None

# Start Message
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Ram Ram ji'Akash set and forget bot' zinda ho gaya hai! 🎯 /setup dabao aur naya order dekho.")

# Asli Magic: Set and Forget Logic
@bot.message_handler(commands=['setup'])
def send_setup(message):
    bot.reply_to(message, "Market check kar raha hoon, 2 second do... ⏳")
    
    current_price = get_btc_price()
    
    if current_price:
        # Sniper Logic: Price se $100 niche ka jaal, 500 SL, 1000 TP
        entry_price = round(current_price - 100)
        sl_price = entry_price - 500
        tp_price = entry_price + 1000
        
        reply_text = f"""🔥 **AKASH SET & FORGET SETUP** 🔥
        
📈 **Live BTC Price:** ${current_price:,.2f}

🎯 **Entry (Limit Buy):** ${entry_price:,.2f}
🛑 **Stop Loss (SL):** ${sl_price:,.2f}
💰 **Take Profit (TP):** ${tp_price:,.2f}

⚖️ **Risk/Reward:** 1:2
Delta app mein feed karo aur aaram se so jao! 💸"""
        
        bot.reply_to(message, reply_text)
    else:
        bot.reply_to(message, "Bhai, server se live price nahi mil raha. Thodi der mein try karna!")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
