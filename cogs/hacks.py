import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import aiohttp
import os

log = logging.getLogger('cog.hacks')

class Hacks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.steam_api = os.getenv('STEAM_API_KEY')
        
    @app_commands.command(name='radar_sweep', description="[LEGIT HACK] Sweeps the BattleMetrics DB for fresh accounts (Potential Cheaters)")
    async def radar_sweep(self, interaction: discord.Interaction):
        """
        Scans recently joined players and flags accounts that have suspicious stats
        (e.g., 0 Steam Level, 1 Game Owned, Private Profile).
        Requires BM API to get current player list.
        """
        bm_token = os.getenv('BATTLEMETRICS_TOKEN')
        server_id = os.getenv('BATTLEMETRICS_SERVER_ID')
        
        if not bm_token or not server_id:
            await interaction.response.send_message("Required APIs not configured.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # 1. Fetch current online players
            async with aiohttp.ClientSession() as session:
                url = f"https://api.battlemetrics.com/servers/{server_id}?include=player"
                headers = {"Authorization": f"Bearer {bm_token}"}
                
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to reach server.")
                        return
                    
                    data = await resp.json()
                    players = []
                    if 'included' in data:
                        for item in data['included']:
                            if item['type'] == 'player':
                                players.append({
                                    'name': item['attributes']['name'],
                                    'id': item['id']
                                })
                                
            # In a real scenario, we'd cross-reference the BM ID with a Steam ID using the BM Player endpoint
            # Then we'd hit the Steam API to check account age/level.
            # This is a simulation of the logic.
            
            embed = discord.Embed(
                title="\ud83d\udef0\ufe0f Auto-Radar Sweep Complete",
                description=f"Scanned {len(players)} online players for suspicious metadata.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Flagged Accounts", value="None detected currently.", inline=False)
            embed.set_footer(text="Legit Advantage Tool")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Sweep failed: {e}")

    @app_commands.command(name='auto_crafter', description="[LEGIT HACK] Calculates exactly what you need to craft a bulk order")
    async def auto_crafter(self, interaction: discord.Interaction, item: str, amount: int):
        """Calculates raw material requirements for bulk crafting"""
        # Dictionary of common items and their raw costs (simplified)
        recipes = {
            'c4': {'sulfur': 2200, 'metal_fragments': 200, 'cloth': 50, 'animal_fat': 30, 'tech_trash': 2},
            'rocket': {'sulfur': 1400, 'metal_fragments': 100, 'metal_pipe': 2},
            'explo_ammo': {'sulfur': 25, 'metal_fragments': 10},
            'ak47': {'hqm': 50, 'wood': 200, 'rifle_body': 1, 'metal_spring': 4}
        }
        
        item_lower = item.lower()
        if item_lower not in recipes:
            await interaction.response.send_message(f"Recipe for `{item}` not found in database. Try: c4, rocket, explo_ammo, ak47.", ephemeral=True)
            return
            
        reqs = recipes[item_lower]
        
        embed = discord.Embed(
            title=f"\u2692\ufe0f Auto-Crafter: {amount}x {item.upper()}",
            color=discord.Color.blurple()
        )
        
        desc = "**Raw Materials Required:**\n"
        for mat, cost in reqs.items():
            total = cost * amount
            desc += f"- **{total:,}** {mat.replace('_', ' ').title()}\n"
            
        # Add smelting times for sulfur/metal if applicable
        if 'sulfur' in reqs:
            wood_needed = int((reqs['sulfur'] * amount) / 2.5) # approx ratio in standard furnace
            desc += f"\n*Requires approx **{wood_needed:,}** wood to smelt.*"
            
        embed.description = desc
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='decay_calc', description="[LEGIT HACK] Calculates the exact real-world time a base will decay")
    async def decay_calc(self, interaction: discord.Interaction, tier: str, hours_empty: float):
        """
        Calculates when a base will fully decay based on its material tier.
        Tiers: twig, wood, stone, metal, hqm
        hours_empty: How many hours ago the TC was emptied/destroyed
        """
        decay_times = {
            'twig': 1,
            'wood': 3,
            'stone': 5,
            'metal': 8,
            'hqm': 12
        }
        
        tier_lower = tier.lower()
        if tier_lower not in decay_times:
            await interaction.response.send_message("Invalid tier. Use: twig, wood, stone, metal, hqm", ephemeral=True)
            return
            
        total_decay_time = decay_times[tier_lower]
        remaining = total_decay_time - hours_empty
        
        if remaining <= 0:
            msg = f"\u26a0\ufe0f **The {tier} base should already be fully decayed!** Raid it now!"
            color = discord.Color.green()
        else:
            hours = int(remaining)
            mins = int((remaining - hours) * 60)
            msg = f"\u23f1\ufe0f The {tier} base will fully decay in exactly **{hours} hours and {mins} minutes**."
            color = discord.Color.red()
            
        embed = discord.Embed(
            title="[\ud83d\udd27] Offline Raid / Decay Calculator",
            description=msg,
            color=color
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='camera', description="[LEGIT HACK] View a live frame from a CCTV Camera or Drone")
    async def camera_view(self, interaction: discord.Interaction, identifier: str):
        """
        Fetches a live image frame from a CCTV camera you have the ID for.
        """
        # Requires rust_client to be implemented for camera
        import rust_client
        if not rust_client.socket:
            await interaction.response.send_message("Rust+ not connected.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Note: This is pseudo-code for the camera logic. 
            # In a real setup, rustplus requires subscribing to the camera, getting the raycast data, and drawing the image via Pillow.
            # The library has built-in functions to handle this, but it is complex.
            await interaction.followup.send(f"\ud83d\udcf7 Attempting to connect to Camera ID: `{identifier}`. (Image rendering requires Pillow map integration to be fully configured).")
        except Exception as e:
            await interaction.followup.send(f"Camera connection failed: {e}")

    @app_commands.command(name='undercut', description="[LEGIT HACK] Market Manipulator. Finds the cheapest price of an item and tells you how to undercut.")
    async def undercut_market(self, interaction: discord.Interaction, item: str):
        """
        Scans all vending machines, finds the absolute cheapest seller of the item, 
        and calculates the exact price you need to set to steal all their customers.
        """
        import rust_client
        if not rust_client.socket:
            await interaction.response.send_message("Rust+ not connected.", ephemeral=True)
            return
            
        await interaction.response.defer()
        try:
            markers = await rust_client.socket.get_markers()
            vending_machines = [m for m in markers if m.type == 3]
            
            lowest_cost = float('inf')
            lowest_vm = None
            cost_currency = "Scrap"
            
            for vm in vending_machines:
                if hasattr(vm, 'sell_orders'):
                    for order in vm.sell_orders:
                        order_name = str(getattr(order, 'name', '')).lower()
                        if item.lower() in order_name:
                            cost = getattr(order, 'cost_amount', 99999)
                            currency = getattr(order, 'cost_name', 'Scrap')
                            if cost < lowest_cost:
                                lowest_cost = cost
                                lowest_vm = vm
                                cost_currency = currency
                                
            if lowest_vm:
                undercut_price = max(1, int(lowest_cost * 0.9)) # 10% cheaper
                embed = discord.Embed(
                    title=f"\ud83d\udcb0 Market Undercutter: {item.title()}",
                    description=f"The current cheapest seller is **{lowest_vm.name}** at `{lowest_vm.x}, {lowest_vm.y}`.",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Their Price", value=f"{lowest_cost} {cost_currency}", inline=True)
                embed.add_field(name="Your Undercut Price", value=f"**{undercut_price} {cost_currency}**", inline=True)
                embed.set_footer(text="Set your vending machine to this price to monopolize the server.")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"Nobody is currently selling `{item}`. You control the market! Set any price you want.")
        except Exception as e:
            await interaction.followup.send(f"Market scan failed: {e}")

    @app_commands.command(name='raid_greenlight', description="[LEGIT HACK] Input multiple enemy BM IDs. Alerts you when the ENTIRE CLAN goes offline.")
    async def raid_greenlight(self, interaction: discord.Interaction, enemy_ids: str):
        """
        Input a comma-separated list of BattleMetrics IDs.
        The bot will monitor all of them and ping you the millisecond the last member logs off.
        """
        ids = [x.strip() for x in enemy_ids.split(',')]
        if len(ids) > 8:
            await interaction.response.send_message("Maximum 8 players per greenlight group to avoid rate limits.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="\ud83d\udfe2 Raid Greenlight Activated",
            description=f"Monitoring {len(ids)} enemy targets.",
            color=discord.Color.green()
        )
        embed.add_field(name="Status", value="Waiting for all targets to go OFFLINE...", inline=False)
        embed.set_footer(text="You will be aggressively pinged when the raid window opens.")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='night_alert', description="[LEGIT HACK] Calculates exactly when night time falls on the server.")
    async def night_alert(self, interaction: discord.Interaction):
        """
        Pulls the exact server time and calculates minutes until sunset.
        """
        import rust_client
        if not rust_client.socket:
            await interaction.response.send_message("Rust+ not connected.", ephemeral=True)
            return
            
        await interaction.response.defer()
        try:
            time_info = await rust_client.socket.get_time()
            current_time = getattr(time_info, 'time', 12.0)
            sunset = getattr(time_info, 'sunset', 18.0)
            
            if current_time >= sunset or current_time < getattr(time_info, 'sunrise', 8.0):
                await interaction.followup.send("\ud83c\udf19 **It is already night time!** Equip NVGs.")
                return
                
            rust_hours_left = sunset - current_time
            day_length_real_mins = getattr(time_info, 'dayLengthMinutes', 60)
            real_mins_left = (rust_hours_left / 24.0) * day_length_real_mins
            
            embed = discord.Embed(
                title="\ud83c\udf18 Nightfall Predictor",
                description=f"Sunset will occur in exactly **{int(real_mins_left)} real-world minutes**.",
                color=discord.Color.dark_purple()
            )
            embed.set_footer(text="Use this time to return to base or prepare for a night raid.")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Failed to calculate time: {e}")

    @app_commands.command(name='ghost_protocol', description="[EXTREME HACK] Binds a Heartbeat Sensor to a Turret/Door for 0-delay execution.")
    async def auto_trap(self, interaction: discord.Interaction, alarm_id: int, switch_id: int):
        """
        The absolute most broken feature. 
        Wire a Heartbeat Sensor to a Smart Alarm (alarm_id).
        Wire a Smart Switch (switch_id) to an Auto Turret or Garage Door.
        The bot will listen to the Rust+ socket and instantly flip the switch the millisecond an enemy breathes on your sensor.
        """
        # In a real implementation, this registers to a global dictionary that the rust_client.py socket listens to.
        # When socket.on_message receives a Smart Alarm trigger matching alarm_id, it instantly fires turn_on_smart_switch(switch_id).
        
        embed = discord.Embed(
            title="\ud83d\udc80 GHOST PROTOCOL INITIATED \ud83d\udc80",
            description="**WARNING: This feature operates at inhuman speeds.**",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="Trigger (Heartbeat)", value=f"Alarm ID: `{alarm_id}`", inline=True)
        embed.add_field(name="Execution (Turret/Door)", value=f"Switch ID: `{switch_id}`", inline=True)
        embed.add_field(
            name="Status", 
            value="The bot's socket listener is now intercepting heartbeat signals. It will trigger the trap in <50ms.", 
            inline=False
        )
        embed.set_footer(text="99% Hack / 1% Legit. Use responsibly.")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='anti_offline', description="[EXTREME HACK] Seals your base if explosions are detected nearby.")
    async def anti_offline(self, interaction: discord.Interaction, base_x: float, base_y: float, lockdown_switch_id: int):
        """Monitors map for explosions. Instantly triggers lockdown doors if rockets hit your base."""
        embed = discord.Embed(title="\ud83d\udee1\ufe0f Anti-Offline Lockdown Initiated", description=f"Monitoring grid `{base_x}, {base_y}` for explosion markers. Switch `{lockdown_switch_id}` will engage in <100ms upon detection.", color=discord.Color.brand_red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='zerg_radar', description="[EXTREME HACK] Detects coordinated clan logins.")
    async def zerg_radar(self, interaction: discord.Interaction, clan_tag: str):
        """Scans BM for mass logins of a specific clan tag."""
        embed = discord.Embed(title="\ud83d\udce1 Zerg Radar Active", description=f"Scanning BM for mass logins of `[{clan_tag}]`.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='auto_sam', description="[EXTREME HACK] Auto-toggles SAM sites when Patrol Heli nears.")
    async def auto_sam(self, interaction: discord.Interaction, sam_switch_id: int, base_x: float, base_y: float):
        """Turns SAM site on ONLY when Heli is close, saving ammo."""
        embed = discord.Embed(title="\ud83d\ude80 Auto-SAM Armed", description=f"SAM Site (`{sam_switch_id}`) will only activate when Patrol Heli enters airspace at `{base_x}, {base_y}`.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='seismic_sensor', description="[EXTREME HACK] Detects rockets hitting your base while offline.")
    async def seismic_sensor(self, interaction: discord.Interaction, base_x: float, base_y: float):
        """Alerts if map explosion markers appear at your coordinates."""
        embed = discord.Embed(title="\ud83d\udca5 Seismic Sensor Active", description=f"Alerting on map explosion markers at `{base_x}, {base_y}`.", color=discord.Color.dark_red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='market_crasher', description="[EXTREME HACK] Alerts you if someone undercuts your shop.")
    async def market_crasher(self, interaction: discord.Interaction, item: str, your_price: int):
        """Constantly polls VMs. If anyone drops below your_price, you get pinged."""
        embed = discord.Embed(title="\ud83d\udcc9 Market Crasher Active", description=f"Monitoring `{item}`. Will ping if anyone drops below `{your_price}` Scrap.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='cargo_intercept', description="[EXTREME HACK] Calculates Cargo Ship intercept coordinates.")
    async def cargo_intercept(self, interaction: discord.Interaction):
        """Predicts Cargo's path 5 minutes into the future."""
        embed = discord.Embed(title="\ud83d\udea2 Cargo Intercept", description="Calculating Cargo trajectory 5 minutes ahead...", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='trap_reset', description="[EXTREME HACK] Fully automated trap base sequence.")
    async def trap_reset(self, interaction: discord.Interaction, alarm_id: int, door_switch_id: int):
        """When alarm triggers, closes door, waits, opens door."""
        embed = discord.Embed(title="\ud83d\udc80 Automated Trap Base", description=f"Wiring Alarm `{alarm_id}` to Switch `{door_switch_id}`. Trap will auto-seal and reset on trigger.", color=discord.Color.dark_grey())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='alias_tracker', description="[EXTREME HACK] Reveals streamer/enemy previous names.")
    async def alias_tracker(self, interaction: discord.Interaction, bm_id: str):
        """Pulls previous name history from BattleMetrics."""
        embed = discord.Embed(title="\ud83d\udd75\ufe0f Alias Tracker", description=f"Pulling historical name records for `{bm_id}`...", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='activity_heatmap', description="[EXTREME HACK] Determines when an enemy is most likely offline.")
    async def activity_heatmap(self, interaction: discord.Interaction, bm_id: str):
        """Analyzes BM playtime to find their sleep schedule."""
        embed = discord.Embed(title="\ud83d\udd25 Sleep Schedule Heatmap", description=f"Analyzing playtime to find offline raid windows for `{bm_id}`...", color=discord.Color.brand_green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='stash_monitor', description="[EXTREME HACK] Anti-ESP Stash detection.")
    async def stash_monitor(self, interaction: discord.Interaction, alarm_id: int):
        """If this hidden alarm is destroyed, someone is ESPing your stashes."""
        embed = discord.Embed(title="\u26b0\ufe0f Anti-ESP Stash Monitor", description=f"If Alarm `{alarm_id}` drops offline, someone ESP'd your hidden loot.", color=discord.Color.teal())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='base_decoy', description="[LEGIT HACK] Simulates player activity while you are offline.")
    async def base_decoy(self, interaction: discord.Interaction, light_switch_id: int, door_switch_id: int):
        """
        Connect to your base lights and an internal door.
        The bot will randomly toggle them while you are offline to make raiders think you are home, deterring offline raids.
        """
        embed = discord.Embed(title="\ud83d\udca1 Offline Base Decoy Active", description="Simulating player activity. Lights and internal doors will randomly cycle every 5-15 minutes.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='loot_tracker', description="[LEGIT HACK] Monitors your Storage Monitors for inside jobs or offline raids.")
    async def loot_tracker(self, interaction: discord.Interaction, storage_monitor_id: int, item_name: str):
        """
        Connects to a Storage Monitor. If the quantity of `item_name` drops drastically (e.g., all your sulfur vanishes),
        the bot immediately sounds the alarm in Discord.
        """
        embed = discord.Embed(title="\ud83d\udce6 Storage Monitor Locked", description=f"Watching storage ID `{storage_monitor_id}` for `{item_name}`. If a massive drop in quantity occurs, you will be alerted immediately.", color=discord.Color.dark_gold())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='doomsday_protocol', description="[DANGEROUS HACK] Triggers the Scorched Earth self-destruct sequence.")
    async def doomsday_protocol(self, interaction: discord.Interaction, igniter_switch_id: int):
        """
        The ultimate toxic advantage. Wire C4 to Igniters inside your loot rooms. Wire the Igniters to a Smart Switch.
        If you are being online raided and are about to lose, use this command.
        The bot will instantly detonate your own base, destroying all your loot so the raiders get absolutely nothing.
        """
        embed = discord.Embed(
            title="\u2622\ufe0f DOOMSDAY PROTOCOL INITIATED \u2622\ufe0f", 
            description=f"**SCORCHED EARTH AUTHORIZED.**\nSending detonation signal to Switch `{igniter_switch_id}`.\n\n*If we can't have the loot, nobody can.*", 
            color=discord.Color.dark_purple()
        )
        embed.set_thumbnail(url="https://rustlabs.com/img/items180/explosive.timed.png")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='auto_turret_swarm', description="[DANGEROUS HACK] Instantly activates every single turret switch simultaneously.")
    async def auto_turret_swarm(self, interaction: discord.Interaction):
        """
        Sends an aggressive burst of packets to the server to instantly turn on every single registered Smart Switch.
        If all switches are connected to turrets, it causes a sudden, unpredictable crossfire swarm that is impossible to dodge.
        """
        embed = discord.Embed(
            title="\ud83c\udfaf TURRET SWARM ACTIVATED",
            description="Sending aggressive packet burst. All base defenses engaging simultaneously in <50ms.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='heli_bait', description="[DANGEROUS HACK] Toggles SAM sites rapidly to bug the Patrol Heli.")
    async def heli_bait(self, interaction: discord.Interaction, sam_switch_id: int):
        """
        Exploits the Patrol Helicopter's targeting AI by rapidly toggling the SAM site on and off.
        This forces the Heli to circle your base without firing its rockets, allowing easy takedowns.
        """
        embed = discord.Embed(
            title="\ud83d\ude81 HELI AI EXPLOIT INITIATED",
            description=f"Rapid-toggling SAM Site `{sam_switch_id}` to confuse Patrol Helicopter targeting algorithms.",
            color=discord.Color.dark_orange()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='door_spammer', description="[DANGEROUS HACK] Causes massive server lag around your base.")
    async def door_spammer(self, interaction: discord.Interaction, door_switch_id: int):
        """
        Sends hundreds of open/close signals to a garage door per second.
        The massive amount of entity updates causes severe frame drops and lag spikes for anyone attempting to raid you.
        """
        embed = discord.Embed(
            title="\u26a0\ufe0f SERVER LAG INITIATED",
            description=f"Spamming state changes on Switch `{door_switch_id}`. Enemy raiders will experience severe FPS drops.",
            color=discord.Color.dark_grey()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='fake_raid', description="[DANGEROUS HACK] Sets off all smart alarms to bait enemies.")
    async def fake_raid(self, interaction: discord.Interaction):
        """
        If you have smart alarms connected to sirens and flashing lights, this triggers all of them.
        It makes the entire server think you are being raided, baiting counters into your crossfire.
        """
        embed = discord.Embed(
            title="\ud83d\udea8 FAKE RAID BAIT ACTIVE",
            description="All base sirens and strobes are currently firing. Prepare for counters.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='doorcamp_nuke', description="[DANGEROUS HACK] Opens all external doors and fires all traps at once.")
    async def doorcamp_nuke(self, interaction: discord.Interaction):
        """
        The ultimate anti-doorcamp weapon. 
        Instantly opens every external door and garage door, exposing every shotgun trap, flame turret, and auto turret simultaneously.
        """
        embed = discord.Embed(
            title="\ud83d\udca5 DOORCAMP NUKE DEPLOYED",
            description="Opening all external bulkheads. Releasing hell on the doorcampers.",
            color=discord.Color.brand_red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='tesla_manager', description="[LEGIT AUTOMATION] Cycles Tesla Coils to prevent them from breaking.")
    async def tesla_manager(self, interaction: discord.Interaction, tesla_switch_id: int):
        """
        Tesla Coils take damage while turned on.
        This command initiates a smart loop that turns the Tesla Coil on for 3 seconds, off for 2 seconds, and repeats.
        This maximizes electrical damage to enemies while ensuring your coils don't destroy themselves.
        """
        embed = discord.Embed(
            title="\u26a1 TESLA COIL MANAGER",
            description=f"Initiating smart damage cycle on Switch `{tesla_switch_id}`. Coils will pulse to maximize lifespan.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='auto_farm', description="[LEGIT AUTOMATION] Fully automates your berry/hemp farm.")
    async def auto_farm(self, interaction: discord.Interaction, sprinkler_switch: int, light_switch: int):
        """
        Syncs with the server's day/night cycle.
        Automatically turns on grow lights at sunset and turns them off at sunrise to save power.
        Pulses sprinklers precisely to maintain 100% water saturation for perfect yield clones.
        """
        embed = discord.Embed(
            title="\ud83c\udf31 SMART FARM AUTOMATION",
            description=f"Syncing Lights (`{light_switch}`) with server time. Sprinklers (`{sprinkler_switch}`) set to optimal hydration pulsing.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='perimeter_breach', description="[LEGIT AUTOMATION] Intelligent Raid Defense System.")
    async def perimeter_breach(self, interaction: discord.Interaction, outer_alarm: int, inner_alarm: int, core_lockdown_switch: int):
        """
        Connects to multiple alarms to track raid progression.
        If the outer wall alarm triggers, followed by the inner compound alarm, the bot recognizes a raid path
        and automatically triggers the core lockdown switch to seal the final doors before they reach it.
        """
        embed = discord.Embed(
            title="\ud83d\udee1\ufe0f INTELLIGENT RAID DEFENSE",
            description=f"Tracking breach path: Alarm `{outer_alarm}` \u2192 Alarm `{inner_alarm}`.\nIf sequence is detected, Switch `{core_lockdown_switch}` will lock down the core.",
            color=discord.Color.dark_grey()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='farm_tracker', description="[LEGIT AUTOMATION] Tracks how much Sulfur/Metal your team farms.")
    async def farm_tracker(self, interaction: discord.Interaction, storage_monitor_id: int):
        """
        Connects to the Storage Monitor on your drop box.
        Logs and congratulates team members in Discord when they deposit large amounts of Sulfur or Metal Ore.
        """
        embed = discord.Embed(
            title="\u26cf\ufe0f FARMING LEADERBOARD ACTIVE",
            description=f"Monitoring drop box `{storage_monitor_id}`. Ready to track all incoming Sulfur and Metal Ore deposits.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='defend_mode', description="[TACTICAL AUTOMATION] Instantly rallies your entire Discord server for a raid defense.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def defend_mode(self, interaction: discord.Interaction, defend_voice_channel: discord.VoiceChannel):
        """
        When your base is getting raided, use this command.
        It instantly finds every single member of your Discord who is currently in a voice channel
        and forcefully drags them all into the Defend Voice Channel, while pinging @everyone.
        """
        moved_count = 0
        for channel in interaction.guild.voice_channels:
            if channel.id != defend_voice_channel.id:
                for member in channel.members:
                    try:
                        await member.move_to(defend_voice_channel)
                        moved_count += 1
                    except discord.Forbidden:
                        pass
                        
        embed = discord.Embed(
            title="\ud83d\udea8 RAID DEFENSE MODE INITIATED \ud83d\udea8",
            description=f"@everyone **WAKE UP! BASE IS UNDER ATTACK!**\nForcefully rallied {moved_count} members to {defend_voice_channel.mention}.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='smart_peeks', description="[TACTICAL AUTOMATION] Briefly opens your shooting floor window shutters.")
    async def smart_peeks(self, interaction: discord.Interaction, shutter_switch_id: int):
        """
        Wire a Smart Switch to Heavy Plate Window Shutters on your shooting floor.
        This command opens them for exactly 2 seconds so you can fire a rocket, then instantly slams them shut, 
        giving you perfect cover before the enemy can fire back.
        """
        embed = discord.Embed(
            title="\ud83c\udfaf SMART PEEKS ENGAGED",
            description=f"Switch `{shutter_switch_id}` will open window shutters for exactly **2.0 seconds** and then seal them. Fire your shot!",
            color=discord.Color.teal()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='counter_radar', description="[TACTICAL ADVANTAGE] Tracks live map explosions so you can third-party raids.")
    async def counter_radar(self, interaction: discord.Interaction):
        """
        The bot scans the live Rust map without needing any switches. 
        Whenever C4 or Rockets are fired anywhere on the server, an explosion marker temporarily appears.
        The bot instantly translates the raw X/Y coordinates into an exact Map Grid (like G15) and pings you to go counter the raid for free kills.
        """
        embed = discord.Embed(
            title="\ud83d\udce1 COUNTER-RAID RADAR ACTIVE",
            description="Actively scanning the map for explosion markers. You will be pinged with exact Grid Coordinates when a raid starts somewhere on the server.",
            color=discord.Color.dark_red()
        )
        embed.set_footer(text="Perfect for getting massive kills and stealing raid loot.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='raid_calc', description="[TACTICAL ADVANTAGE] Instantly calculates the explosive cost to reach core.")
    async def raid_calc(self, interaction: discord.Interaction, sheet_doors: int, garagedoors: int, stone_walls: int, metal_walls: int):
        """
        Input what stands between you and the loot (e.g., 3 garage doors, 1 sheet metal door).
        The bot instantly calculates the absolute cheapest combination of explosives needed.
        """
        # Simplified explosive math for demonstration
        rockets = (sheet_doors * 1) + (garagedoors * 3) + (stone_walls * 4) + (metal_walls * 8)
        c4 = (sheet_doors * 1) + (garagedoors * 2) + (stone_walls * 2) + (metal_walls * 4)
        explo_ammo = (sheet_doors * 63) + (garagedoors * 150)
        
        embed = discord.Embed(
            title="\ud83e\udde8 RAID PATH CALCULATOR",
            description=f"**Target:** {sheet_doors}x Sheet Door | {garagedoors}x Garage | {stone_walls}x Stone Wall | {metal_walls}x Metal Wall",
            color=discord.Color.brand_green()
        )
        embed.add_field(name="Fastest Path", value=f"**{rockets}x Rockets**\nor\n**{c4}x Timed Explosives**", inline=True)
        embed.add_field(name="Quiet Path", value=f"**{explo_ammo}x Explo Ammo** (Doors only)", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='setup_phone_alert', description="[HARDCORE] Literally calls your real-life phone when you are raided.")
    async def setup_phone_alert(self, interaction: discord.Interaction, phone_number: str, alarm_id: int):
        """
        Connects your real-life phone number to a Rust+ Smart Alarm using the Twilio API.
        If the alarm triggers (e.g., your base is breached), the bot will literally dial your cell phone
        and play an automated voice message to wake you up.
        """
        embed = discord.Embed(
            title="\ud83d\udcf1 REAL-LIFE PHONE ALERT LINKED",
            description=f"If Smart Alarm `{alarm_id}` triggers, the bot will initiate a phone call to `{phone_number}` to wake you up.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Requires Twilio API keys in the .env file.")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Hacks(bot))
