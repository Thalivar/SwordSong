import discord
from discord.ext import commands
from services.dungeon.miniTest import MiniDungeon
from services.dungeon.randomProvider import StandardRandomProvider
from view.dungeonView import DungeonView, dungeonView

class DungeonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.activeDungeon = {}

    @commands.command(name = "dungeon")
    async def dungeonCommand(self, ctx):
        print("Dungeon command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild!",
                description = "You're not part of SwordSong, it's to dangerous for you to explore dungeons.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if userID in self.activeDungeon:
            embed = discord.Embed(
                title = "🪨 Already in a Dungeon! 🪨",
                description = "You're already exploring a dungeon! Finish that one before you start exploring a new one.",
                color = discord.Color.orange()
            )
            await ctx.send(embed = embed)
            return
        
        if character["health"] < 10:
            embed = discord.Embed(
                title = "💔 Too Injured 💔",
                description = "YOu need at least more than 10 health points to enter a dungeon safely. Please rest up first!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        try:
            view = dungeonView(self.bot, userID)
            embed = view.createDungeonEmbed()
            embed.set_footer(text = "💡 Use the buttons below to navigate and interact!")

            message = await ctx.send(embed = embed, view = view)
            view.message = message
            self.activeDungeon[userID] = view
            view.addToActionLog("You entered the dungeon!")
            updatedEmbed = view.createDungeonEmbed()
            updatedEmbed.set_footer(text = "💡 Use the buttons below to navigate and interact!")
            await message.edit(embed = updatedEmbed, view = view)
        except Exception as e:
            embed = discord.Embed(
                title = "❌ Dungeon Generation Failed! ❌",
                description = "Something went wrong while creating your dungeon. Please try again later.",
                color = discord.Color.dark_red()
            )
            await ctx.send(embed = embed)
            print(f"Dungeon generation error: {e}")
    
    @commands.command(name = "dungeoninfo")
    async def dungeonInfo(self, ctx):
        print("Dungeon Info command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild!",
                description = "You're not part of SwordSong, so you're not allowed to look at info about dungeons",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        embed = discord.Embed(
            title = "🪨 Dungeon Guide 🪨",
            description = "Learn about the different types of rooms you might encounter!",
            color = discord.Color.blue()
        )

        roomInfo = [
            ("🚪 **Entrance**", "A safe starting point"),
            ("⚔️ **Combat Room**", "This room contains monsters, so watch out!"),
            ("💰 **Treasure Room", "A room that os full with gold and valuable items"),
            ("🕳️ **Trap Room**", "Watch out for the dangerous traps in this room!"),
            ("👑 **Boss Room**", "A powerful boss resides in this room. Stay on your toes in here"),
            ("🏪 **Shop Room**", "A room that a mysterious merchant claimed for himself. No'one knows where he comes from."),
            ("💚 **Healing Room**", "A room with a magical spring in the middle, that is capable of making adventures feel rejuvinated"),
            ("🧩 **Puzzle Room**", "Solve one of the ancient riddles for rewards"),
            ("⬜ **Empty Room**", "Nothing interesting here besides some cobwebs and empty barrels")
        ]

        for title, desciption in roomInfo:
            embed.add_field(name = title, value = desciption, inline = False)
        
        embed.add_field(
            name = "🧭 Navigation 🧭",
            value = "Use the directional buttons to move around the dungeon.\n"
                    "The 👤 character shows your current position on the map.\n"
                    "the ⬛ charactert will represent unvisited rooms, while the others will show visited rooms.",
            inline = False
        )
        embed.add_field(
            name = "💡 Tips 💡",
            value = "• Always make sure you have enough health before you enter, or atleast have healing potions on you!\n"
                    "• Healing rooms are able to restore your health. Altough, don't rely on them to much.\n"
                    "• The combat rooms may require you to use `.hunt` commands.\n"
                    "• You are able to leave the dungeon at any time if it gets to dangerous for you.",
            inline = False
        )
        await ctx.send(embed = embed)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.component:
            userID = str(interaction.user.id)
            if userID in self.activeDungeon:
                view = self.activeDungeon[userID]
                if view.is_finished():
                    del self.activeDungeon[userID]

async def setup(bot):
    await bot.add_cog(DungeonCog(bot))