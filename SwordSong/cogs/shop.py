import discord
import asyncio
from discord.ext import commands

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.shopItem = bot.shopItems

    @commands.command(name = "shop")
    async def shop(self, ctx):
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
    
    @commands.command(name = "buy")
    async def buy(self, ctx, *, itemName: str):
        print("Buy command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        shopItems = self.shopitem
        if not character:
            embed = discord.Embed(
                title = "You're not in the guild.",
                description = "You're not in SwordSong, so you wont have acces to guild only equipment.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        item = next((item for item in shopItems if item["name"].lower() == itemName.lower(), none))

        if not item:
            embed = discord.Embed(
                title = f"We don't have {item} in the store!",
                description = "We unfortunatly don't sell that item here in the story.",
                color = discord.Color.orange()
            )
            await ctx.send(embed = embed)
            return
        if character["coints"] < item["buyPrice"]:
            embed = discord.Embed(
                title = "You don't have enough coins on you!",
                description = f"You don't have enough coins with you to buy that items, it costs {item["buyPrice"]} and you only have {character["coints"]}!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        inventory = character["inventory"]
        inventory[item["name"]] = inventory.get(item["name"], 0) + 1
        update = {
            "inventory": inventory,
            "coins": character["coins"] - item["buyPrice"]
        }
        self.db.updateCharacter(userID, update)
        embed = discord.Embed(
            title = "Thank you for your purchase!",
            description = f"You bought {item["name"]} for {item["buyPrice"]} coins! Thank you for your purchase and have a nice rest of your day.",
            color = discord.color.green()
        )
        await ctx.send(embed = embed)

    @commands.command(name = "sell")
    async def sell(self, ctx, *, itemName: str):
        print("Sell command was called by:" ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        shopItems = self.shopitem
        inventory = character["inventory"]
        if not character:
            embed = discord.Embed(
                title = "You're not in the guild!",
                description = "You're not in SwordSong, so you're not allowed to be in the guild store sell things.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if itemName not in inventory or inventory["itemName"] <= 0:
            embed = discord.Embed(
                title = "You can't sell that!",
                description = "You don't own that item so you're not able to sell it! Use `.inventory` to see all the things you can sell.",
                color = discord.Color.orange()
            )
            await ctx.send(embed = embed)
            return
        
        item = next((item for item in shopItems if item["name"].lower() == itemName.lower()), None)
        if not item:
            embed = discord.Embed(
                title = "That item cant be sold!",
                description = "Unfortunatly that item can't be sold here.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        sellPrice = item["buyPrice"] // 2
        inventory["itemName"] -= 1

        if inventory["itemName"] <= 0:
            del inventory["itemName"]

        update = {
            "inventory": inventory,
            "coins": character["coins"] + sellPrice
        }
        self.db.updateCharacter(userID, update)
        
        embed = discord.Embed(
            name = ""
        )

        

async def setup(bot):
    await bot.add_cog(ShopCog(bot))