import os
import requests
import google.generativeai as genai
import smtplib
from email.message import EmailMessage
from datetime import date
from dotenv import load_dotenv
import discord

# --- LOAD ALL SECRET KEYS ---
load_dotenv()
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# --- CONFIGURE THE APIs ---
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Helper function to send long messages to Discord in chunks
async def send_long_message(channel, content):
    max_length = 2000
    while len(content) > 0:
        to_send = content[:max_length]
        await channel.send(to_send)
        content = content[max_length:]

# Helper to fetch news data from Mediastack for given params
def fetch_news(params):
    url = 'http://api.mediastack.com/v1/news'
    response = requests.get(url, params=params)
    data = response.json()
    return data.get('data', [])

# Format articles list for prompt input
def format_articles_list(articles):
    formatted = ""
    for i, article in enumerate(articles):
        title = article.get('title', 'No Title')
        url = article.get('url', '')
        formatted += f"{i+1}. Title: {title}\n   URL: {url}\n\n"
    return formatted

@client.event
async def on_ready():
    print(f'Bot logged in as {client.user}')
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("Error: Could not find Discord channel.")
        await client.close()
        return

    try:
        print("Fetching news for Technology, AI, and Python...")

        # Prepare parameters for three queries
        base_params = {
            'access_key': NEWS_API_KEY,
            'languages': 'en',
            'limit': 10,
            'sort': 'published_desc'
        }

        # 1. Technology category
        tech_params = base_params.copy()
        tech_params['categories'] = 'technology'
        tech_news = fetch_news(tech_params)

        # 2. AI keyword
        ai_params = base_params.copy()
        ai_params['keywords'] = 'AI,artificial intelligence'
        ai_news = fetch_news(ai_params)

        # 3. Python keyword
        python_params = base_params.copy()
        python_params['keywords'] = 'Python'
        python_news = fetch_news(python_params)

        # Format all for AI prompt
        tech_formatted = format_articles_list(tech_news)
        ai_formatted = format_articles_list(ai_news)
        python_formatted = format_articles_list(python_news)

        combined_prompt = f"""
You are an expert email newsletter designer. Create a professional HTML newsletter with three sections: Technology News, AI News, and Python News.

Main title: "<h1>📬 Your Daily Tech & AI & Python News Briefing 📬</h1>"

Section titles as <h2>, each followed by bold clickable headlines and one-sentence summaries in <p> tags, separated by <hr>.

Technology News:
{tech_formatted}

AI News:
{ai_formatted}

Python News:
{python_formatted}
"""

        gemini_response = model.generate_content(combined_prompt)
        html_body = gemini_response.text.replace("``````", "").strip()

        # For Discord summary message (short text)
        discord_prompt = f"""
You are a tech news editor. Create a Discord message titled "⚡️ Today's Top Tech, AI, Python Headlines ⚡️", with bold headlines + one-sentence summaries for the following news:

Technology:
{tech_formatted}

AI:
{ai_formatted}

Python:
{python_formatted}
"""
        discord_response = model.generate_content(discord_prompt)
        discord_body = discord_response.text.strip()

        # Send Discord message in chunks if too long
        await send_long_message(channel, discord_body)
        print("Posted news to Discord.")

        # Send email
        today = date.today().strftime("%B %d, %Y")
        msg = EmailMessage()
        msg['Subject'] = f"Your Daily Tech & AI & Python News for {today}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg.add_alternative(html_body, subtype='html')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"Sent email to {RECIPIENT_EMAIL}.")

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        print("Task done, logging out.")
        await client.close()

# Run bot
client.run(DISCORD_TOKEN)

