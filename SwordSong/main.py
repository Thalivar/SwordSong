import discord
from discord.ext import commands
from discord.ext.commands import cooldowns, BucketType
from dotenv import load_dotenv
from database import Database
from pathlib import Path
import asyncio
import random
import json
import os

# === Load the environment variables ===
load_dotenv()
TOKEN = os.getenv("DISCORDTOKEN")

if not TOKEN:
    print("Error: DISCORDTOKEN is not found in the .env file.")
    exit(1)

# === Setup the Bot ===
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=".", intents = intents)
db = Database()

# === Get the directory to data folder ===
BOT_DIR = Path(__file__).parent
DATA_DIR = BOT_DIR / "data"
DATA_DIR.mkdir(exist_ok = True)

# === Loading the game data ===
try:
    with open(DATA_DIR / 'areas.json', 'r') as f:
        areas = json.load(f)
    with open(DATA_DIR / 'items.json', 'r') as f:
        items = json.load(f)
except FileNotFoundError as e:
    print(f"Error the required JSON file was not found: {e}")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error the JSON file is not properly formatted: {e}")
    exit(1)

# === Sets the bot's activity feed and prints a message when the bot is ready ===
@client.event
async def on_ready():
    await client.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = "Over the Azefarnia"))
    print(f"Logged in as {client.user}")

# === error handling for commands ===
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is currently on cooldown. Please try again in {error.retry_after:.2f}s.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"That command does not exist. Use `.help` to see a list of available commands.")

# === Help command to show all available commands ===
@client.command()
async def help(ctx):
    embed = discord.Embed(
        title = "SwordSong Help",
        description = "List of the available commands",
        color = discord.Color.Purple()
    )

    embed.add_field(name = ".start", value = "Start your adventure for the guild SwordSong in Azefarnia", inline = False)
    embed.add_field(name = ".profile", value = "View your character's profile", inline = False)
    embed.add_field(name = ".inventory", value = "View all the wares you currently have in your inventory", inline = False)
    embed.add_field(name = ".shop", value = "View all the items that are available for purchase", inline = False)
    embed.add_field(name = ".but <item>", value = "But the desired items from the shop", inline = False)
    embed.add_field(name = ".sell <item>", value = "Sell an item from your inventory to the shop", inline = False)
    embed.add_field(name = ".equip <item>", value = "Equip a weapon or armor from your inventory", inline = False)
    embed.add_field(name = ".unequip <item>", value = "unequip a weapon or armor that you're currently wearing", inline = False)
    embed.add_field(name = ".adventure", value = "Go on an adventure to hunt monsters and earn loot", inline = False)

client.run(TOKEN)