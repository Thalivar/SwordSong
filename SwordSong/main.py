import discord
from discord.ext import commands
from discord.ext.commands import cooldowns, BucketType
from dotenv import load_dotenv
from database import DataBase
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
db = DataBase()


client.run(TOKEN)