import discord
import asyncio
import math
from discord.ext import commands
from view.shopView import ShopView

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.shopItems = bot.shopItems
        self.areas = bot.areas

    @commands.command(name="shop")
    async def shop(self, ctx, page: int = 1):
        print("Shop command was called by:", ctx.author)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        
        if not character:
            embed = discord.Embed(
                title = "You're not in the guild!",
                description = "You're not in SwordSong! So you can't use the guild shop",
                color = discord.Color.red()
            )
            return await ctx.send(embed = embed)
        
        view = ShopView(self.bot, userID, page)
        embed = view.createEmbed()
        await ctx.send(embed = embed, view = view)
    
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
                description = f"You don't have enough coins with you to buy that items, it costs {item['buyPrice']} and you only have {character['coins']}!",
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
        inventoryDict = dict(inventory) if inventory else {}

        if not character:
            embed = discord.Embed(
                title = "You're not in the guild!",
                description = "You're not in SwordSong, so you're not allowed to be in the guild store sell things.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
    
        actualItemName = None
        for invItem, quantity in inventoryDict.items():
            if invItem.lower() == itemName.lower():
                actualItemName = invItem
                break

        if not actualItemName:
            embed = discord.Embed(
                title = "You don't have that item!",
                description = f"You don't have `{itemName}` in your inventory.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return

        item = None
        for shopItem in shopItems:
            if shopItem["name"].lower() == actualItemName.lower():
                item = shopItem
                break
        
        if not item:
            for area in self.areas.values():
                for monster in area["monsters"]:
                    loot = monster["lootTable"].get(actualItemName)
                    if loot:
                        item = {
                            "name": actualItemName,
                            "sellPrice": loot["sellPrice"],
                            "desciption": loot["description"]
                        }
                        break
                if item:
                    break

        if not item:
            embed = discord.Embed(
                title = "That item can't be sold!",
                description = f"Unfortunately '{itemName}' can't be sold here. Only items from the shop can be sold back.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return

        sellPrice = item.get("sellPrice", 0)

        if sellPrice <= 0:
            embed = discord.Embed(
                title = "That item has no sell value!",
                description = f"'{itemName}' cannot be sold as it has no sell price set.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return

        removalSuccess = self.db.removeItem(userID, actualItemName, 1)
        if removalSuccess:
            newCoins = character["coins"] + sellPrice
            self.db.updateCharacter(userID, {"coins": newCoins})
    
            embed = discord.Embed(
                title = "Item sold!",
                description = f"You sold **{actualItemName}** for {sellPrice} coins!",
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