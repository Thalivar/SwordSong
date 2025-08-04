import discord
from discord.ext import commands
import asyncio
import math

class BuyItemModal(discord.ui.modal, title = "Buy Item"):
    def __init__(self, bot, userID, shopView):
        super().__init__()
        self.bot = bot
        self.userID = userID
        self.shopView = shopView
    
    itemName = discord.ui.TextInput(
        label = "Item Name",
        placeholder = "Enter the exact name of the item you want to buy...",
        min_length = 1,
        max_length= 100
    )

    async def on_submit(self, interaction: discord.Interaction):
        character = self.bot.db.getCharacter(self.userID)
        if not character:
            embed = discord.Embed(
                title = "You're not in the guild.",
                description = "You're not in SwordSong, so you won't have access to guild only equipment and items.",
                color = discord.Color.red()
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)
            return

        item = next((item for item in self.bot.shopItems if item["name"].lower() == self.itemName.value.lower()), None)
        if not item:
            embed = discord.Embed(
                title = f"We don't have {self.itemName.value} in the store!",
                description = "We unfortunately don't sell that item here in the shop.",
                color = discord.Color.orange()
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)
            return
        
        if character["coins"] < item["buyPrice"]:
            embed = discord.Embed(
                title = "You don't have enough coins!",
                description = f"You don't have enough coins to buy that item. It costs {item['buyPrice']} and you have {character['coins']} coins!",
                color = discord.Color.red()
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)
            return
        
        if self.bot.db.addItem(self.userID, item["name"], 1):
            newCoins = character["coins"] - item["buyPrice"]
            self.bot.db.updateCharacter(self.userID, {"coins": newCoins})

            embed = discord.Embed(
                title = "Thank you for your purchase!",
                description = f"You bought **{item['name']}** for {item['buyPrice']} coins!",
                color = discord.Color.green()
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)
            
            shopEmbed = self.shopView.createEmbed()
            await interaction.edit_original_response(embed = shopEmbed, view = self.shopView)
        else:
            embed = discord.Embed(
                title = "Your purchase failed!",
                description = "There was an error while processing your purchase. Please try again.",
                color = discord.Color.red()
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)


class ShopView(discord.ui.View):
    def __init__(self, bot, userID, page = 1):
        super().__init__(timeout = 120)
        self.bot = bot
        self.userID = userID
        self.page = page
        self.itemsPerPage = 6
        self.totalPages = math.ceil(len(bot.shopItems) / self.itemsPerPage)
        self.updateButtons()

    def updateButtons(self):
        prevButton = discord.utils.get(self.children, customID = "prevPage")
        if prevButton:
            prevButton.is_disabled = self.page <= 1
        
        nextButton = discord.utils.get(self.children, customID = "nextPage")
        if nextButton:
            nextButton.disabled = self.page >= self.totalPages
    
    def getCurrentItems(self):
        startIDX = (self.page - 1) * self.itemsPerPage
        endIDX = startIDX + self.itemsPerPage
        return self.bot.shopItems[startIDX:endIDX]
    
    def createEmbed(self):
        character = self.bot.db.getCharacter(self.userID)
        if not character:
            return discord.Embed(
                title = "You're not in the guild!",
                description = "You're not in SwordSong! So you can't use the guild's shop",
                color = discord.Color.red()
            )

        embed = discord.Embed(
            title = f"Guild Shop ({self.page}/{self.totalPages})",
            color = discord.Color.gold()
        )
        embed.add_field(
            name = "💰 Your Coins",
            value = f"{character['coins']} coins",
            inline = False
        )

        currentItems = self.getCurrentItems()
        for item in currentItems:
            name = item.get("name", "Unknown")
            price = item.get("butPrice", 0)
            itemType = item.get("type", "misc")
            desciption = item.get("description", "")
            embed.add_field(
                name = f"{name} - {price} coins",
                value = f"Type: {itemType}\n"
                        f"{desciption}",
                inline = False
            )
        
        return embed
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user.id):
            await interaction.response.send_message(
                "This shop interface is not for you!",
                ephemeral = True
            )
            return False
        return True

    @discord.ui.button(label = "◀ Previous", style = discord.ButtonStyle.secondary, custom_id = "prevPage")
    async def previousPage(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            self.updateButtons()
            embed = self.createEmbed()
            await interaction.response.edit_message(embed = embed, view = self)
    
    @discord.ui.button(label = "Next ▶", style = discord.ButtonStyle.primary, custom_id = "nextPage")
    async def nextPage(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.totalPages:
            self.page += 1
            self.updateButtons()
            embed = self.createEmbed()
            await interaction.response.edit_message(embed = embed, view = self)
    
    @discord.ui.button(label = "🛒 Buy Item", style = discord.ButtonStyle.primary)
    async def buyItem(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = buyItemModal(self.bot, self.userID, self)
        await interaction.response.send_modal(modal)