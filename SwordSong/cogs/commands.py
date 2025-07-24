import discord
import asyncio
from discord.ext import commands

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.command(name = "help")
    async def help(self, ctx):
        print("Help command was called by:", ctx.author.name)
        embed = discord.Embed(
            name = "SwordSong's Help Scroll",
            description = "List of available commands.",
            color = discord.Color.random()
        )
        embed.add_field(name = ".start", value = "Start your adventure for the guild SwordSong in Azefarnia", inline = False)
        embed.add_field(name = ".profile", value = "View your character's profile", inline = False)
        embed.add_field(name = ".inventory", value = "View all the wares you currently have in your inventory", inline = False)
        embed.add_field(name = ".shop", value = "WIP View all the items that are available for purchase", inline = False)
        embed.add_field(name = ".buy <item>", value = "WIP But the desired items from the shop", inline = False)
        embed.add_field(name = ".sell <item>", value = "WIP Sell an item from your inventory to the shop", inline = False)
        embed.add_field(name = ".equip <item>", value = "WIP Equip a weapon or armor from your inventory", inline = False)
        embed.add_field(name = ".unequip <item>", value = "WIP unequip a weapon or armor that you're currently wearing", inline = False)
        embed.add_field(name = ".travel", value = "WIP Travel between the regions of Azefarnia and find new monsters and people", inline = False)
        embed.add_field(name = ".map", value = "WIP view the map of Azefarnia!", inline = False)
        embed.add_field(name = ".fight", value = "Go on an adventure to hunt monsters and earn loot", inline = False)
        embed.add_field(name = ".leaveguild", value = "If you ever desire to leave SwordSong", inline = False)
        await ctx.send(embed = embed)

    @commands.command(name = "start")
    async def start(self, ctx):
        print("Start command was called by", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        if character:
            embed = discord.Embed(
                title = f"You're already part of the guild {character["name"]}!",
                description = "You're already in the guild, go out and hunt monsters and make yourself useful!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        embed = discord.Embed(
            title = "Welcome to SwordSong!",
            description = "Welcome to SwordSong! What would you like to be known by?",
            color = discord.Color.orange()
        )
        await ctx.send(embed = embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for("message", check = check, timeout = 30.0)
            if self.db.createCharacter(userID, msg.content):
                defaultArea = "forest"
                embed = discord.Embed(
                    title = "Welcome to SwordSong!",
                    description = f"Welcome, {msg.content}! Your adventure across Azefarnia begins now.",
                    color = discord.Color.green()
                )
                await ctx.send(embed = embed)
            else:
                embed = discord.Embed(
                    title = "Sorry traveler!",
                    description = "Apologies traveler, there was an issue while trying to enlist you. Please try again later.",
                    color = discord.Color.dark_red()
                )
                await ctx.send(embed = embed)
                return
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title = "Timeout",
                description = "You took to long to tell us your name. Please try again once you thought of a name.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)

    @commands.command(name = "profile")
    async def profile(self, ctx):
        print("Profile command was called by", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild.",
                description = "You're not part of SwordSong, so you're not able to view the guilds profile system.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        embed = discord.Embed(
            title = f"{character["name"]}'s Profile",
            color = discord.Color.blue()
        )

        embed.add_field(name = "Level", value = character["level"], inline = True)
        embed.add_field(name = "XP", value = f"{character["xp"]}/{character['xpToLevel']}", inline = True)
        embed.add_field(name = "Area", value = character.get("currentArea", "forest").capitalize(), inline = True)
        embed.add_field(name = "Health", value = f"{character["health"]}/{character["maxHealth"]}", inline = True)
        embed.add_field(name = "Attack", value = character["attack"], inline = True)
        embed.add_field(name = "Defense", value = character["defense"], inline = True)
        embed.add_field(name = "Coins", value = character["coins"], inline = True)
        await ctx.send(embed = embed)

    @commands.command(name = "inventory")
    async def inventory(self, ctx):
        print("inventory command was called by", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        items = self.db.getInventory(userID)
        if not character:
            embed = discord.Embed(
                name = "You're not part of the guild",
                description = "You're not part of SwordSong, so you don't have the guild's magic backpack.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if items:
            inventoryText = "\n".join([f"{name}: {qty}" for name, qty in items])
        else:
            inventoryText = "Empty"
        
        embed = discord.Embed(
            title = f"{character["name"]}'s Inventory",
            color = discord.Color.blue()
        )
        embed.add_field(
            name = "Items",
            value = inventoryText,
            inline = False
        )
        
        # Add section equipment here

        await ctx.send(embed = embed)
    
    @commands.command(name = "leaveguild")
    async def leaveguild(self, ctx):
        print("Character reset command was called by", ctx.author.name)
        userID = str(ctx.author.id)
        if not self.db.getCharacter(userID):
            embed = discord.Embed(
                title = "You're already not part of the guild!",
                description = "You're not part of SwordSong, so you're not able to leave the guild.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        embed = discord.Embed(
            title = "Are you sure you want to leave the guild?",
            description = "This action cannot be undone. Type `yes` to confirm that you want to leave SwordSong.",
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"
        
        try:
            await self.bot.wait_for("message", check = check, timeout = 30.0)
            if self.db.deleteCharacter(userID):
                embed = discord.Embed(
                    title = "You left the guild.",
                    description = "You successfully left SwordSong. If you wish to rejoin in the future, use `.start` to join again.",
                    color = discord.Color.green()
                )
                await ctx.send(embed = embed)
            else:
                embed = discord.Embed(
                    name = "A problem arose while you were thinking.",
                    description = "If you insist on leaving SwordSong, please try again with `.leaveguild`.",
                    color = discord.Color.orange()
                )
                await ctx.send(embed = embed)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title = "Timeout",
                description = "You were thinking for too long. If you really insist on leaving, please use `/leaveguild` again.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))