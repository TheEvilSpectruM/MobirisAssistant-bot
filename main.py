import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong !")

@bot.command()
async def bonjour(ctx):
    await ctx.send(f"👋 Salut {ctx.author.name} !")

bot.run(os.getenv("TOKEN"))

