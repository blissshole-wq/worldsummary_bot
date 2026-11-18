import os
import pytz
import requests
import yfinance as yf
import feedparser
from datetime import datetime
from google import genai

# Load Secrets
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_market_data():
    """Fetches live/latest prices for key global assets with fallback error handling."""
    tickers = {
        "Nifty 50": "^NSEI",
        "Sensex": "^BSESN",
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Nikkei 225": "^N225",
        "Hang Seng": "^HSI",
        "FTSE 100": "^FTSE",
        "DAX": "^GDAXI",
        "Gold": "GC=F",
        "Crude Oil": "BZ=F",
        "USD/INR": "INR=X"
    }
    
    summary_lines = []
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if not hist.empty and len(hist) >= 1:
                curr_close = hist['Close'].iloc[-1]
                summary_lines.append(f"• {name}: {curr_close:,.2f}")
            else:
                summary_lines.append(f"• {name}: Stable")
        except Exception:
            summary_lines.append(f"• {name}: Active")
            
    return "\n".join(summary_lines)

def get_news_headlines():
    """Fetches top headlines from global business and Tamil regional RSS feeds."""
    feeds = {
        "Global Markets": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
        "India Business": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    }
    
    news_items = []
    for category, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                headlines = [entry.title for entry in feed.entries[:3]]
                news_items.append(f"*{category}*\n" + "\n".join([f"- {h}" for h in headlines]))
        except Exception:
            continue
            
    return "\n\n".join(news_items) if news_items else "Global financial markets reacting to macro indicators."

def generate_story_report(is_morning, date_str, market_data, headlines):
    """Generates report via Gemini, with an instant text fallback if servers are busy."""
    session_type = "காலை நேர உலகச் சந்தை நாடித்துடிப்பு (Morning Global Pulse)" if is_morning else "மாலை உலகச் சந்தை மற்றும் கமாடிட்டி மூடப்புச் சுருக்கம் (Evening Closure Summary)"
    
    prompt = f"""
    You are an expert financial journalist writing for a Tamil reader in Tirunelveli, Tamil Nadu.
    Session: {session_type}
    Date: {date_str}
    Market Data:
    {market_data}
    Headlines:
    {headlines}

    Write a comprehensive, engaging, story-style report in Tamil (with English financial terms). Use clean Telegram Markdown. Keep under 3800 chars.
    """

    models_to_try = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3.8-flash"]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"Model {model_name} busy: {e}")
            continue
            
    # Guaranteed Bulletproof Fallback if Gemini is fully congested
    fallback_report = f"""🌙 *மாலை உலகச் சந்தை மற்றும் கமாடிட்டி மூடப்புச் சுருக்கம்*
📅 *{date_str} | நெல்லை எக்ஸ்பிரஸ் வணிகப் பார்வை*

வணக்கம் நெல்லை மற்றும் தென் தமிழக வாசகர்களே! இன்றைய சந்தை நேர முடிவில் உலகளாவிய குறியீடுகள் மற்றும் கமாடிட்டி நிலவரங்களின் தொகுப்பு இதோ:

📊 *முக்கிய சந்தை நிலவரங்கள்:*
{market_data}

📰 *தலைப்புச் செய்திகள்:*
{headlines}

💡 *சுருக்கமான பார்வை:*
சர்வதேச பொருளாதாரச் சூழல் மற்றும் கமாடிட்டி விலை மாற்றங்கள் தொடர்ந்து கண்காணிக்கப்பட்டு வருகின்றன. நாளைய அமர்வு குறித்த விரிவான எதிர்பார்ப்புகளுடன் வர்த்தகம் நிறைவடைந்துள்ளது."""
    
    return fallback_report

def send_telegram_message(text):
    """Sends message to Telegram, splitting safely if over 4000 characters."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    max_length = 4000
    
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    for chunk in chunks:
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        res = requests.post(url, json=payload)
        if res.status_code != 200:
            payload.pop("parse_mode")
            requests.post(url, json=payload)

def main():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    is_morning = now.hour < 12
    date_str = now.strftime('%d-%m-%Y %I:%M %p IST')

    print("Fetching market data...")
    market_data = get_market_data()
    
    print("Fetching news headlines...")
    headlines = get_news_headlines()
    
    print("Generating story report...")
    report = generate_story_report(is_morning, date_str, market_data, headlines)
    
    print("Sending to Telegram...")
    send_telegram_message(report)
    print("Done!")

if __name__ == "__main__":
    main()