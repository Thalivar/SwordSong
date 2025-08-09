import discord
from discord.ext import commands
import asyncio
import random
from services.dungeon.miniTest import MiniDungeon
from services.dungeon.models import RoomType

class DungeonView(discord.ui.View):
    def __init__(self, bot, userID, dungeon: MiniDungeon, timeout = 180):
        super().__init__(timeout = timeout)
        self.bot = bot
        self.userID = userID
        self.dungeon = dungeon
        self.db = bot.db
        self.message = None
        self.actionLog = []

    async def interaction_check(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.userID:
            await interaction.response.send_message("This isn't your dungeon!", ephemeral = True)
            return False
        return True
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        try:
            embed = discord.Embed(
                title = "🪨 Dungeon Adventure Ended 🪨",
                description = "You got lost in the dungeon, so the rescue team found you and helped you escape the dungeon.",
                color = discord.Color.gray()
            )
            await self.message.edit(embed = embed, view = self)
        except:
            pass
    
    def addToActionLog(self, message: str):
        self.actionLog.append(f"• {message}")
        if len(self.actionLog) > 4:
            self.actionLog.pop(0)
    
    def createDungeonEmbed(self) -> discord.Embed:
        currentRoom = self.dungeon.currentRoom
        character = self.db.getCharacter(self.userID)

        embed = discord.Embed(
            title = "🪨 Dungeon Adventure 🪨",
            description = f"**Current Location:** {currentRoom.roomType.value.title()}\n"
                          f"**Position:** ({self.dungeon.playerPos.x}, {self.dungeon.playerPos.y})",
            color = discord.Color.dark_teal()
        )

        dungeonMap = self.dungeon.getASCII()
        embed.add_field(
            name = "🗺️ Dungeon Map 🗺️",
            value = f"```\n{dungeonMap}\n```",
            inline = False
        )

        roomDescriptions = {
            RoomType.ENTRANCE: "The entrance to the dungeon. You are able to rest safely here as there is no threat around.",
            RoomType.COMBAT: "Its a dangerous room that is filled with monsters!",
            RoomType.TREASURE: "A room that containes a lot of value treasures!",
            RoomType.TRAP: "Watch out! This room is full with deadly traps.",
            RoomType.BOSS: "This is the boss chamber. You better stay aware of your surroundings as the boss is hiding here somewhere.",
            RoomType.SHOP: "A mysterious merchant has set up shop here. Nobody knows why he's here.",
            RoomType.HEALING: "Its a peaceful room with water that seems to revitalize the people that drink it.",
            RoomType.PUZZLE: "These kind of rooms are full with ancient puzzles to solve.",
            RoomType.EMPTY: "It's a empty room. There seems to be nothing interesting here."
        }

        embed.add_field(
            name = "📍 Current Room 📍",
            value = roomDescriptions.get(currentRoom.roomType, "An unknow room..."),
            inline = False
        )
        embed.add_field(
            name = "👤 Your Stats 👤",
            value = f"❤️ Health: {character['health']}/{character['maxHealth']}\n"
                    f"⚔️ Attack: {character['attack']}\n"
                    f"🛡️ Defense: {character['defense']}\n"
                    f"💰 Coins: {character['coins']}.",
            inline = True
        )

        directions = []
        for direction, canMove in currentRoom.connections.items():
            if canMove:
                directions.append(f"➡️ {direction.title()}")
        
        if directions:
            embed.add_field(
                name = "🧭 Available Paths 🧭",
                value = "\n".join(directions),
                inline = True
            )

        if self.actionLog:
            embed.add_field(
                name = "📜 Recent Actions 📜",
                value = "\n".join(self.actionLog),
                inline = True
            )
        
        return embed

    @discord.ui.button(label = "North", style = discord.ButtonStyle.secondary, emoji = "⬆️", row = 0)
    async def northButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.movePlayer(interaction, "north")

    @discord.ui.button(label = "West", style = discord.ButtonStyle.secondary, emoji = "⬅️", row = 1)
    async def WestButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.movePlayer(interaction, "west")

    @discord.ui.button(label = "East", style = discord.ButtonStyle.secondary, emoji = "➡️", row = 1)
    async def eastButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.movePlayer(interaction, "east")

    @discord.ui.button(label = "South", style = discord.ButtonStyle.secondary, emoji = "⬇️", row = 2)
    async def southButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.movePlayer(interaction, "south")
    
    @discord.ui.button(label = "Interact", style = discord.ButtonStyle.primary, emoji = "🔍", row = 1)
    async def interactButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.interactWithRoom(interaction)
    
    @discord.ui.button(label = "Leave Dungeon", style = discord.ButtonStyle.danger, emoji = "🚪", row = 3)
    async def leaveButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.leaveDungeon(interaction)
    
    async def movePlayer(self, interaction: discord.Interaction, direction: str):
        await interaction.response.defer()

        currentRoom = self.dungeon.currentRoom
        if not currentRoom.connections.get(direction, False):
            embed = discord.Embed(
                title = "❌ Can't Move ❌",
                description = f"There's no path to the {direction}!",
                color = discord.Color.red()
            )
            await interaction.followup.send(embed = embed, ephemeral = True)
            return
        
        if self.dungeon.movePlayer(direction):
            newRoom = self.dungeon.currentRoom
            self.addToActionLog(f"Moved {direction} to a {newRoom.roomType.value} room.")
            embed = self.createDungeonEmbed()
            await interaction.edit_original_response(embed = embed, view = self)
        else:
            embed = discord.Embed(
                title = "❌ Movement Failed! ❌",
                description = "Something prevented you from moving in that direction.",
                color = discord.Color.red()
            )
            await interaction.followup.send(embed = embed, ephemeral = True)
    
    async def interactWithRoom(self, interaction: discord.Interaction):
        await interaction.response.defer()

        currentRoom = self.dungeon.currentRoom
        character = self.db.getCharacter(self.userID)

        if currentRoom.cleared:
            embed = discord.Embed(
                title = "💭 Nothin here 💭",
                description = "You've already explored this room! There was nothing new found.",
                color = discord.Color.light_grey()
            )
            await interaction.followup.send(embed = embed, ephemeral = True)
            return
        
        if currentRoom.roomType == RoomType.TREASURE:
            await self.handleTreasureRoom(interaction, currentRoom, character)
        elif currentRoom.roomType == RoomType.COMBAT:
            await self.handleCombatRoom(interaction, currentRoom, character)
        elif currentRoom.roomType == RoomType.TRAP:
            await self.handleTrapRoom(interaction, currentRoom, character)
        elif currentRoom.roomType == RoomType.HEALING:
            await self.handleHealingRoom(interaction, currentRoom, character)
        elif currentRoom.roomType == RoomType.SHOP:
            await self.handleShopRoom(interaction, currentRoom, character)
        elif currentRoom.roomType == RoomType.PUZZLE:
            await self.handlePuzzleRoom(interaction, currentRoom, character)
        elif currentRoom.roomType == RoomType.EMPTY:
            embed = discord.Embed(
                title = "💭 Empty Room 💭",
                description = "This room is completely empty. There is nothing to see here.",
                color = discord.Color.light_grey()
            )
            await interaction.followup.send(embed = embed, ephemeral = True)
        else:
            embed = discord.Embed(
                title = "❓ Unknown Room ❓",
                description = "You're not sure what to do in this room.",
                color = discord.Color.light_grey()
            )
            await interaction.followup.send(embed = embed, ephemeral = True)
    
    async def handleTreasureRoom(self, interaction: discord.Interaction, room, character):
        coinsFound = random.randint(20, 100)
        self.db.updateCharacter(self.userID, {"coins": character["coins"] + coinsFound})
        room.clear()
        self.addToActionLog(f"Found {coinsFound} coins in a treasure chest!")
        embed = discord.Embed(
            title = "💰 Treasure Found! 💰",
            description = f"You found a treasure chest containing {coinsFound} coins!",
            color = discord.Color.gold()
        )
        await interaction.followup.send(embed = embed, ephemeral = True)

        updatedEmbed = self.createDungeonEmbed()
        await interaction.edit_original_response(embed = updatedEmbed, view = self)
    
    async def handleCombatRoom(self, interaction: discord.Interaction, room, character):
        if hasattr(self.bot, "combatSystem") and self.bot.combatSystem.isInCombat(self.userID):
            embed = discord.Embed(
                title = "⚔️ Already in Combat! ⚔️",
                description = "You're already fighting a monster! Finish your current fight first before exploring a dungeon!",
                color = discord.Color.red()
            )
            await interaction.followup.send(embed = embed, ephemeral = True)
            return
        
        embed = discord.Embed(
            title = "⚔️ Monster Encounter! ⚔️",
            description = "Am onster blocks your path!",
            color = discord.Color.red()
        )
        await interaction.followup.send(embed = embed, ephemeral = True)

    async def handleTrapRoom(self, interaction: discord.Interaction, room, character):
        if random.randint(1, 100) <= 30:
            embed = discord.Embed(
                title = "🕳️ Trap Avoided! 🕳️",
                description = "You carefully navigated around the traps in this room.",
                color = discord.Color.green()
            )
            self.addToActionLog("You successfully avoided the traps!")
        else:
            damage = random.randint(5, 15)
            newHealth = max(1, character["health"] - damage)
            self.db.updateCharacter(self.userID, {"health": newHealth})
            self.addToActionLog(f"You triggered a trap! You lost {damage} health!")

            embed = discord.Embed(
                title = "🕳️ Trap Triggered! 🕳️",
                description = f"You triggered a trap and lost {damage} health!",
                color = discord.Color.red()
            )
        
        room.clear()
        await interaction.followup.send(embed = embed, ephemeral = True)
        updatedEmbed = self.createDungeonEmbed()
        await interaction.edit_original_response(embed = updatedEmbed, view = self)

    async def handleHealingRoom(self, interaction: discord.Interaction, room, character):
        healAmount = min(30, character["maxHealth"] - character["health"])
        if healAmount > 0:
            newHealth = character["health"] + healAmount
            self.db.updateCharacter(self.userID, {"health": newHealth})
            self.addToActionLog(f"You healed for {healAmount} health at the spring!")

            embed = discord.Embed(
                title = "💚 Healing Spring 💚",
                description = f"You drink from the magical spring and recover {healAmount} health!",
                color = discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title = "💚 Healing Spring 💚",
                description = "The spring's magic has no effect on you. You're already at full health!",
                color = discord.Color.light_grey()
            )
        
        room.clear()
        await interaction.followup.send(embed = embed, ephemeral = True)
        updatedEmbed = self.createDungeonEmbed()
        await interaction.edit_original_response(embed = updatedEmbed, view = self)

    async def handleShopRoom(self, interaction: discord.Interaction, room, character):
        embed = discord.Embed(
            title = "🏪 Mysterious Merchant 🏪",
            description = "A hooded figure offers to trade with you. Use `.shop` to see their wares.",
            color = discord.Color.blue()
        )
        await interaction.followup.send(embed = embed, ephemeral = True)
    
    async def handlePuzzleRoom(self, interaction: discord.Interactions, room, character):
        correctAnswer = random.randint(1, 3)
        userGuess = random.randint(1, 3)

        if userGuess == correctAnswer:
            reward = random.randint(10, 30)
            self.db.updateCharacter(self.userID, {"coins": character["coins"] + reward})
            self.addToActionLog(f"You solved the puzzle! You gained {reward} coins.")

            embed = discord.Embed(
                title = "🧩 Puzzle Solved! 🧩",
                description = f"You solved the ancient puzzle and received {reward} coins!",
                color = discord.Color.purple()
            )
        else:
            embed = discord.Embed(
                title = "🧩 Puzzle Failed 🧩",
                description = "You couldn't solve the puzzle this time. Maybe try again later.",
                color = discord.Color.orange()
            )
        
        room.clear()
        await interaction.followup.send(embed = embed, ephemeral = True)
        updatedEmbed = self.createDungeonEmbed()
        await interaction.edit_original_response(embed = updatedEmbed, view = self)
    
    async def leaveDungeon(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title = "🚪 You left the dungeon 🚪",
            description = "You decided it was safer to leave the dungeon than to continue exploring it.",
            color = discord.Color.green()
        )

        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed = embed, view = self)
        self.stop()

def dungeonView(bot, userID: str) -> DungeonView:
    dungeon = MiniDungeon(size = 4)
    return DungeonView(bot, userID, dungeon)