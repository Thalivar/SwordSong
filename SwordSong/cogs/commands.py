import discord
import asyncio
from discord.ext import commands
from view.commandsView import HelpView, StartView, ProfileView, InventoryView, LeaveGuildView

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.command(name = "help")
    async def help(self, ctx):
        print("Help command was called by:", ctx.author.name)
        
        embed = discord.Embed(
            title = "📜 SwordSong's Help Scroll 📜",
            description = "Welcome To SwordSong! Choose a category to view commands:",
            color = discord.Color.gold()
        )
        embed.add_field(
            name = "Getting started",
            value = "Use `.start` to being your adventure in Azefarnia!",
            inline = False
        )
        embed.set_footer(text = "Click the buttons below to explore different command categories")

        view = HelpView(self.bot)
        message = await ctx.send(embed = embed, view = view)
        view.message = message

    @commands.command(name = "start")
    async def start(self, ctx):
        print("Start command was called by", ctx.author.name)
        
        embed = discord.Embed(
            title = "Welcome to SwordSong!",
            description = "Join the guild SwordSong and start your adventure across the mystical land of Azefarnia!",
            color = discord.Color.gold()
        )
        embed.add_field(
            name = "What awaits you:",
            value = "🗡️ Epic battles with monsters\n"
                    "💰 Treasures and rewards\n"
                    "🌍 Vast lands and secrets to explore",
            inline = False
        )
        embed.set_footer(text = "Click the button below to join the guild!")
        view = StartView(self.bot)
        await ctx.send(embed = embed, view = view)

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

        embed.add_field(name = "📈 Level", value = character["level"], inline = True)
        embed.add_field(name = "✨ XP", value = f"{character['xp']}/{character['xpToLevel']}", inline = True)
        embed.add_field(name = "🌲 Area", value = character.get("currentArea", "forest").capitalize(), inline = True)

        embed.add_field(name = "❤️ Health", value = f"{character['health']}/{character['maxHealth']}", inline = True)
        embed.add_field(name = "⚔️ Attack", value = character["attack"], inline = True)
        embed.add_field(name = "🛡️ Defense", value = character["defense"], inline = True)

        embed.add_field(name = "💰 Coins", value = f"{character['coins']} coins", inline = True)
        embed.add_field(name = "🔮 Mana", value = f"{character.get('mana', 50)}/{character.get('maxMana', 50)}", inline = True)
        embed.add_field(name = "\u200b", value = "\u200b", inline = True)

        view = ProfileView(self.bot, character)
        message = await ctx.send(embed = embed, view = view)
        view.message = message

    @commands.command(name = "inventory")
    async def inventory(self, ctx):
        print("inventory command was called by", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild",
                description = "You're not part of SwordSong, so you don't have the guild's magic backpack.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        equipment = self.db.getEquipment(userID)
        items = self.db.getInventory(userID)
        equipText = "\n".join([f"{slot.title()}: {item or 'Empty'}" for slot, item in equipment.items()])
        embed = discord.Embed(
            title = f"{character['name']}'s Inventory",
            color = discord.Color.blue()
        )
        embed.add_field(
            name = "🛡️ Equipment 🛡️",
            value = equipText or "No Equipment",
            inline = False
        )

        if items:
            itemsList = [f"{name}: {qty}" for name, qty in items]
            if len(itemsList) > 10:
                mid = len(itemsList) // 2
                firstHalf = "\n".join(itemsList[:mid])
                secondHalf = "\n".join(itemsList[mid:])

                embed.add_field(
                    name = "🎒 Items ",
                    value = firstHalf,
                    inline = True
                )
                embed.add_field(
                    name = " Items 🎒",
                    value = secondHalf,
                    inline = True
                )
            else:
                embed.add_field(
                    name = "🎒 Items 🎒",
                    value = "\n".join(itemsList),
                    inline = True
                )
        
            embed.add_field(
                name = "💰 Coins 💰",
                value = f"{character['coins']} coins",
                inline = True
            )
        else:
            embed.add_field(
                name = "🎒 Items 🎒",
                value = "Empty",
                inline = True
            )
            embed.add_field(
                name = "💰 Coins 💰",
                value = f"{character['coins']} coins",
                inline = True
            )

        embed.set_footer(text = f"Current Area: {character.get('currentArea', 'forest').capitalize()}")
        view = InventoryView(self.bot, character)
        message = await ctx.send(embed = embed, view = view)
        view.message = message
    
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
            title = "⚠️ Are you sure you want to leave the guild? ⚠️",
            description = "This action **cannot be undone**. You will lose all your progress, items, and character data.",
            color = discord.Color.red()
        )
        embed.add_field(
            name = "What you'll lose:",
            value = "- Your character data and all stats\n"
                    "- All items and equipment\n"
                    "- All coins and progress",
            inline = False
        )
        embed.set_footer(text = "Think carefully before making this decision!")

        view = LeaveGuildView(self.bot)
        await ctx.send(embed = embed, view = view)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))