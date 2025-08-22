# bot.py: Automation Version

import os
import discord
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# --- LOAD ALL SECRET KEYS ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID')) # Get the channel ID

# --- CONFIGURE THE APIs ---
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
intents = discord.Intents.default() # We don't need privileged intents for this
client = discord.Client(intents=intents)

# --- BOT EVENTS ---
@client.event
async def on_ready():
    """This event runs once the bot is online and ready."""
    print(f'Bot has logged in as {client.user}')
    
    # Find the specific channel to send the message to
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("Error: Could not find the specified channel.")
        await client.close()
        return

    print("Fetching and generating the news report...")
    try:
        # 1. FETCH NEWS
        url = f"https://newsapi.org/v2/top-headlines?country=us&category=technology&pageSize=10&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        articles = data.get('articles', [])

        if not articles:
            await channel.send("Sorry, I couldn't find any news today.")
            await client.close()
            return

        # 2. CREATE A PROFESSIONAL REPORT WITH GEMINI AI
        formatted_articles = ""
        for i, article in enumerate(articles):
            formatted_articles += f"{i+1}. Title: {article['title']}\n"

        prompt = f"""
        You are an expert tech news editor for a Discord channel. I will give you a list of 10 raw article titles.
        Your job is to turn this into a professional and engaging "Top Tech News" report.
        Create a main title: "⚡️ Today's Top Tech Headlines ⚡️"
        For each article, create a short, exciting headline with a relevant emoji and a one-sentence summary.
        Format it clearly using Discord markdown.
        Here are the raw articles:
        {formatted_articles}
        """
        gemini_response = model.generate_content(prompt)
        news_report = gemini_response.text

        # 3. POST THE FINAL REPORT
        await channel.send(news_report)
        print("Successfully posted the news report to Discord.")

    except Exception as e:
        print(f"An error occurred: {e}")
        await channel.send(f"Sorry, an error occurred while creating the news report: {e}")
    
    finally:
        # 4. LOG OUT AND SHUT DOWN
        print("Task complete. Logging out.")
        await client.close()

# --- RUN THE BOT ---
client.run(DISCORD_TOKEN)