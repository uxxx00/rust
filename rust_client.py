import asyncio
import os
import logging
from rustplus import RustSocket, CommandOptions
from dotenv import load_dotenv

import database
import discord

load_dotenv()

log = logging.getLogger('rust_client')

IP = os.getenv('RUST_SERVER_IP')
PORT = os.getenv('RUST_SERVER_PORT')
STEAM_ID = os.getenv('RUST_PLAYER_STEAM_ID')
PLAYER_TOKEN = os.getenv('RUST_PLAYER_TOKEN')

socket = None
discord_bot_ref = None
known_events = set()

async def init_rust_socket(bot):
    global socket, discord_bot_ref
    discord_bot_ref = bot
    
    if not all([IP, PORT, STEAM_ID, PLAYER_TOKEN]):
        log.warning("Rust+ credentials missing in .env. Rust features disabled.")
        return
        
    try:
        socket = RustSocket(
            IP, 
            str(PORT), 
            int(STEAM_ID), 
            int(PLAYER_TOKEN),
            command_options=CommandOptions(prefix="!")
        )
        await socket.connect()
        log.info(f"Connected to Rust+ server at {IP}:{PORT}")
        
        asyncio.create_task(keep_alive())
        asyncio.create_task(event_radar_loop())
    except Exception as e:
        log.error(f"Failed to connect to Rust+: {e}")

async def keep_alive():
    while True:
        await asyncio.sleep(60)
        if socket:
            try:
                await socket.get_time()
            except Exception as e:
                log.error(f"Rust+ Keepalive failed: {e}")
                try:
                    await socket.connect()
                except:
                    pass

async def event_radar_loop():
    """Polls map markers to detect active events"""
    global known_events
    await asyncio.sleep(10) # initial delay
    while True:
        if socket:
            try:
                markers = await socket.get_markers()
                current_events = set()
                
                # Types: 2=Cargo, 4=Explosion, 5=Heli, 6=Chinook
                # Not all servers expose all markers
                for m in markers:
                    if m.type in [2, 4, 5, 6]:
                        event_id = f"{m.type}_{m.id}"
                        current_events.add(event_id)
                        
                        if event_id not in known_events:
                            await trigger_discord_event(m.type, m.x, m.y)
                            
                known_events = current_events
            except Exception as e:
                log.error(f"Event radar poll failed: {e}")
                
        await asyncio.sleep(60) # Poll every 60s

async def trigger_discord_event(marker_type: int, x: float, y: float):
    event_names = {
        2: "Cargo Ship",
        4: "Explosion (RAID DETECTED!)",
        5: "Patrol Helicopter",
        6: "Chinook (Hackable Crate)"
    }
    name = event_names.get(marker_type, "Unknown Event")
    
    # If it's an explosion, trigger the mobile app websocket!
    if marker_type == 4:
        try:
            import server
            await server.broadcast_raid_alert()
        except Exception as e:
            log.error(f"Failed to trigger WS Raid Alert: {e}")
    
    channel_id = await database.get_setting('channel_events')
    if not channel_id:
        channel_id = os.getenv('EVENTS_CHANNEL_ID')
        
    if channel_id and discord_bot_ref:
        channel = discord_bot_ref.get_channel(int(channel_id))
        if channel:
            embed = discord.Embed(
                title="\u26a0\ufe0f Event Detected!",
                description=f"The **{name}** has spawned on the map at coordinates `{x}, {y}`!",
                color=discord.Color.red() if marker_type == 4 else discord.Color.gold()
            )
            await channel.send(embed=embed)

async def send_team_message(message: str):
    if socket:
        try:
            await socket.send_team_message(message)
            return True
        except:
            return False
    return False

async def get_server_info():
    if socket:
        try:
            return await socket.get_info()
        except:
            return None
    return None

async def turn_on_smart_switch(entity_id: int):
    if socket:
        try:
            await socket.turn_on_smart_switch(entity_id)
            return True
        except:
            return False
    return False

async def turn_off_smart_switch(entity_id: int):
    if socket:
        try:
            await socket.turn_off_smart_switch(entity_id)
            return True
        except:
            return False
    return False

async def get_entity_info(entity_id: int):
    if socket:
        try:
            return await socket.get_entity_info(entity_id)
        except:
            return None
    return None
