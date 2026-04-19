import discord
from discord.ext import commands
import logging

import database
import rust_client

log = logging.getLogger('cog.devices')

class Devices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='pair')
    async def pair_device(self, ctx, entity_id: int, *, name: str):
        """Pairs a smart device (switch, alarm, monitor)"""
        info = await rust_client.get_entity_info(entity_id)
        if info:
            device_type = str(info.type) # e.g. Switch, Alarm
            await database.add_device(entity_id, name, device_type)
            embed = discord.Embed(
                title="Device Paired \u2705",
                description=f"Successfully paired `{name}` (ID: {entity_id}, Type: {device_type})",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Pairing Failed \u274c",
                description=f"Could not find a device with ID `{entity_id}`. Make sure it's placed and your credentials are correct.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='devices')
    async def list_devices(self, ctx):
        """Lists all paired smart devices"""
        devices = await database.get_all_devices()
        if not devices:
            await ctx.send("No devices are currently paired.")
            return

        embed = discord.Embed(title="Paired Smart Devices", color=discord.Color.blue())
        for device_id, name, d_type in devices:
            embed.add_field(name=f"{name} ({d_type})", value=f"ID: `{device_id}`", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='switch')
    async def toggle_switch(self, ctx, entity_id: int, action: str):
        """Turn a smart switch on or off. Usage: !switch <id> on/off"""
        action = action.lower()
        if action not in ['on', 'off']:
            await ctx.send("Invalid action. Use 'on' or 'off'.")
            return

        success = False
        if action == 'on':
            success = await rust_client.turn_on_smart_switch(entity_id)
        else:
            success = await rust_client.turn_off_smart_switch(entity_id)

        if success:
            embed = discord.Embed(
                title="Switch Toggled \u2705",
                description=f"Successfully turned {action} switch `{entity_id}`.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Action Failed \u274c",
                description=f"Failed to turn {action} switch `{entity_id}`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Devices(bot))
