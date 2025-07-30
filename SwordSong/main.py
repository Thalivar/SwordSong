import discord
from config import TOKEN, botDir, dataDir, intents, dataBasePath, initialExtensions
from discord.ext import commands
from services.database import Database
from services.combadsys import combatSystem
import json
import os
import sys
import asyncio

try:
    with open(dataDir / 'areas.json', 'r') as f:
        areas = json.load(f)
    with open(dataDir / 'items.json', 'r') as f:
        items = json.load(f)
except FileNotFoundError as e:
    print(f"Error the required JSON file was not found: {e}")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error the JSON file is not properly formatted: {e}")
    exit(1)

client = commands.Bot(
    command_prefix=".",
    intents=intents,
    help_command=None,
   case_insensitive=True
)
db = Database(dataBasePath)
combatSystems = combatSystem(db, areas, items)
client.db = db
client.combatSystem = combatSystems
client.shopItems = items["shop"]
client.areas = areas["areas"]

async def loadExtensions():
    for ext in initialExtensions:
        try:
            await client.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load {ext}: {e}")
            import traceback
            traceback.print_exc()

@client.event
async def on_ready():
    await client.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = "Over Azefarnia"))
    print(f"Logged in as {client.user}")

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is currently on cooldown. Please try again in {error.retry_after:.2f}s.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"That command does not exist. Use `.help` to see a list of available commands.")

async def main():
    await loadExtensions()
    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())