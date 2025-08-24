# agent.py: Final Automation Version using GNews API

import os
import requests
import google.generativeai as genai
import smtplib
from email.message import EmailMessage
from datetime import date
from dotenv import load_dotenv
import discord

# --- LOAD ALL SECRET KEYS from environment variables ---
# These will be set by our automation tool (GitHub Actions)
load_dotenv()
NEWS_API_KEY = os.getenv('NEWS_API_KEY') # This should be your GNews key
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
# This event runs once the bot is online and ready.
@client.event
async def on_ready():
    print(f'Bot has logged in as {client.user}')
    
    # Find the specific channel to send the message to
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("Error: Could not find the specified channel.")
        await client.close()
        return

    print("Fetching and generating the news report from GNews...")
    try:
        # 1. FETCH NEWS from GNews
        topic = "technology"
        # Using the more reliable 'search' endpoint
        url = f"https://gnews.io/api/v4/search?q={topic}&lang=en&country=us&max=10&apikey={NEWS_API_KEY}"
        
        response = requests.get(url)
        data = response.json()
        articles = data.get('articles', [])

        if not articles:
            await channel.send("Sorry, I couldn't find any news today using GNews.")
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

        # 3. SEND THE HTML EMAIL
        today = date.today().strftime("%B %d, %Y")
        msg = EmailMessage()
        msg['Subject'] = f"Your Daily Tech Briefing for {today}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg.add_alternative(html_body, subtype='html')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        
        print(f"Successfully sent GNews report to {RECIPIENT_EMAIL}.")

    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # 4. LOG OUT AND SHUT DOWN
        print("Task complete. Logging out.")
        await client.close()

# --- RUN THE BOT ---
# This line starts the bot. For automation, it will run the on_ready event and then shut down.
client.run(DISCORD_TOKEN)