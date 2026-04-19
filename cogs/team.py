import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import aiohttp
import os

import rust_client

log = logging.getLogger('cog.team')

class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.steam_api_key = os.getenv('STEAM_API_KEY')
        self.bm_token = os.getenv('BATTLEMETRICS_TOKEN')
        self.bm_server_id = os.getenv('BATTLEMETRICS_SERVER_ID')

    async def fetch_steam_stats(self, session, steam_id):
        if not self.steam_api_key:
            return {"kills": 0, "deaths": 0}
        url = f"http://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=252490&key={self.steam_api_key}&steamid={steam_id}"
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    stats = data.get('playerstats', {}).get('stats', [])
                    kills = 0
                    deaths = 0
                    for stat in stats:
                        name = stat.get('name')
                        if name == 'kill_player':
                            kills = stat.get('value')
                        elif name == 'deaths':
                            deaths = stat.get('value')
                    return {"kills": kills, "deaths": deaths}
        except Exception as e:
            log.error(f"Steam stats fetch failed for {steam_id}: {e}")
        return {"kills": 0, "deaths": 0}

    async def fetch_bm_playtime(self, session, steam_id):
        if not self.bm_token or not self.bm_server_id:
            return 0
        
        headers = {"Authorization": f"Bearer {self.bm_token}"}
        # 1. Get player BM ID
        search_url = f"https://api.battlemetrics.com/players?filter[search]={steam_id}&filter[game]=rust"
        try:
            async with session.get(search_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('data'):
                        bm_id = data['data'][0]['id']
                        
                        # 2. Get server stats
                        server_url = f"https://api.battlemetrics.com/players/{bm_id}/servers/{self.bm_server_id}"
                        async with session.get(server_url, headers=headers) as resp2:
                            if resp2.status == 200:
                                data2 = await resp2.json()
                                if 'data' in data2 and 'attributes' in data2['data']:
                                    time_played = data2['data']['attributes'].get('timePlayed', 0)
                                    return time_played # in seconds
        except Exception as e:
            log.error(f"BM Playtime fetch failed for {steam_id}: {e}")
        return 0

    async def get_member_data(self, session, member):
        steam_id = member.steam_id
        name = member.name
        
        # Parallel fetch
        steam_task = self.fetch_steam_stats(session, steam_id)
        bm_task = self.fetch_bm_playtime(session, steam_id)
        
        steam_stats, playtime_seconds = await asyncio.gather(steam_task, bm_task)
        
        return {
            "name": name,
            "steam_id": steam_id,
            "kills": steam_stats.get('kills', 0),
            "deaths": steam_stats.get('deaths', 0),
            "playtime_seconds": playtime_seconds
        }

    @app_commands.command(name='topmate', description="Shows team members sorted by server playtime, with global kills/deaths.")
    async def topmate(self, interaction: discord.Interaction):
        if not rust_client.socket:
            await interaction.response.send_message("Rust+ is not connected. Try again in a moment.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            team_info = await rust_client.socket.get_team_info()
        except Exception as e:
            await interaction.followup.send(f"Failed to get team info from Rust+: {e}")
            return

        if not team_info or not hasattr(team_info, 'members') or not team_info.members:
            await interaction.followup.send("You don't appear to be in a team or team info is unavailable.")
            return

        members_data = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for member in team_info.members:
                tasks.append(self.get_member_data(session, member))
                
            results = await asyncio.gather(*tasks)
            for res in results:
                if res:
                    members_data.append(res)
                    
        # Sort by playtime (descending)
        members_data.sort(key=lambda x: x['playtime_seconds'], reverse=True)
        
        embed = discord.Embed(
            title="\ud83c\udfc6 Top Teammates Rankings",
            description="Your team members ranked by playtime on this server.",
            color=discord.Color.gold()
        )
        
        for idx, md in enumerate(members_data):
            hours = round(md['playtime_seconds'] / 3600, 1)
            kills = md['kills']
            deaths = md['deaths']
            kd = round(kills / max(1, deaths), 2)
            
            medal = "\ud83e\udd47" if idx == 0 else "\ud83e\udd48" if idx == 1 else "\ud83e\udd49" if idx == 2 else "\u25ab\ufe0f"
            
            stats_str = f"**Hours (Server):** {hours}h\n**Kills (Global):** {kills:,}\n**Deaths (Global):** {deaths:,}\n**K/D:** {kd}"
            embed.add_field(name=f"{medal} {md['name']}", value=stats_str, inline=False)
            
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Team(bot))
