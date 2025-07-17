import discord
from discord import app_commands
import os
import json
import aiohttp
from dotenv import load_dotenv

load_dotenv()
AI_KEY = os.getenv('AI_KEY')

class ChatAction(discord.app_commands.Choice):
    on = 1
    off = 2
    reset = 3

class Chat:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.conversation_history = {}
        self.disabled_channels = set()
        
    async def call_groq_api(self, user_id: str, message: str) -> str:
        if not AI_KEY:
            return "add ai key in .env file"
            
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            
        self.conversation_history[user_id].append({"role": "user", "content": message})
        
        messages = [
            {"role": "system", "content": "you are Kyra, CTO of QeinTech. you are smart, kind, and a bit playful, but professional when it counts. you talk like a real, approachable person — clear, casual, and human. powered by Qeinova-1, stay friendly and causally less professional and more like a drunk human."},
            *self.conversation_history[user_id][-5:]
        ]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {AI_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-prompt-guard-2-86m",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "top_p": 1,
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    assistant_message = result['choices'][0]['message']['content']
                    
                    self.conversation_history[user_id].append(
                        {"role": "assistant", "content": assistant_message}
                    )
                    
                    return assistant_message
                else:
                    error_text = await response.text()
                    return f"sorry i encountered an error, please try again later."

    async def handle_mention(self, message: discord.Message):
        if message.channel.id in self.disabled_channels:
            return
            
        content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
        
        if not content:
            await message.reply("Looks like you summoned me! What quest shall we embark upon? <:Pepe_Business:1162565546500436079>")
            return

        async with message.channel.typing():
            try:
                response = await self.call_groq_api(str(message.author.id), content)
                sent_message = await message.reply(response)
                
                thinking_messages = [msg async for msg in message.channel.history(limit=5) 
                                  if msg.author == self.bot.user and "is thinking" in msg.content]
                for thinking_msg in thinking_messages:
                    try:
                        await thinking_msg.delete()
                    except:
                        pass
                        
            except Exception as e:
                await message.reply(f"Sorry, I encountered an error: {str(e)}")

class ChatCommands(app_commands.Group):
    def __init__(self, chat_instance: Chat):
        super().__init__(name="chat", description="chat settings")
        self.chat = chat_instance

    @app_commands.command(name="settings", description="Control chat settings")
    @app_commands.choices(action=[
        app_commands.Choice(name="on", value=1),
        app_commands.Choice(name="off", value=2),
        app_commands.Choice(name="reset", value=3),
    ])
    async def chat_settings(self, interaction: discord.Interaction, action: app_commands.Choice[int]):
        if action.value in [1, 2]: 
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("🔐 Permission spell failed, try again with power.", ephemeral=True)
                return
                
            if action.value == 1:
                self.chat.disabled_channels.discard(interaction.channel.id)
                await interaction.response.send_message("KyraAI has been enabled <:PepeWitch:1393629420312596641>", ephemeral=True)
            else:
                self.chat.disabled_channels.add(interaction.channel.id)
                await interaction.response.send_message("KyraAI has been disabled <:PepeWitch:1393629420312596641>", ephemeral=True)
        
        elif action.value == 3:
            user_id = str(interaction.user.id)
            if user_id in self.chat.conversation_history:
                del self.chat.conversation_history[user_id]
                await interaction.response.send_message("<:SkaryHalloweenPumpkin:1167705320118816768> The archives have been swept clean.", ephemeral=True)
            else:
                await interaction.response.send_message("<:Pepe_Business:1162565546500436079> The archive is already empty.", ephemeral=True)

async def setup(tree: app_commands.CommandTree, bot: discord.Client):
    chat = Chat(bot)
    
    chat_commands = ChatCommands(chat)
    tree.add_command(chat_commands)
    
    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
            
        if bot.user.mentioned_in(message) and not message.mention_everyone:
            await chat.handle_mention(message)
            
    return chat