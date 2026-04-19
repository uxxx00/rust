from aiohttp import web
import logging
import json

log = logging.getLogger('webhook_server')
discord_bot_ref = None
mobile_clients = set()

async def handle_kill_webhook(request):
    """
    Expects a JSON payload from a Rust Server Plugin (like DiscordMessages or Rustcord).
    Example Payload: {"killer": "PlayerA", "victim": "PlayerB", "weapon": "AK47", "distance": "50m"}
    """
    try:
        data = await request.json()
        log.info(f"Received Webhook Data: {data}")
        
        if discord_bot_ref:
            # We would typically route this to a specific channel
            import database
            import os
            
            # Use same events channel or a dedicated killfeed channel
            channel_id = await database.get_setting('channel_events') or os.getenv('EVENTS_CHANNEL_ID')
            
            if channel_id:
                channel = discord_bot_ref.get_channel(int(channel_id))
                if channel:
                    killer = data.get('killer', 'Unknown')
                    victim = data.get('victim', 'Unknown')
                    weapon = data.get('weapon', 'Unknown')
                    distance = data.get('distance', '?')
                    
                    # Assuming discord.py is imported in the main context
                    import discord
                    embed = discord.Embed(
                        description=f"\ud83d\udd2b **{killer}** killed **{victim}** using `{weapon}` ({distance})",
                        color=discord.Color.brand_red()
                    )
                    await channel.send(embed=embed)
                    
        return web.Response(text="Success")
    except Exception as e:
        log.error(f"Failed to process webhook: {e}")
        return web.Response(status=500, text="Internal Error")

async def handle_mobile_ws(request):
    ws = web.WebSocketResponse(heartbeat=30.0)
    await ws.prepare(request)
    
    mobile_clients.add(ws)
    log.info(f"Mobile client connected. Total: {len(mobile_clients)}")
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                log.info(f"WS Recv: {data}")
    finally:
        mobile_clients.remove(ws)
    return ws

async def broadcast_raid_alert():
    log.info("Broadcasting RAID ALERT to all mobile clients!")
    payload = json.dumps({"type": "RAID"})
    for ws in list(mobile_clients):
        try:
            await ws.send_str(payload)
        except Exception as e:
            log.error(f"WS Send error: {e}")

async def start_webhook_server(bot, port=8080):
    global discord_bot_ref
    discord_bot_ref = bot
    
    app = web.Application()
    app.router.add_post('/rust-killfeed', handle_kill_webhook)
    app.router.add_get('/', handle_mobile_ws) # WebSocket route
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    log.info(f"Started Webhook/WS Server on port {port}")
    await site.start()
