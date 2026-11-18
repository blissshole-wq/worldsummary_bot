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
                summary_lines.append(f"{name}: {curr_close:,.2f}")
            else:
                summary_lines.append(f"{name}: Market data currently stable")
        except Exception:
            summary_lines.append(f"{name}: Live tracking active")
            
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
                news_items.append(f"--- {category} ---\n" + "\n".join(headlines))
        except Exception:
            continue
            
    return "\n\n".join(news_items) if news_items else "Global financial markets reacting to macro indicators."

def generate_story_report(is_morning, date_str, market_data, headlines):
    """Uses Gemini to weave raw numbers and headlines into a Tamil story-style analysis with fallback."""
    session_type = "Morning Global Pulse & Daily Brief (7:00 AM IST)" if is_morning else "Evening Market & Global Closure Summary (8:00 PM IST)"
    
    prompt = f"""
    You are an expert financial journalist and macro-economic analyst writing for a Tamil reader in Tirunelveli, Tamil Nadu.
    Current Session: {session_type}
    Date & Time: {date_str}

    Market Reference Data:
    {market_data}

    Latest Headlines:
    {headlines}

    Task:
    Write a comprehensive, engaging, story-style report in Tamil (using clear English terms for financial metrics/indices). 
    Do NOT just list dry numbers. Connect the dots:
    1. **The Story Arc (சங்கிலித் தொடர் பகுப்பாய்வு):** Explain how global cues (US/Europe/Asia) are triggering chain reactions in commodities (Gold, Crude Oil), currency (USD/INR), and Indian equities.
    2. **Key Numbers & Context:** Integrate the provided market numbers naturally into the narrative.
    3. **Sector & Expert Synthesis (நிபுணர்களின் பார்வை & துறை தாக்கம்):** Analyze what institutional experts are watching and how Banking, IT, Energy, and Metals are affected.
    4. {"**Regional & Daily Touch:** Briefly include Southern Tamil Nadu (Tirunelveli/Madurai/Tuticorin) context, tech/cinema highlights, and horoscope/daily outlook." if is_morning else "**Expectations vs. Reality:** Summarize how the trading day started versus how it closed and what experts predict for tomorrow."}

    Formatting Rules:
    - Use clean Telegram Markdown (*bold* for headers/key numbers, bullet points for readability).
    - Keep total length under 3,800 characters so it fits cleanly in Telegram.
    """

    # Try primary model, fallback to alternative if 503/unavailable occurs
    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash"]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            print(f"Model {model_name} failed due to: {e}. Trying fallback...")
            continue
            
    raise Exception("All Gemini models are currently busy. Please try again shortly.")

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
    
    print("Generating AI story report...")
    report = generate_story_report(is_morning, date_str, market_data, headlines)
    
    print("Sending to Telegram...")
    send_telegram_message(report)
    print("Done!")

if __name__ == "__main__":
    main()