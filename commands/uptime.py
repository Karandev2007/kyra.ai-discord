import discord
from discord import app_commands, Embed
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
my_admin = os.getenv('ADMIN_ID')
admin_user = int(my_admin) if my_admin else None
theme_color = 0x6f42c1

bot_started = datetime.utcnow()

async def setup(tree: app_commands.CommandTree):
    @tree.command(name="uptime", description="bot uptime")
    async def show_uptime(interaction: discord.Interaction):
        if not interaction.user.id == admin_user:
            no_access = Embed(description="🔐 Permission spell failed, try again with power.", color=theme_color)
            await interaction.response.send_message(embed=no_access, ephemeral=True)
            return

        now = datetime.utcnow()
        time_running = now - bot_started
        
        d = time_running.days
        remaining = time_running.seconds
        h = remaining // 3600
        remaining %= 3600
        m = remaining // 60
        s = remaining % 60

        time_text = f'{d} days, {h} hours, {m} minutes, {s} seconds'
        result = Embed(title="<:blue_bot_v2:1395549990373298198> Bot Uptime", description=time_text, color=theme_color)
        await interaction.response.send_message(embed=result) 