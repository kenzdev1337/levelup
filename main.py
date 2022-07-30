import asyncio
import discord
from discord.ext import commands
import os
import settings

os.chdir(settings.PATH)
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="---", intents=intents, help_command=None, status=discord.Game(name="full rewrite!"))

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.tree.sync(guild=discord.Object(settings.SUPPORT_GUILD))
    print(f"Bot logged as {bot.user.name}#{bot.user.discriminator}")
    
for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        asyncio.run(bot.load_extension(f'cogs.{filename[:-3]}'))
bot.run(settings.TOKEN)