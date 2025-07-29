import discord
import asyncio
import math
from discord.ext import commands

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.shopItems = bot.shopItems

    @commands.command(name="shop")
    async def shop(self, ctx, page: int = 1):
        print("Shop command was called by:", ctx.author)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        items = self.shopItems
        perPage = 6
        total = len(items)
        pages = (total + perPage - 1) // perPage
        page  = max(1, min(page, pages))
        startIDX = (page - 1) * perPage
        chunk = items[startIDX : startIDX + perPage]

        if not character:      
            embed=discord.Embed(
                title = "Not in the guild!",
                description = "You're not in SwordSong! So you can't use the guild's shop",
                color = discord.Color.red()
            )
            return await ctx.send(embed = embed)

        embed = discord.Embed(
            title = f"Guild Shop ({page}/{pages})",
            color = discord.Color.gold()
        )
        for item in chunk:
            name = item.get("name", "Unknown")
            price = item.get("buyPrice", 0)
            type = item.get("type", "misc")
            description = item.get("description", "")
            embed.add_field(
                name=f"{name} — {price} coins",
                value=f"type: {type}\n{description}",
                inline=False
            )

        msg = await ctx.send(embed=embed)
        if pages > 1:
            await msg.add_reaction("⬅️")
            await msg.add_reaction("➡️")

            def check(r, u):
                return (
                    u == ctx.author and
                    r.message.id == msg.id and
                    str(r.emoji) in ("⬅️", "➡️")
                )

            current   = page - 1
            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=60, check=check
                    )
                    current   = (current   + (1 if str(reaction.emoji)=="➡️" else -1)) % pages
                    newEmbed = discord.Embed(
                        title=f"Guild Shop ({current + 1}/{pages})",
                        color=discord.Color.gold()
                    )
                    for item in items[current * perPage : current * perPage + perPage]:
                        name = item.get("name", "Unknown")
                        price = item.get("buyPrice", 0)
                        type = item.get("type", "misc")
                        effect = item.get("effect", {})
                        description = item.get("description", "")
                        newEmbed.add_field(
                            name = f"{name} — {price} coins",
                            value = f"type: {type}\n{description}",
                            inline = False
                        )
                    await msg.edit(embed = newEmbed)
                    await msg.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    break
    
    @commands.command(name = "buy")
    async def buy(self, ctx, *, itemName: str):
        print("Buy command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        shopItems = self.shopItems
        if not character:
            embed = discord.Embed(
                title = "You're not in the guild.",
                description = "You're not in SwordSong, so you wont have acces to guild only equipment.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        item = next((item for item in shopItems if item["name"].lower() == itemName.lower()), None)

        if not item:
            embed = discord.Embed(
                title = f"We don't have {itemName} in the store!",
                description = "We unfortunatly don't sell that item here in the story.",
                color = discord.Color.orange()
            )
            await ctx.send(embed = embed)
            return
        if character["coins"] < item["buyPrice"]:
            embed = discord.Embed(
                title = "You don't have enough coins on you!",
                description = f"You don't have enough coins with you to buy that items, it costs {item["buyPrice"]} and you only have {character["coins"]}!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if self.db.addItem(userID, item["name"], 1):
            newCoins = character["coins"] - item["buyPrice"]
            self.db.updateCharacter(userID, {"coins": newCoins})

            embed = discord.Embed(
                title = "Thank you for your purchase!",
                description = f"You bought {item['name']} for {item['buyPrice']} coins!",
                color = discord.Color.green()
            )
            await ctx.send(embed = embed)
        else:
            embed = discord.Embed(
                title = "Your purchase failed!",
                description = "There was an error while we were processing your purchase. Please try again.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)

    @commands.command(name = "sell")
    async def sell(self, ctx, *, itemName: str):
        print("Sell command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        shopItems = self.shopItems
        inventory = self.db.getInventory(userID)
        inventoryDict = dict(inventory)

        if not character:
            embed = discord.Embed(
                title = "You're not in the guild!",
                description = "You're not in SwordSong, so you're not allowed to be in the guild store sell things.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if itemName not in inventoryDict or inventoryDict.get(itemName, 0) <= 0:
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
                title = "That item can't be sold!",
                description = "Unfortunately that item can't be sold here.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
    
        sellPrice = item.get("sellPrice", 0)
    
        if self.db.removeItem(userID, itemName, 1):
            newCoins = character["coins"] + sellPrice
            self.db.updateCharacter(userID, {"coins": newCoins})
        
            embed = discord.Embed(
                title = "Item sold!",
                description = f"You sold **{itemName}** for {sellPrice} coins!",
                color = discord.Color.green()
            )
            await ctx.send(embed = embed)
        else:
            embed = discord.Embed(
                title = "Sale failed!",
                description = "There was an error processing your sale. Please try again.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)


async def setup(bot):
    await bot.add_cog(ShopCog(bot))