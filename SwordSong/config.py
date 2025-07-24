import os
import discord
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
TOKEN = os.getenv("discordToken")
if not TOKEN:
    print("Error: DISCORDTOKEN is not found in the .env file.")
    exit(1)

botDir = Path(__file__).parent
dataDir = botDir / "data"
dataDir.mkdir(exist_ok = True)
dataBasePath = Path(os.getenv("dataBasePath", dataDir / "game.db"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

initialExtensions = [
    "cogs.combat",
    "cogs.commands"
]
