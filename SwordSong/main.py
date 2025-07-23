import discord
from config import TOKEN, BOT_DIR, DATA_DIR, intents, DATABASEPATH
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from services.database import Database
from services.combadsys import combatSystem
from pathlib import Path
import math
import random
import asyncio
import json
import os

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

client = commands.Bot(command_prefix=".", intents = intents, help_command = None, case_insensitive = True)
db = Database(DATABASEPATH)
combatSystem = combatSystem(db, areas, items)

# === Sets the bot's activity feed and prints a message when the bot is ready ===
@client.event
async def on_ready():
    await client.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = "Over Azefarnia"))
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
@cooldown(1, 4, BucketType.user)
async def help(ctx):
    print("Custom help command called by", ctx.author.name )
    embed = discord.Embed(
        title = "SwordSong Help",
        description = "List of the available commands",
        color = discord.Color.purple()
    )

    embed.add_field(name = ".start", value = "Start your adventure for the guild SwordSong in Azefarnia", inline = False)
    embed.add_field(name = ".profile", value = "View your character's profile", inline = False)
    embed.add_field(name = ".inventory", value = "View all the wares you currently have in your inventory", inline = False)
    embed.add_field(name = ".shop", value = "View all the items that are available for purchase", inline = False)
    embed.add_field(name = ".buy <item>", value = "But the desired items from the shop", inline = False)
    embed.add_field(name = ".sell <item>", value = "Sell an item from your inventory to the shop", inline = False)
    embed.add_field(name = ".equip <item>", value = "Equip a weapon or armor from your inventory", inline = False)
    embed.add_field(name = ".unequip <item>", value = "unequip a weapon or armor that you're currently wearing", inline = False)
    embed.add_field(name = ".adventure", value = "Go on an adventure to hunt monsters and earn loot", inline = False)

    await ctx.send(embed=embed)

"""
System commands
* Consists of .start, .profile, .inventory, .shop, .equip/unequip
* These are commands to access some of the systems of the game will most likely add more in the future however these are the ones i'm currently working
"""

# === Command to create an character to use the rpg commands ===
@client.command()
@cooldown(1, 4, BucketType.user)
async def start(ctx):
    print("Start command was called by", ctx.author.name)
    userID = str(ctx.author.id)
    if db.getCharacter(userID):
        embed = discord.Embed(
            title = "You're already part of the guild.",
            description = "Yu're already enlisted into SwordSong, you unfortunatly cant enroll again.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    embed = discord.Embed(
        title = "Welcome Adventurer!",
        description = "Welcome to SwordSong! What would you like to be called?",
        color = discord.Color.orange()
    )
    await ctx.send(embed = embed)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    try:
        msg = await client.wait_for('message', timeout = 30.0, check = check)
        if db.createCharacter(userID, msg.content):
            defaultArea = "forest"
            if "areas" in areas and areas["areas"]:
                defaultArea = list(areas["areas"].keys())[0]
            embed = discord.Embed(
                title = "Welcome to SwordSong!",
                description = f"Welcome, {msg.content}! You're adventure across Azefarnia begins now.",
                color = discord.Color.green()
            )
            await ctx.send(embed = embed)
        else:
            await ctx.send("An problem occured while trying to enlist you into SwordSong.")
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title = "Timeout",
            description = "You unfortunatly took to long to write down your name. Please try again",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)

# === Command to see your own player stats ===
@client.command()
@cooldown(1, 5, BucketType.user)
async def profile(ctx):
    print("Character profile command was called by", ctx.author.name)
    character = db.getCharacter(str(ctx.author.id))
    if not character:
        embed = discord.Embed(
            title = "You're not part of the guild.",
            description = "You're not part of SwordSong, so you're not able to see your profile.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    embed = discord.Embed(
        title = f"{character['name']}'s Profile",
        color = discord.Color.blue()
    )

    embed.add_field(name = "level", value = character['level'], inline = True)
    embed.add_field(name = "XP", value = f"{character['xp']} / {character['xpToLevel']}", inline = True)
    embed.add_field(name = "Health", value = f"{character['health']} / {character['maxHealth']}", inline = True)
    embed.add_field(name = "Attack", value = character['attack'], inline = True)
    embed.add_field(name = "Defense", value = character['defense'], inline = True)
    embed.add_field(name = "Coins", value = character['coins'], inline = True)

    await ctx.send(embed = embed)

