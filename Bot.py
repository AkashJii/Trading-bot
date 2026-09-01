import telebot
from flask import Flask
import threading
import os

# Tumhara token
TOKEN = '8665827387:AAEDbbZSPvJ_z6wGJHCN7CvuBYoGsi3Fv9A'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Render ke liye dummy web page
@app.route('/')
def index():
    return "Ram ram bhai Bot 24/7 Zinda Hai!"

# Telegram ka command
@bot.message_handler(commands=['start', 'setup'])
def send_setup(message):
    bot.reply_to(message, "Bhai, Akash Sniper Bot zinda ho gaya hai! 🎯 Target lock karne ke liye ready hoon.")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # Bot aur Server dono ek sath chalane ke liye
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
