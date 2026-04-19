import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv

import database
from rust_client import init_rust_socket

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('bot')

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX', '!')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    log.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    await database.init_db()
    
    # Initialize Rust+ Connection
    await init_rust_socket(bot)
    
    # Start Webhook Server for Live Kills
    try:
        import server
        await server.start_webhook_server(bot, port=8080)
    except ImportError:
        pass
        
    # Load cogs
    cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
    if not os.path.exists(cogs_dir):
        os.makedirs(cogs_dir)
        
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                log.info(f'Loaded cog: {filename}')
            except Exception as e:
                log.error(f'Failed to load cog {filename}: {e}')
                
    try:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        log.error(f"Failed to sync slash commands: {e}")

if __name__ == '__main__':
    if not TOKEN or TOKEN == 'your_discord_bot_token_here':
        log.error("Please configure your DISCORD_TOKEN in the .env file.")
    else:
        bot.run(TOKEN)
