import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
admin_user = int(os.getenv('ADMIN_ID')) if os.getenv('ADMIN_ID') else None

class Report(app_commands.Group):
    def __init__(self, tree: app_commands.CommandTree):
        super().__init__(name="report", description="Report issues or concerns")

    @app_commands.command(name="issue", description="Report issues or concerns")
    @app_commands.choices(issue_type=[
        app_commands.Choice(name="Bug", value="bug"),
        app_commands.Choice(name="User Behavior", value="user"),
        app_commands.Choice(name="Server Issue", value="server"),
        app_commands.Choice(name="Bot Issue", value="bot"),
        app_commands.Choice(name="Other", value="other")
    ])
    async def report(
        self, 
        interaction: discord.Interaction, 
        issue_type: app_commands.Choice[str],
        description: str,
        evidence: str = None
    ):
        embed = discord.Embed(
            title=f"<:Report_Message:1395536703049175070> New Report",
            description=description,
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="Reporter",
            value=f"{interaction.user.name} (ID: {interaction.user.id})",
            inline=False
        )
        
        embed.add_field(
            name="Location",
            value=f"Channel: {interaction.channel.name}\nServer: {interaction.guild.name}\nCategory: {issue_type.name}",

            inline=False
        )
        
        if evidence:
            embed.add_field(
                name="Evidence",
                value=evidence,
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        try:
            if admin_user:
                admin = await interaction.client.fetch_user(admin_user)
                if admin:
                    await admin.send(embed=embed)
            
            await interaction.response.send_message(
                "<:policeofficer:1395537152074584104> Thank you for your report. It has been submitted.",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                "There was an error submitting your report. Please try again later or contact an administrator directly.",
                ephemeral=True
            )

async def setup(tree: app_commands.CommandTree):
    report_group = Report(tree)
    tree.add_command(report_group)