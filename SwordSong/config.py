import os
import discord
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
TOKEN = os.getenv('DISCORDTOKEN')
if not TOKEN:
    print("Error: DISCORDTOKEN is not found in the .env file.")
    exit(1)

BOT_DIR = Path(__file__).parent
DATA_DIR = BOT_DIR / "data"
DATA_DIR.mkdir(exist_ok = True)
DATABASEPATH = Path(os.getenv("DATABASEPATH", DATA_DIR / "game.db"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

initialExtensions = [
    "cogs.combat",
    "cogs.shop",
    "cogs.inventory",
    "cogs.base"
]
