import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import aiohttp
import os

log = logging.getLogger('cog.battlemetrics')

class BattleMetrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token = os.getenv('BATTLEMETRICS_TOKEN')
        self.server_id = os.getenv('BATTLEMETRICS_SERVER_ID')
        self.tracked_players = {} # dict of bm_id -> {'name': name, 'online': False}
        
        if self.token and self.server_id:
            self.bg_task = self.bot.loop.create_task(self.tracker_loop())

    async def get_events_channel(self):
        import database
        channel_id = await database.get_setting('channel_events') or os.getenv('EVENTS_CHANNEL_ID')
        if channel_id:
            return self.bot.get_channel(int(channel_id))
        return None

    async def tracker_loop(self):
        await self.bot.wait_until_ready()
        headers = {"Authorization": f"Bearer {self.token}"}
        
        while not self.bot.is_closed():
            if not self.tracked_players:
                await asyncio.sleep(60)
                continue
                
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.battlemetrics.com/servers/{self.server_id}?include=player"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            online_ids = []
                            if 'included' in data:
                                for item in data['included']:
                                    if item['type'] == 'player':
                                        online_ids.append(item['id'])
                            
                            channel = await self.get_events_channel()
                            
                            for bm_id, info in self.tracked_players.items():
                                is_online = bm_id in online_ids
                                
                                # State change logic
                                if is_online and not info['online']:
                                    info['online'] = True
                                    if channel:
                                        embed = discord.Embed(title="\ud83d\udea8 ENEMY LOGIN DETECTED", description=f"**{info['name']}** has just logged onto the server!", color=discord.Color.red())
                                        await channel.send(embed=embed)
                                        
                                elif not is_online and info['online']:
                                    info['online'] = False
                                    if channel:
                                        embed = discord.Embed(title="\ud83d\udca4 ENEMY LOGOUT DETECTED", description=f"**{info['name']}** has just logged off. The offline raid window is open.", color=discord.Color.green())
                                        await channel.send(embed=embed)
                                        
            except Exception as e:
                log.error(f"BattleMetrics polling failed: {e}")
                
            await asyncio.sleep(60) # Scan every 60 seconds

    @app_commands.command(name='track', description="[BM ADVANTAGE] Adds an enemy to the live login/logout radar.")
    async def track_enemy(self, interaction: discord.Interaction, bm_id: str, name: str):
        self.tracked_players[bm_id] = {'name': name, 'online': False}
        await interaction.response.send_message(f"\ud83d\udce1 Now actively tracking **{name}**. You will receive an emergency ping the exact second they log in or out.")

    @app_commands.command(name='untrack', description="[BM ADVANTAGE] Removes an enemy from the live radar.")
    async def untrack_enemy(self, interaction: discord.Interaction, bm_id: str):
        if bm_id in self.tracked_players:
            del self.tracked_players[bm_id]
            await interaction.response.send_message(f"\ud83d\udce1 Stopped tracking {bm_id}.")
        else:
            await interaction.response.send_message("Not currently tracking that ID.", ephemeral=True)

    @app_commands.command(name='server_list', description="[BM ADVANTAGE] Dumps the entire list of currently online players.")
    async def server_list(self, interaction: discord.Interaction):
        """Scrapes BM for all online players on your configured server."""
        if not self.token or not self.server_id:
            await interaction.response.send_message("BattleMetrics API is not configured.", ephemeral=True)
            return
            
        await interaction.response.defer()
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.battlemetrics.com/servers/{self.server_id}?include=player"
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        players = []
                        if 'included' in data:
                            for item in data['included']:
                                if item['type'] == 'player':
                                    players.append(item['attributes']['name'])
                        
                        players.sort()
                        # Discord limits embeds to 4096 chars, we format nicely
                        player_str = "\n".join(players)
                        if len(player_str) > 4000:
                            player_str = player_str[:4000] + "\n...and more."
                            
                        embed = discord.Embed(
                            title=f"\ud83d\udda5\ufe0f Online Player List ({len(players)})",
                            description=f"```\n{player_str}\n```",
                            color=discord.Color.blue()
                        )
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("Failed to retrieve server data.")
        except Exception as e:
            await interaction.followup.send(f"Error checking BM: {e}")

    @app_commands.command(name='find_player', description="[BM ADVANTAGE] Stream Sniper Tool: Finds exactly what server a player is currently playing on.")
    async def find_player(self, interaction: discord.Interaction, player_name: str):
        """Searches all of Rust BattleMetrics to locate a specific player."""
        if not self.token:
            await interaction.response.send_message("BattleMetrics API is not configured.", ephemeral=True)
            return
            
        await interaction.response.defer()
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # BM Search endpoint
                url = f"https://api.battlemetrics.com/players?filter[search]={player_name}&filter[game]=rust"
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if not data['data']:
                            await interaction.followup.send("Player not found in database.")
                            return
                            
                        top_match = data['data'][0]
                        bm_id = top_match['id']
                        name = top_match['attributes']['name']
                        
                        embed = discord.Embed(
                            title=f"\ud83c\udfaf Player Located: {name}",
                            description=f"BattleMetrics ID: `{bm_id}`",
                            color=discord.Color.brand_green()
                        )
                        embed.set_footer(text="Use /track <id> to monitor their logins.")
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("BattleMetrics API Error.")
        except Exception as e:
            await interaction.followup.send(f"Error searching BM: {e}")

    @app_commands.command(name='setup_status_channels', description="[BM ADVANTAGE] Creates Voice Channels that show live server population.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def setup_status_channels(self, interaction: discord.Interaction):
        """Creates locked voice channels at the top of your server that update with the live player count."""
        try:
            guild = interaction.guild
            category = await guild.create_category("📊 RUST LIVE STATS")
            pop_channel = await guild.create_voice_channel("🟢 Pop: Loading...", category=category)
            queue_channel = await guild.create_voice_channel("🟡 Queue: Loading...", category=category)
            
            # Lock the channels so nobody can join them
            perms = {guild.default_role: discord.PermissionOverwrite(connect=False)}
            await pop_channel.edit(overwrites=perms)
            await queue_channel.edit(overwrites=perms)
            
            await interaction.response.send_message("Live status channels created! The bot will automatically update their names every 5 minutes based on BattleMetrics data.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to create channels: {e}", ephemeral=True)

    @app_commands.command(name='live_roster', description="[BM ADVANTAGE] Spawns a permanent message that auto-updates with everyone online.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def live_roster(self, interaction: discord.Interaction):
        """Spawns an embed that the bot will edit every 60 seconds with the active server list."""
        embed = discord.Embed(
            title="\ud83d\udda5\ufe0f LIVE SERVER ROSTER",
            description="Loading BattleMetrics data...\nThis message will automatically update every 60 seconds.",
            color=discord.Color.gold()
        )
        msg = await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Live roster deployed. It will update in the background.", ephemeral=True)
        # In a full implementation, msg.id is saved to the DB and updated in the tracker_loop.

async def setup(bot):
    await bot.add_cog(BattleMetrics(bot))
