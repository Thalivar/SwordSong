import discord
from discord.ext import commands
import asyncio

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout = 300)
        self.bot = bot

    @discord.ui.button(label = "Commands", style = discord.ButtonStyle.primary, emoji = "⚔️")
    async def showCommands(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "⚔️ Combat & Adventure Commands ⚔️",
            description = "Commands for fighting and exploring Azefarnia",
            color = discord.Color.red()
        )
        embed.add_field(name = ".fight", value = "Go on an adventure to hunt monsters and earn loot.", inline = False)
        embed.add_field(name = ".rest", value = "Rest at a nearby campfire to recover your health after a fight.", inline = False)
        embed.add_field(name = ".travel", value = "WIP Travel between the regions of Azefarnia", inline = False)
        embed.add_field(name = ".map", value = "WIP View the map of Azefarnia!", inline = False)

        await interaction.response.edit_message(embed = embed, view = self)
        
    @discord.ui.button(label = "Character", style = discord.ButtonStyle.secondary, emoji = "👤")
    async def showCharacter(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "👤 Character Commands 👤",
            description = "Commands for managing your character",
            color = discord.Color.blue()
        )
        embed.add_field(name = ".profile", value = "View your character's profile and stats", inline = False)
        embed.add_field(name = ".inventory", value = "View all items in your inventory", inline = False)
        embed.add_field(name = ".equip <item>", value = "WIP Equip a weapon or armor", inline = False)
        embed.add_field(name = ".unequip <item>", value = "WIP Unequip a weapon or armor", inline = False)

        await interaction.response.edit_message(embed = embed, view = self)
        
    @discord.ui.button(label = "Shop", style = discord.ButtonStyle.success, emoji = "🛒")
    async def showShop(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "🛒 Shop Commands 🛒",
            description = "Commands for buying and selling items",
            color = discord.Color.green()
        )
        embed.add_field(name = ".shop", value = "View all items that are available for purchase", inline = False)
        embed.add_field(name = ".buy <item>", value = "Buy the desired item from the shop", inline = False)
        embed.add_field(name = ".sell <item>", value = "sell an item from your inventory", inline = False)

        await interaction.response.edit_message(embed = embed, view = self)
        
    @discord.ui.button(label = "Guild", style = discord.ButtonStyle.danger, emoji = "🏛️")
    async def showGuild(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "🏛️ Guild Commands 🏛️",
            description = "Commands for joining and leaving SwordSong",
            color = discord.Color.purple()
        )
        embed.add_field(name = ".start", value = "Start your adventure and join SwordSong", inline = False)
        embed.add_field(name = ".leaveguild", value = "Leave SwordSong", inline = False)

        await interaction.response.edit_message(embed = embed, view = self)
        
    @discord.ui.button(label = "Back To Main", style = discord.ButtonStyle.gray, emoji = "🏠")
    async def backToMain(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "📜 SwordSong's Help Scroll 📜",
            description = "Welcome to SwordSong! Choose a category to view commands:",
            color = discord.Color.gold()
        )
        embed.add_field(
            name = "Getting Started",
            value = "Use `.start` to begin your adventure in Azefarnia!",
            inline = False
        )
        embed.set_footer(text = "Click the buttons below to explore different command categories")

        await interaction.response.edit_message(embed = embed, view = self)
    
    @discord.ui.button(label = "Close", style = discord.ButtonStyle.gray, emoji = "❌")
    async def closeHelp(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "Help Closed",
            description = "You put away the help scroll back into your backpack.\n"
                          "If you need help again open it with `.help`",
            color = discord.Color.gray()
        )
        await interaction.response.edit_message(embed = embed, view = None)
        
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class StartView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout = 300)
        self.bot = bot
    
    @discord.ui.button(label = "Join SwordSong", style = discord.ButtonStyle.success, emoji = "⚔️")
    async def joinGuild(self, interaction: discord.Interaction, button: discord.ui.Button):
        userID = str(interaction.user.id)

        if self.bot.db.getCharacter(userID):
            embed = discord.Embed(
                title = "You're already part of the guild!",
                description = "You're already a member of SwordSong. Use `.profile` to view your character stats.",
                color = discord.Color.orange()
            )
            await interaction.response.edit_message(embed = embed, view = None)
            return
        
        modal = NameInputModal(self.bot)
        await interaction.response.send_modal(modal)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class NameInputModal(discord.ui.Modal, title = "Join SwordSong"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    name = discord.ui.TextInput(
        label = "What would you like to be known by?",
        placeholder = "Enter your character's name ...",
        max_length = 50,
        min_length = 1
    )

    async def on_submit(self, interaction: discord.Interaction):
        userID = str(interaction.user.id)
        characterName = self.name.value.strip()

        try:
            if self.bot.db.createCharacter(userID, characterName):
                embed = discord.Embed(
                    title = "Welcome to SwordSong!",
                    description = f"Welcome, {characterName}! You adventure across Azefarnia begins now.",
                    color = discord.Color.green()
                )
                embed.add_field(
                    name = "Next Steps",
                    value = "Use `.profile` to view your stats\n"
                            "Use `.fight` to go on a adventure to battle monsters\n"
                            "Use `.help` for a scroll full with commands",
                    inline = False
                )
            else:
                embed = discord.Embed(
                    title = "Sorry Traveler!",
                    description = "There was an issue while trying to enlist you. Please try again later",
                    color = discord.Color.dark_red()
                )
        except Exception as e:
            print(f"Error creating character: {e}")
            embed = discord.Embed(
                    title = "Sorry Traveler!",
                    description = "There was an issue while trying to enlist you. Please try again later",
                    color = discord.Color.dark_red()
                )

        await interaction.response.send_message(embed = embed, ephemeral = True)

class ProfileView(discord.ui.View):
    def __init__(self, bot, character):
        super().__init__(timeout = 300)
        self.bot = bot
        self.character = character

    @discord.ui.button(label = "View Inventory", style = discord.ButtonStyle.secondary, emoji = "🎒")
    async def viewInventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        userID = str(interaction.user.id)
        inventoryView = InventoryView(self.bot, self.character)
        await inventoryView.showInventory(interaction)
    
    @discord.ui.button(label = "Refresh Stats", style = discord.ButtonStyle.primary, emoji = "🔄")
    async def refreshProfile(self, interaction: discord.Interaction, button: discord.ui.Button):
        userID = str(interaction.user.id)
        self.character = self.bot.db.getCharacter(userID)

        if not self.character:
            embed = discord.Embed(
                title = "Error",
                description = "We could not retrieve your character data.",
                color = discord.Color.red()
            )
            await interaction.response.edit_message(embed = embed, view = self)
            return
        
        embed = discord.Embed(
            title = f"{self.character['name']}'s Profile",
            color = discord.Color.blue()
        )
        embed.add_field(name = "📈 Level", value = self.character["level"], inline = True)
        embed.add_field(name = "✨ XP", value = f"{self.character['xp']}/{self.character['xpToLevel']}", inline = True)
        embed.add_field(name = "🌲 Area", value = self.character.get("currentArea", "forest").capitalize(), inline = True)

        embed.add_field(name = "❤️ Health", value = f"{self.character['health']}/{self.character['maxHealth']}", inline = True)
        embed.add_field(name = "⚔️ Attack", value = self.character["attack"], inline = True)
        embed.add_field(name = "🛡️ Defense", value = self.character["defense"], inline = True)

        embed.add_field(name = "💰 Coins", value = f"{self.character['coins']} coins", inline = True)
        embed.add_field(name = "🔮 Mana", value = f"{self.character.get('mana', 50)}/{self.character.get('maxMana', 50)}", inline = True)
        embed.add_field(name = "\u200b", value = "\u200b", inline = True) # <- Temp empty field for alignment

        await interaction.response.edit_message(embed = embed, view = self)
    
    @discord.ui.button(label = "Close", style = discord.ButtonStyle.gray, emoji = "❌")
    async def closeProfile(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "Profile Closed",
            description = "You stopped looking at your character profile.",
            color = discord.Color.gray()
        )
        await interaction.response.edit_message(embed = embed, view = None)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class InventoryView(discord.ui.View):
    def __init__(self, bot, character):
        super().__init__(timeout = 300)
        self.bot = bot
        self.character = character

    async def showInventory(self, interaction: discord.Interaction):
        userID = str(interaction.user.id)
        equipment = self.bot.db.getEquipment(userID)
        items = self.bot.db.getInventory(userID)

        embed = discord.Embed(
            title = f"{self.character['name']}'s Inventory",
            color = discord.Color.blue()
        )

        equipText = "\n".join([f"{slot.title()}: {item or 'Empty'}" for slot, item in equipment.items()])
        embed.add_field(
            name = "🛡️ Equipment 🛡️",
            value = equipText or "No Equipment",
            inline = False
        )

        if items:
            inventoryText = "\n".join([f"{name}: {qty}" for name, qty in items])
        else:
            inventoryText = "Empty"

        embed.add_field(
            name = "🎒 Items 🎒",
            value = inventoryText,
            inline = False
        )
        embed.add_field(
            name = "💰 Coins 💰",
            value = f"{self.character['coins']} coins",
            inline = False
        )

        embed.set_footer(text = f"Current Area: {self.character.get('currentArea', 'forest').capitalize()}")
        await interaction.response.edit_message(embed = embed, view = self)
    
    @discord.ui.button(label = "Back to Profile", style = discord.ButtonStyle.gray, emoji = "👤")
    async def backToProfile(self, interaction: discord.Interaction, button: discord.ui.Button):
        userID = str(interaction.user.id)
        self.character = self.bot.db.getCharacter(userID)
        profileView = ProfileView(self.bot, self.character)

        embed = discord.Embed(
            title = f"{self.character['name']}'s Profile",
            color = discord.Color.blue()
        )
        embed.add_field(name = "📈 Level", value = self.character["level"], inline = True)
        embed.add_field(name = "✨ XP", value = f"{self.character['xp']}/{self.character['xpToLevel']}", inline = True)
        embed.add_field(name = "🌲 Area", value = self.character.get("currentArea", "forest").capitalize(), inline = True)

        embed.add_field(name = "❤️ Health", value = f"{self.character['health']}/{self.character['maxHealth']}", inline = True)
        embed.add_field(name = "⚔️ Attack", value = self.character["attack"], inline = True)
        embed.add_field(name = "🛡️ Defense", value = self.character["defense"], inline = True)

        embed.add_field(name = "💰 Coins", value = f"{self.character['coins']} coins", inline = True)
        embed.add_field(name = "🔮 Mana", value = f"{self.character.get('mana', 50)}/{self.character.get('maxMana', 50)}", inline = True)
        embed.add_field(name = "\u200b", value = "\u200b", inline = True) # <- Temp empty field for alignment

        await interaction.response.edit_message(embed = embed, view = profileView)

    @discord.ui.button(label = "Refresh", style = discord.ButtonStyle.primary, emoji = "🔄")
    async def refreshInventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.showInventory(interaction)
    
    @discord.ui.button(label = "Close", style = discord.ButtonStyle.gray, emoji = "❌")
    async def closeInventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "Inventory Closed",
            description = "You stopped looking in your backpack.",
            color = discord.Color.gray()
        )
        await interaction.response.edit_message(embed = embed, view = None)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class LeaveGuildView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout = 300)
        self.bot = bot

    @discord.ui.button(label = "Yes, Leave Guild", style = discord.ButtonStyle.danger, emoji = "⚠️")
    async def confirmLeave(self, interaction: discord.Interaction, button: discord.ui.Button):
        userID = str(interaction.user.id)

        if self.bot.db.deleteCharacter(userID):
            embed = discord.Embed(
                title = "You left the guild.",
                description = "You successfully left SwordSong. If you wish to rejoin in the future, use `.start` to join again",
                color = discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title = "A problem arose while leaving.",
                description = "If you insist on leaving SwordSong, please try again with `.leaveguild`.",
                color = discord.Color.orange()
            )

        await interaction.response.edit_message(embed = embed, view = None)

    @discord.ui.button(label = "Cancel", style = discord.ButtonStyle.secondary, emoji = "❌")
    async def cancelLeave(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title = "Action Cancelled",
            description = "You decided to stay with SwordSong. We're all happy with that decision!",
            color = discord.Color.green()
        )
        await interaction.response.edit_message(embed = embed, view = None)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True