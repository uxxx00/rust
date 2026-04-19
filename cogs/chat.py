import discord
from discord.ext import commands
import logging
import os

import rust_client
import database

log = logging.getLogger('cog.chat')

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Prevent bot from replying to itself
        if message.author == self.bot.user:
            return

        # Check if the message is in the configured team chat channel
        chat_channel_id = await database.get_setting('channel_chat')
        # Fallback to env var if not set in DB
        if not chat_channel_id:
            chat_channel_id = os.getenv('TEAM_CHAT_CHANNEL_ID')

        if chat_channel_id and str(message.channel.id) == str(chat_channel_id):
            # Send to Rust+
            content = f"[{message.author.display_name}] {message.content}"
            success = await rust_client.send_team_message(content)
            if success:
                await message.add_reaction('\u2705') # checkmark
            else:
                await message.add_reaction('\u274c') # X mark

async def setup(bot):
    await bot.add_cog(Chat(bot))
