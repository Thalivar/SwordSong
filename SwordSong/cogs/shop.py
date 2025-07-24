import discord
import asyncio
from discord.ext import commands

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.shopItem = bot.shopItems

    @commands.command(name = "shop")
    async def shop(self ,ctx):
        print("Shop command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        items = self.shopitem
        itemsPerPage = 6
        pages = []
        if not character:
            embed = discord.Embed(
                title =  "You're not part of the guild!",
                description = "You're not part of SwordSong, so you're not able to acces the guild only store.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        for i in range(0, len(items), itemsPerPage):
            embed = discord.Embed(name = "Guild's Shop", color = discord.Color.gold())
            pageItems = items[i : i + itemsPerPage]
            for item in pageItems:
                embed.add_field(
                    name = f"{item["name"]} - {item["buyPrice"]} coins",
                    value = f"Type: {item["type"]}\nEffect: {item["effect"]}\n{item["description"]}",
                    inline = False
                )
            pages.append(embed)
        
        currentPage = 0
        msg = await ctx.send(embed = pages[currentPage])

        if len(pages) > 1:
            await msg.add_reaction("⬅️")
            await msg.add_reaction("➡️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]
            
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout = 60.0, check = check)
                    if str(reaction.emoji) == "➡️":
                        currentPage = (currentPage + 1) % len(pages)
                    if str(reaction.emoji) == "⬅️":
                        currentPage = (currentPage - 1) % len(pages)
                    
                    await msg.edit(embed = pages[currentPage])
                    await msg.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    break

async def setup(bot):
    await bot.add_cog(ShopCog(bot))