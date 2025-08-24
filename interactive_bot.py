# interactive_bot.py: For manually chatting with the bot

import os
import discord
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

# --- LOAD ALL SECRET KEYS ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# --- CONFIGURE THE APIs ---
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
intents = discord.Intents.all()
client = discord.Client(intents=intents)


# --- BOT EVENTS ---
@client.event
async def on_ready():
    print(f'Bot has logged in as {client.user}. It is now listening for commands.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # A simple test command
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')

    # The news-fetching command (posts to Discord)
    if message.content.startswith('!news'):
        parts = message.content.split()
        topic = ' '.join(parts[1:]) if len(parts) > 1 else 'technology'
        
        await message.channel.send(f"Okay, I'm gathering today's top 10 headlines about '{topic}'...")
        try:
            url = f"https://newsapi.org/v2/everything?q={topic}&language=en&pageSize=10&apiKey={NEWS_API_KEY}"
            response = requests.get(url)
            data = response.json()
            articles = data.get('articles', [])

            if not articles:
                await message.channel.send(f"Sorry, I couldn't find any news about '{topic}' right now.")
                return

            formatted_articles = ""
            for i, article in enumerate(articles):
                formatted_articles += f"{i+1}. Title: {article['title']}\n"

            prompt = f"""
            You are an expert tech news editor for a Discord channel. Given a list of 10 raw article titles about '{topic}', turn this into a professional "Top News" report.
            Create a main title: "⚡️ Today's Top Headlines about {topic.capitalize()} ⚡️"
            For each article, create a short, exciting headline with a relevant emoji and a one-sentence summary.
            Format the output using Discord markdown.
            Here are the raw articles:
            {formatted_articles}
            """
            gemini_response = model.generate_content(prompt)
            await message.channel.send(gemini_response.text)
        except Exception as e:
            await message.channel.send(f"Sorry, an error occurred. Error: {e}")

    # The email command
    if message.content.startswith('!emailnews'):
        parts = message.content.split()
        topic = ' '.join(parts[1:]) if len(parts) > 1 else 'technology'

        await message.channel.send(f"Okay, preparing a professional HTML report about '{topic}' and sending it...")
        try:
            url = f"https://newsapi.org/v2/everything?q={topic}&language=en&pageSize=10&apiKey={NEWS_API_KEY}"
            response = requests.get(url)
            data = response.json()
            articles = data.get('articles', [])

            if not articles:
                await message.channel.send(f"Sorry, I couldn't find any news about '{topic}' to email.")
                return

            formatted_articles = ""
            for i, article in enumerate(articles):
                formatted_articles += f"{i+1}. Title: {article['title']}\n   URL: {article['url']}\n\n"
            
            prompt = f"""
            You are an expert email newsletter designer. Given a list of 10 raw articles about '{topic}', turn this into a visually appealing HTML email.
            The entire output must be a single block of HTML code. Use inline CSS for styling.
            Create a main title: "<h1>⚡️ Today's Top Tech Headlines: {topic.capitalize()} ⚡️</h1>"
            For each article, create a headline in an <h2> tag with an emoji and make it a clickable link. Add a summary in a <p> tag. Add an <hr> between items.
            Here are the raw articles:
            {formatted_articles}
            """
            gemini_response = model.generate_content(prompt)
            html_body = gemini_response.text.replace("```html", "").replace("```", "").strip()

            msg = EmailMessage()
            msg['Subject'] = f"⚡️ Today's Top Tech Headlines: {topic.capitalize()} ⚡️"
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECIPIENT_EMAIL
            msg.add_alternative(html_body, subtype='html')

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                smtp.send_message(msg)
            
            await message.channel.send(f"Success! I've sent the professional report to {RECIPIENT_EMAIL}.")
        except Exception as e:
            await message.channel.send(f"Sorry, I couldn't send the email. Error: {e}")

# --- RUN THE BOT ---
client.run(DISCORD_TOKEN)