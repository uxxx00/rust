import discord
from discord.ext import commands
import logging
import asyncio

import rust_client

log = logging.getLogger('cog.info')

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='server')
    async def server_info(self, ctx):
        """Displays current server information"""
        info = await rust_client.get_server_info()
        if info:
            embed = discord.Embed(
                title=f"Server Information - {info.name}",
                color=discord.Color.gold()
            )
            embed.add_field(name="Players", value=f"{info.players} / {info.max_players}", inline=True)
            embed.add_field(name="Queued", value=f"{info.queued_players}", inline=True)
            embed.add_field(name="Map Size", value=f"{info.size}", inline=True)
            
            embed.set_footer(text="Rust+ Companion Bot")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("Could not retrieve server information. Is the Rust+ connection active?")

    @commands.command(name='vending')
    async def find_vending_item(self, ctx, *, item_name: str):
        """Searches vending machines across the map for a specific item"""
        if not rust_client.socket:
            await ctx.send("Rust+ is not connected.")
            return
            
        loading_msg = await ctx.send(f"\u23f3 Scanning map for `{item_name}`...")
        
        try:
            markers = await rust_client.socket.get_markers()
            
            # Filter for Vending Machines (Type 3)
            vending_machines = [m for m in markers if m.type == 3]
            
            results = []
            
            for vm in vending_machines:
                # vm.sellOrders might contain the list of items being sold if the API provides it
                # For basic rustplus we match by name if the name indicates what's being sold
                # Usually vending machine names are custom set by the player
                
                # In the rustplus library, vending machine items are in sellOrders.
                # Let's check if the library supports sell_orders
                if hasattr(vm, 'sell_orders'):
                    for order in vm.sell_orders:
                        # order.item_id usually, or order.name
                        # Assuming order object has item_name or we check the VM name as fallback
                        order_item_name = str(getattr(order, 'name', '')).lower()
                        item_id = getattr(order, 'item_id', '')
                        
                        if item_name.lower() in order_item_name or item_name.lower() in str(item_id):
                            cost_amount = getattr(order, 'cost_amount', '?')
                            cost_item = getattr(order, 'cost_name', 'Scrap') # fallback
                            amount = getattr(order, 'amount', '?')
                            
                            results.append(f"**{vm.name}** at `{vm.x}, {vm.y}` is selling **{amount}x** for **{cost_amount} {cost_item}**")
                
                # Fallback: check if the item name is in the Vending Machine title
                elif item_name.lower() in vm.name.lower():
                    results.append(f"Found machine named **{vm.name}** at coordinates `{vm.x}, {vm.y}`.")
            
            if not results:
                await loading_msg.edit(content=f"\u274c Could not find any vending machines selling `{item_name}`.")
                return
                
            # Limit results if too many
            if len(results) > 10:
                results = results[:10]
                results.append("*...and more (showing top 10)*")
                
            embed = discord.Embed(
                title=f"\ud83d\uded2 Vending Machine Sniper: {item_name}",
                description="\n".join(results),
                color=discord.Color.green()
            )
            await loading_msg.edit(content=None, embed=embed)
            
        except Exception as e:
            log.error(f"Vending machine search failed: {e}")
            await loading_msg.edit(content="\u274c Failed to scan the map. Is Rust+ connected?")

async def setup(bot):
    await bot.add_cog(Info(bot))
