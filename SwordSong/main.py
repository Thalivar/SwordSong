import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from dotenv import load_dotenv
from database import Database
from combadsys import combatSystem
from pathlib import Path
import random
import asyncio
import json
import os

# === Load the environment variables ===
load_dotenv()
TOKEN = os.getenv("DISCORDTOKEN")

if not TOKEN:
    print("Error: DISCORDTOKEN is not found in the .env file.")
    exit(1)

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

# === Setup the Bot ===
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=".", intents = intents, help_command = None, case_insensitive = True)
db = Database()
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

# === Fighting command to fight monsters ===
@client.command()
@cooldown(1, 5, BucketType.user)
async def fight(ctx):
    print(f"Fight command was called by {ctx.author.name}")
    userID = str(ctx.author.id)

    # Checks if the character exists in the database
    character = db.getCharacter(userID)
    if not character:
        embed = discord.Embed(
            title = "You're not part of the guild.",
            description = "You're not part of SwordSong, so you're not able to see your profile.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    # Checks if the player is already in combat
    if combatSystem.getCombatState(userID):
        embed = discord.Embed(
            title = "Already in combat!",
            description = "Watch out! You're already fighting a monster! Use `.attack`, `.skill`, `.flee`",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)
        return
    
    # checks if the player has enough health or needs to heal up
    if character["health"] <= 0:
        embed = discord.Embed(
            title = "You are too injured to fight right now!",
            description = "You're health is to low to fight. Rest or use healing potions before going on a hunt again.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    # Gets the area the character is in and the monsters is the area
    currentArea = character.get("currentArea", "forest")
    monster = combatSystem.spawnMonster(userID, currentArea)

    # Checks if there are huntable monsters in the area
    if not monster:
        embed = discord.Embed(
            title = "There were no monsters found!",
            description = "There are no monsters in this area right now. Please try again later.",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)
        return
    
    combatState = combatSystem.startCombat(userID, monster)
    embed= discord.Embed(
        title = "❗Watch out! You ran into a monster❗",
        description = f"A wild **{monster["name"]}** appears!\n\n{monster["description"]}",
        color = discord.Color.red()
    )

    embed.add_field(
        name = "Monster's stats",
        value = f"❤️ Health: {monster["currentHealth"]}/{monster["maxHealth"]}\n"
                f"⚔️ Attack: {monster["attack"]}\n"
                f"🛡️ Defense: {monster["defense"]}\n"
                f"🌟 Rarity: {monster["rarity"].title()}",
        inline = True
    )

    embed.add_field(
        name = f"{character["name"]}'s stats",
        value = f"❤️ Health: {character["health"]}/{character["maxHealth"]}\n"
                f"🔵 Mana: {character["mana"]}\n"
                f"⚔️ Attack: {character["attack"]}\n"
                f"🛡️ Defense: {character["defense"]}\n",
        inline = True
    )

    embed.add_field(
        name = "Actions",
        value = "`.attack` - A basic attack\n"
                "`.skill` - Use a skill\n"
                "`.flee` - Try to escape from the battle\n",
        inline = False
    )

    await ctx.send(embed = embed)
    
# === Performs a basic attack while the user is in combat ===
async def handleCombatVictory(ctx, userID, monster):
    rewards = combatSystem.distributeRewards(userID, monster)
    embed = discord.Embed(
        title = "Victory!",
        description = f"You defeated the {monster['name']} and earned {rewards['xp']} XP and {rewards['coins']} coins!",
        color = discord.Color.green()
    )
    if rewards.get("items"):
        loot = "\n".join([f"{item['quantity']}x {item['name']}" for item in rewards["items"]])
        embed.add_field(name="Loot", value=loot, inline=False)

    if rewards.get("levelUP"):
        embed.add_field(
            name = "Level Up!",
            value = f"You reached level {rewards['levelUP']['newLevel']}! Stats increased.",
            inline = False
        )
    await ctx.send(embed=embed)

# === Handles the monsters turn ===
async def processMonsterTurnAsync(ctx, userID):
    monsterResult = combatSystem.processMonsterTurn

    # Checks for any potential errors while processing the monster turn
    if "error" in monsterResult:
        embed = discord.Embed(
            title = "There was a combat error!",
            description = monsterResult["error"],
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return False
    
    embed = discord.Embed(
        title = "💥 Monster Attack!",
        desctiption = monsterResult["message"],
        color = discord.Color.red()
    )

    await ctx.send(embed = embed)

    # Checks if the user was defeated and if true sends out a defeat message
    if monsterResult.get("playerDefeated"):
        embed = discord.Embed(
            title = "💀 Defeat!",
            description = "You were defeated by the monster! You should get some rest and recover before going back.",
            color = discord.Color.dark_red()
        )
        await ctx.send(embed = embed)
        combatSystem.endCombat(userID)
        return False
    return True

@client.command()
@cooldown(1, 3, BucketType.user)
async def attack(ctx):
    print(f"Attack command was called by {ctx.author.id}")
    userID = str(ctx.author.id)

    # Checks if the character is in the database
    character = db.getCharacter(userID)
    if not character:
        embed = discord.Embed(
            title = "You're not part of the guild.",
            description = "You're not part of SwordSong, so you're not able to see your profile.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    # Checks if the character is in combat
    combatState = combatSystem.getCombatState(userID)
    if not combatState:
        embed = discord.Embed(
            title = "Not in combat!",
            description = "You're not fighting anyone right now. Use `.fight` to start hunting monsters.",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)
        return
    
    # Checks if its the users turn
    if combatState["turn"] != "player":
        embed = discord.Embed(
            title = "Not your turn!",
            description = "Wait for the monster to finish it's turn before you can attack.",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)
        return
    
    result = combatSystem.processPlayerAttack(userID)

    # If there is any error during the attack stops it
    if "error" in result:
        embed = discord.Embed(
            title = "Your attack failed!",
            description = result["error"],
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    embed = discord.Embed(
        title = "⚔️ Attack!",
        description = result["message"],
        color = discord.Color.blue()
    )

    monster = combatState["monster"]
    embed.add_field(
        name = "Monster's Health",
        value = f"❤️ {monster["currentHealth"]}/{monster["maxHealth"]}",
        inline = True
    )

    await ctx.send(embed = embed)

    # Checks if the monster died and if so handles the fight vicotry
    if result.get("monsterDefeated"):
        await handleCombatVictory(ctx, userID, monster)
        return
    
    await asyncio.sleep(2) # <= purely a wait for dramatic effect
    await combatSystem.processMonsterTurn(ctx, userID) # If monster didn't die go to the monsters turn

# === Add a command to use a skill (Will work this into a emoji bassed command its just a temporary test function) ===
@client.command
@cooldown(1, 3, BucketType.user)
async def skill(ctx, *, skillName = None):
    print(f"Skill command was called by {ctx.author.name}")
    userID = str(ctx.author.id)
    character = db.getCharacter(userID)
    if not character:
        embed = discord.Embed(
            title = "You're not part of the guild.",
            description = "You're not part of SwordSong, so you're not allowed to use skills.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)
        return
    
    combatState = combatSystem.getCombatState(userID)
    if not combatState:
        embed = discord.Embed(
            title = "You're not in combat!",
            description = "You're not allowed to use skills outside combat. Use `.fight` to start hunting monster.",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)
        return
    
    if combatState["turn"] != "player":
        embed = discord.Embed(
            title = "It's not your turn!",
            description = "Focus on dodging the monsters attack before casting a spell!",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)
        return
    
    if not skillName:
        availableSkills = combatSystem.getAvailableSkills(userID)

        embed = discord.Embed(
            title = "Available Skills",
            description = "Please choose a skills to use:",
            color = discord.Color.dark_blue()
        )

        for skill in availableSkills:
            status = "✅ Ready" if skill["canUse"] else f"❌ Cooldown: {skill["cooldownRemaining"]} turn"

            embed.add_field(
                name = skill["name"],
                value = f"{skill["data"]["description"]}\n{status}",
                inline = True
            )

        embed.add_field(
            name = "Usage",
            value = "Use `.skill <Skill Name>` to cast a skill.",
            inline = False
        )
        await ctx.send(embed = embed)
        return

    result = combatState.processPlayerAttack(userID, skillName)

    if "error" in result:
        embed = discord.Embed(
            title = "Skill Failed!",
            description = result["error"],
            color = discord.color.red()
        )
        await ctx.send(embed = embed)
        return
    
    if result["action"] == "heal":
        embed = discord.Embed(
            title = "💚 Healing",
            description = result["message"],
            color = discord.Color.brand_green()
        )
    elif result["action"] == "defensiveStance":
        embed = discord.Embed(
            title = "🛡️ Defensive Stance",
            description = result["message"],
            color = discord.Color.dark_blue()
        )
    else:
        embed = discord.Embed(
            title = "⚡ Skill Attack!",
            descripton = result["message"],
            color = discord.Color.dark_magenta()
        )
    
    monster = combatState["monster"]
    if result.get("damage", 0) > 0:
        embed.add_field(
            name = "Monster's Health",
            value = f"❤️ {monster["currentHealth"]}/{monster["maxHealth"]}",
            inline = True
        )

    await ctx.send(embed = embed)

    if result.get("monsterDefeated"):
        await handleCombatVictory(ctx, userID, monster)
        combatSystem.endCombat(userID)
        return
    
    await asyncio.sleep(2)
    await processMonsterTurnAsync(ctx, userID)

# === Command for the user to escape or flee from combat ===
@client.command()
@cooldown(1, 3, BucketType.user)
async def flee(ctx):
    print(f"The Flee command was called by {ctx.author.id}")
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
    
    if random



# === Test commands to make sure things work correctly ===

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