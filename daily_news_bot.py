import os
import requests
from google import genai
from google.genai.types import HttpOptions
from email.message import EmailMessage
import smtplib
from datetime import date
import discord
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

NEWS_API_KEY = os.getenv('NEWS_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize Google GenAI client for Vertex AI Gemini with v1 API
client = genai.Client(http_options=HttpOptions(api_version="v1"))

intents = discord.Intents.default()
intents.message_content = True
client_discord = discord.Client(intents=intents)

def fetch_news(params):
    url = 'http://api.mediastack.com/v1/news'
    response = requests.get(url, params=params)
    data = response.json()
    return data.get('data', [])

def format_articles_list(articles):
    formatted = ""
    for i, article in enumerate(articles):
        title = article.get('title', 'No Title')
        url = article.get('url', '')
        formatted += f"{i+1}. Title: {title}\n   URL: {url}\n\n"
    return formatted

def generate_content(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

async def send_long_message(channel, content):
    max_length = 2000
    while content:
        await channel.send(content[:max_length])
        content = content[max_length:]

@client_discord.event
async def on_ready():
    print(f'Logged in as {client_discord.user}')
    channel = client_discord.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print(f"Discord channel with ID {DISCORD_CHANNEL_ID} not found or inaccessible.")
        await client_discord.close()
        return
    print(f"Found channel: {channel.name}")

    try:
        base_params = {
            'access_key': NEWS_API_KEY,
            'languages': 'en',
            'limit': 10,
            'sort': 'published_desc'
        }
        tech_news = fetch_news({**base_params, 'categories': 'technology'})
        ai_news = fetch_news({**base_params, 'keywords': 'AI,artificial intelligence'})
        python_news = fetch_news({**base_params, 'keywords': 'Python'})

        tech_formatted = format_articles_list(tech_news)
        ai_formatted = format_articles_list(ai_news)
        python_formatted = format_articles_list(python_news)

        email_prompt = f"""
Create a professional HTML newsletter with sections Technology News, AI News, Python News.

Technology News:
{tech_formatted}

AI News:
{ai_formatted}

Python News:
{python_formatted}
"""
        html_body = generate_content(email_prompt)

        discord_prompt = f"""
Create a Discord message titled "Today's Top Tech, AI, Python Headlines" with bold headlines and one-sentence summaries:

Technology:
{tech_formatted}

AI:
{ai_formatted}

Python:
{python_formatted}
"""
        discord_body = generate_content(discord_prompt)

        await send_long_message(channel, discord_body)
        print("Sent news to Discord")

        today = date.today().strftime("%B %d, %Y")
        msg = EmailMessage()
        msg['Subject'] = f"Daily Tech & AI & Python News - {today}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg.add_alternative(html_body, subtype='html')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        print("Newsletter email sent")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        await client_discord.close()

client_discord.run(DISCORD_TOKEN)




