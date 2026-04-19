import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import logging
import aiosqlite
import os

log = logging.getLogger('cog.mobile')

class MobileAlerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        from database import DB_PATH
        self.db_path = DB_PATH

    async def send_push_notification(self, expo_token, title, body):
        """Sends a push notification using Expo's Push API."""
        url = "https://exp.host/--/api/v2/push/send"
        payload = {
            "to": expo_token,
            "title": title,
            "body": body,
            "sound": "default",
            "priority": "high"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    return True
                else:
                    log.error(f"Failed to send push notification: {await resp.text()}")
                    return False

    @app_commands.command(name='register_device', description="Links your Mobile App to the bot.")
    async def register_device(self, interaction: discord.Interaction, expo_token: str):
        """Saves your mobile device token to the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO user_settings (user_id, setting_key, setting_value) VALUES (?, ?, ?)",
                (interaction.user.id, 'expo_token', expo_token)
            )
            await db.commit()
        
        await interaction.response.send_message("\ud83d\udcf1 **Device Linked!** Your phone is now connected to the tactical alert system.", ephemeral=True)

    @app_commands.command(name='test_mobile', description="Sends a test siren to your mobile app.")
    async def test_mobile(self, interaction: discord.Interaction):
        """Sends a test push notification to the registered device."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT setting_value FROM user_settings WHERE user_id = ? AND setting_key = 'expo_token'", (interaction.user.id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    await interaction.response.send_message("No device registered. Use `/register_device` first.", ephemeral=True)
                    return
                
                token = row[0]
                success = await self.send_push_notification(token, "\ud83d\udea8 RAID ALERT TEST", "If you hear the siren, your app is working perfectly!")
                
                if success:
                    await interaction.response.send_message("Test signal sent to your phone!")
                else:
                    await interaction.response.send_message("Failed to send signal. Check your token.")

async def setup(bot):
    await bot.add_cog(MobileAlerts(bot))
