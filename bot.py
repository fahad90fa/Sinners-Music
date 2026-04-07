import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import asyncio
from dotenv import load_dotenv

def load_environment():
    load_dotenv()
    if os.getenv('DISCORD_TOKEN'):
        return

    # Recover from a common typo where the env file was saved with a trailing space.
    fallback_env = '.env '
    if os.path.exists(fallback_env):
        load_dotenv(fallback_env)

load_environment()

# Bot Configuration
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
bot.launch_time = discord.utils.utcnow()

DEFAULT_CONFIG = {
    "prefix": "!",
    "sales_channel": None,
    "ticket_category": None,
    "admin_roles": [],
    "support_roles": [],
    "log_channel": None,
    "payment_methods": ["PayPal", "Bitcoin", "Ethereum", "Bank Transfer"],
    "embed_color": "0x00ff9d",
    "footer_text": "ZeroDay Tools",
    "thumbnail_url": "https://i.imgur.com/your_logo.png"
}

# Load config
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open('config.json', 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG

config = load_config()

@bot.event
async def on_ready():
    print(f"""
    ╔═══════════════════════════════════════════╗
    ║                                           ║
    ║   🤖 SALES BOT ACTIVATED                  ║
    ║   Bot: {bot.user.name}                    
    ║   ID: {bot.user.id}                       
    ║   Servers: {len(bot.guilds)}              
    ║                                           ║
    ╚═══════════════════════════════════════════╝
    """)
    
    # Load all cogs
    await load_cogs()
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="!help | ZeroDay Tools"
        ),
        status=discord.Status.online
    )


async def load_cogs():
    cogs = ['cogs.setup', 'cogs.products', 'cogs.tickets', 'cogs.admin', 'cogs.rules', 'cogs.welcome']
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

# Run bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN is not set. Add it to a .env file as "
            "DISCORD_TOKEN=your_bot_token"
        )
    bot.run(token)
