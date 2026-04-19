import discord
from discord.ext import commands
import logging
import aiohttp
import os

log = logging.getLogger('cog.steam_stats')

class SteamStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('STEAM_API_KEY')

    @discord.app_commands.command(name='stats', description="Fetches Lifetime Rust Stats for a Steam User")
    async def get_steam_stats(self, interaction: discord.Interaction, steam_id: str):
        if not self.api_key:
            await interaction.response.send_message("Steam API Key is not configured.", ephemeral=True)
            return
            
        if len(steam_id) != 17 or not steam_id.isdigit():
            await interaction.response.send_message("Please provide a valid 64-bit Steam ID.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=252490&key={self.api_key}&steamid={steam_id}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        stats = data.get('playerstats', {}).get('stats', [])
                        
                        kills = 0
                        deaths = 0
                        headshots = 0
                        bullets_fired = 0
                        
                        for stat in stats:
                            name = stat.get('name')
                            value = stat.get('value')
                            if name == 'kill_player':
                                kills = value
                            elif name == 'deaths':
                                deaths = value
                            elif name == 'headshot':
                                headshots = value
                            elif name == 'bullet_fired':
                                bullets_fired = value
                                
                        kd = round(kills / max(1, deaths), 2)
                        acc = round((headshots / max(1, bullets_fired)) * 100, 2)
                        
                        embed = discord.Embed(
                            title=f"Global Rust Stats: {steam_id}",
                            color=discord.Color.dark_red()
                        )
                        embed.add_field(name="Lifetime Kills", value=f"{kills:,}", inline=True)
                        embed.add_field(name="Lifetime Deaths", value=f"{deaths:,}", inline=True)
                        embed.add_field(name="K/D Ratio", value=f"**{kd}**", inline=True)
                        embed.add_field(name="Headshots", value=f"{headshots:,}", inline=True)
                        embed.add_field(name="Est. Accuracy", value=f"{acc}%", inline=True)
                        
                        await interaction.followup.send(embed=embed)
                    elif resp.status == 403:
                        await interaction.followup.send("\u274c Profile is Private. Cannot retrieve stats.")
                    else:
                        await interaction.followup.send("\u274c Failed to retrieve stats or player hasn't played Rust.")
        except Exception as e:
            log.error(f"Steam API error: {e}")
            await interaction.followup.send(f"\u274c Error checking Steam API: {e}")

async def setup(bot):
    await bot.add_cog(SteamStats(bot))
