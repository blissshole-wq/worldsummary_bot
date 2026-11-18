import os
import pytz
from datetime import datetime
import requests

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    print("Status:", response.status_code, response.text)

def run_bot():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_hour = now.hour

    # மதியம் 12 மணிக்கு முன் ரன் ஆனால் காலைச் செய்தி (7:00 AM)
    if current_hour < 12:
        msg = f"☀️ **காலை உலகச் சந்தை மற்றும் உள்ளூர் செய்தித் தொகுப்பு**\nநேரம்: {now.strftime('%d-%m-%Y %I:%M %p')}\n\n(உங்கள் காலைச் செய்தி விவரங்கள்...)"
    # மதியம் 12 மணிக்கு மேல் ரன் ஆனால் இரவுச் செய்தி (8:00 PM)
    else:
        msg = f"🌙 **இரவு உலகச் சந்தை மற்றும் கமாடிட்டி மூடப்புச் சுருக்கம்**\nநேரம்: {now.strftime('%d-%m-%Y %I:%M %p')}\n\n(உங்கள் இரவுச் சந்தை பகுப்பாய்வு...)"

    send_telegram_message(msg)

if __name__ == "__main__":
    run_bot()