import discord
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()
admin_user = int(os.getenv('ADMIN_ID')) if os.getenv('ADMIN_ID') else None

class Say(app_commands.Group):
    def __init__(self, tree: app_commands.CommandTree):
        super().__init__(name="say", description="send messages from kyra side")

    @app_commands.command(name="message", description="send messages from kyra side")
    async def say(self, interaction: discord.Interaction, message: str):
        if interaction.user.id != admin_user:
            await interaction.response.send_message("🔐 Permission spell failed, try again with power.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        await interaction.channel.send(message)
        
        try:
            await interaction.delete_original_response()
        except:
            pass

async def setup(tree: app_commands.CommandTree):
    say_group = Say(tree)
    tree.add_command(say_group) 