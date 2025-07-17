import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import importlib.util
import pathlib
import logging
from typing import Optional
import inspect

logging.basicConfig(
    filename='actions.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# action logger
def log_action(action: str, user: Optional[discord.abc.User] = None, target: Optional[discord.abc.User] = None, reason: Optional[str] = None, extra: Optional[str] = None):
    msg = f"{user} (ID: {getattr(user, 'id', 'N/A')}) performed {action}" if user else f"[Unknown User] performed {action}"
    if target:
        msg += f" on {target} (ID: {getattr(target, 'id', 'N/A')})"
    if reason:
        msg += f" | Reason: {reason}"
    if extra:
        msg += f" | {extra}"
    logging.info(msg)

load_dotenv()

intents = discord.Intents.default()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID is not None:
    ADMIN_ID = int(ADMIN_ID)

bot = commands.Bot(command_prefix=commands.when_mentioned_or(), intents=intents)
tree = bot.tree

async def load_commands(): # that old fetc for cmds
    commands_path = pathlib.Path("commands")
    for file in commands_path.glob("*.py"):
        if file.name == "__init__.py":
            continue
        module_name = f"commands.{file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "setup"):
                setup_params = inspect.signature(module.setup).parameters
                if len(setup_params) > 1:
                    await module.setup(tree, bot)
                else:
                    await module.setup(tree)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="with you :)"))
    await load_commands()
    try:
        synced = await tree.sync()
        print(f"synced {len(synced)} cmds")
    except Exception as e:
        print(f"failed to sync cmds, error - {e}")

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: app_commands.Command):
    user = interaction.user
    channel = interaction.channel
    logging.info(f"[SLASH] {user} (ID: {user.id}) ran /{command.name} in #{getattr(channel, 'name', 'DM')} (ID: {getattr(channel, 'id', 'DM')})")

@bot.event
async def on_command_completion(ctx):
    user = ctx.author
    channel = ctx.channel
    logging.info(f"[PREFIX] {user} (ID: {user.id}) ran {ctx.command} in #{getattr(channel, 'name', 'DM')} (ID: {getattr(channel, 'id', 'DM')})")

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("go & set token in .env file")
    bot.run(TOKEN) 