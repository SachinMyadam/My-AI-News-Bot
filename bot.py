# agent.py: Final Version using Mediastack API

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
NEWS_API_KEY = os.getenv('NEWS_API_KEY') # This will now be your Mediastack key
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

# --- BOT'S SINGLE TASK ---
@client.event
async def on_ready():
    print(f'Bot has logged in as {client.user}')
    
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("Error: Could not find the specified channel.")
        await client.close()
        return

    print("Fetching and generating the news report from Mediastack...")
    try:
        # 1. FETCH NEWS from Mediastack
        params = {
            'access_key': NEWS_API_KEY,
            'categories': 'technology',
            'languages': 'en',
            'limit': 10,
            'sort': 'published_desc'
        }
        response = requests.get('http://api.mediastack.com/v1/news', params=params)
        data = response.json()
        articles = data.get('data', [])

        if not articles:
            await channel.send("Sorry, I couldn't find any news today using Mediastack.")
            await client.close()
            return

        # 2. CREATE A PROFESSIONAL HTML EMAIL WITH GEMINI AI
        formatted_articles = ""
        for i, article in enumerate(articles):
            formatted_articles += f"{i+1}. Title: {article['title']}\n   URL: {article['url']}\n\n"

        prompt = f"""
        You are an expert email newsletter designer. Turn the following list of articles into a professional HTML newsletter.
        Create a main title: "<h1>📬 Your Daily Tech Briefing 📬</h1>"
        For each article, create a bold, clickable headline in an <h2> tag and a one-sentence summary in a <p> tag.
        Separate items with an <hr>. The design should be clean and modern.
        Here are the articles:
        {formatted_articles}
        """
        gemini_response = model.generate_content(prompt)
        html_body = gemini_response.text.replace("```html", "").replace("```", "").strip()
        
        # Create a simple text version for Discord
        discord_prompt = f"""
        You are a tech news editor. Turn the following list of articles into a professional Discord message.
        Create a main title: "⚡️ Today's Top Tech Headlines ⚡️"
        For each article, create a bold headline with an emoji and a one-sentence summary.
        Here are the articles:
        {formatted_articles}
        """
        discord_gemini_response = model.generate_content(discord_prompt)
        discord_body = discord_gemini_response.text

        # 3. POST TO DISCORD
        await channel.send(discord_body)
        print("Successfully posted news to Discord.")

        # 4. SEND THE HTML EMAIL
        today = date.today().strftime("%B %d, %Y")
        msg = EmailMessage()
        msg['Subject'] = f"Your Daily Tech Briefing for {today}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg.add_alternative(html_body, subtype='html')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        
        print(f"Successfully sent Mediastack report to {RECIPIENT_EMAIL}.")

    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        print("Task complete. Logging out.")
        await client.close()

# --- RUN THE BOT ---
client.run(DISCORD_TOKEN)