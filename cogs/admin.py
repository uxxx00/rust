import discord
from discord.ext import commands
import logging

import database

log = logging.getLogger('cog.admin')

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name='setchannel', description="Sets the channel for specific notifications (events, alarms, chat)")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction, channel_type: str, channel: discord.TextChannel):
        valid_types = ['events', 'alarms', 'chat', 'info']
        channel_type = channel_type.lower()
        
        if channel_type not in valid_types:
            await interaction.response.send_message(f"Invalid channel type. Valid types are: {', '.join(valid_types)}", ephemeral=True)
            return
            
        await database.set_setting(f'channel_{channel_type}', str(channel.id))
        
        embed = discord.Embed(
            title="Channel Configured \u2705",
            description=f"Successfully set the `{channel_type}` channel to {channel.mention}.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name='link', description="Links your Discord account to your Steam ID for Rust team features")
    async def link_account(self, interaction: discord.Interaction, steam_id: str):
        if not steam_id.isdigit() or len(steam_id) != 17:
            await interaction.response.send_message("Please provide a valid 64-bit Steam ID (17 digits).", ephemeral=True)
            return
            
        await database.link_user(interaction.user.id, steam_id)
        
        embed = discord.Embed(
            title="Account Linked \u2705",
            description=f"Successfully linked your Discord account to Steam ID `{steam_id}`.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