@client.command()
@cooldown(1, 3, BucketType.user)
async def inventory(ctx):
    print(f"Inventory command was called by", ctx.author.name)
    userID = str(ctx.author.id)
    character = db.getCharacter(userID)
    items = db.getInventory(userID)
    if not character:
        embed = discord.Embed(
            title = "You're not part of the guild",
            description = "You're not part of SwordSong, So you don't have a backpack",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return

    if items:
        inventoryText = "\n".join([f"{name}: {qty}" for name, qty in items])
    else:
        inventoryText = "Empty"

    embed = discord.Embed(
        title = f"{character['name']}'s Inventory",
        color = discord.Color.blue()
    )
    
    embed.add_field(
        name = "Inventory",
        value = inventoryText,
        inline = False
    )

    # Future reference add a equipment showcase here

    await ctx.send(embed = embed)  

"""
* Fighting commands to make the fighting system work.
* Consists of .fight, .attack, .skill, .flee, and some extra functions to make them work
* Right now works on a command based system, however will rework this later on to make it based on reactions for less clutter in the chat
"""

# === Add a command to use a skill (Will work this into a emoji bassed command its just a temporary test function) ===

# === Command for the user to escape or flee from combat ===
@client.command()
@cooldown(1, 3, BucketType.user)
async def flee(ctx):
    print(f"The Flee command was called by", ctx.author.name)
    userID = str(ctx.author.id)
    character = db.getCharacter(userID)
    if not character:
        embed = discord.Embed(
            title = "You're not part of the guild",
            description = "Only members apart of SwordSong are able to hunt monsters.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    combatState = combatSystem.getCombatState(userID)
    if not combatState:
        embed = discord.Embed(
            title = "Not in combat!",
            description = "You're not fighting a monster right now, so you're not able to flee from one.",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)
        return
    
    # Gets a random number between 1-100 if its 70 or less the flee attampt is successfull
    if random.randint(1, 100) <= 70:
        embed = discord.Embed(
            title = "💨 Succsessful Escape!",
            description = "You successfully escaped from the monster!",
            color = discord.Color.green()
        )
        combatSystem.endCombat(userID)
    else:
        embed = discord.Embed(
            title = "❌ You Failed to Escape!",
            description = "You couldn't escape! The monster caught up to you while you were running away!",
            color = discord.Color.dark_red()
        )
        await ctx.send(embed = embed)

        # The monster gets a free attack
        await asyncio.sleep(1)
        await processMonsterTurnAsync(ctx, userID)
        return
    
    await ctx.send(embed = embed)

"""
Admins commands.
* These are purely testing commands for now to test the other function
* Consists if .rest, and .resetdata
* Will most likely make this into actual commands with some tweaks later on
"""

# === Resting command to let the user heal back up ===
@client.command()
@cooldown(1, 300, BucketType.user)
async def rest(ctx):
    print(f"Rest command was called by", ctx.author.name)
    userID = str(ctx.author.id)
    character = db.getCharacter(userID)
    if not character:
        embed = discord.Embed(
            title = "You're not part of the guild",
            description = "You're not part of SwordSong, so you're not allowed in the camp to heal yourself",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return

    currentHealth = character["health"]
    maxHealth = character["maxHealth"]
    ticks = 10
    percentPerTick = 10

    if currentHealth >= maxHealth:
        embed = discord.Embed(
            title = "Already at full health!",
            description = "You're already at full health so don't worry about healing up!",
            color = discord.Color.green()
        )
        await ctx.send(embed = embed)
        return
    
    embed = discord.Embed(
        title = "🔥 Resting back up at the campfire 🔥",
        description = "Eat some smore's at the campfire and rest backup to go back hunting.",
        color = discord.Color.dark_orange()
    )

    embed.add_field(
        name = "Health",
        value = f"❤️ {currentHealth}/{maxHealth}"
    )

    message = await ctx.send(embed = embed)

    for i in range(ticks):
        healAmount = math.ceil(maxHealth * (percentPerTick / 100))
        newHealth = min(currentHealth + healAmount, maxHealth)
        db.updateCharacter(userID, {"health": newHealth})
        currentHealth = newHealth

        embed.set_field_at(
            0,
            name = "Health",
            value = f"❤️ {currentHealth}/{maxHealth}",
            inline = True
        )

        embed.set_footer(
            text = f"Tick {i + 1}/{ticks}"
        )
        await message.edit(embed = embed)

        if newHealth >= maxHealth:
            break

        await asyncio.sleep(1)
    
    embed.title = "🔥 Resting complete! 🔥"
    embed.description = "You had enough smore's for now get back to fighting!"
    embed.set_footer(text = None)
    await message.edit(embed = embed)

# === Resets your character data (might make this into an actual command to reset progress) ===
@client.command()
@cooldown(1, 15, BucketType.user)
async def resetdata(ctx):
    print("Character reset command was called by", ctx.author.name)
    userID = str(ctx.author.id)
    if not db.getCharacter(userID):
        embed = discord.Embed(
            title = "You're not part of the guild.",
            description = "You're not part of SwordSong, so you're not able to leave the guild.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    embed = discord.Embed(
        title = "Character Reset",
        description = "Are you sure you want to leave the guild? This action cannot be undone.\nType 'yes' to confirm you want to leave.",
        color = discord.Color.orange()
    )
    await ctx.send(embed = embed)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    try:
        await client.wait_for('message', timeout = 30.0, check = check)
        if db.deleteCharacter(userID):
            embed = discord.Embed(
                title = "You left the guild.",
                description = "You succsessfully left the guild. If you wish to rejoin use '.start' to join SwordSong again.",
                color = discord.Color.green()
            )
            await ctx.send(embed = embed)
        else:
            embed = discord.Embed(
                title = "A problem arrised while trying to remove you from the guild.",
                description = "Please try to leave the guild again '.resetdata' if you really wish to leave.",
                color = discord.Color.orange()
            )
            await ctx.send(embed = embed)
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title = "Timeout",
            description = "You were thinking for a long time, if you really wish to continue please use '.resetdata' again.",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)

client.run(TOKEN)