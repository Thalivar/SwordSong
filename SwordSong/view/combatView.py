import discord
from discord.ext import commands
import asyncio
import random

class CombatView(discord.ui.View):
    def __init__(self, bot, userID):
        super().__init__(timeout = 180)
        self.bot = bot
        self.userID = userID
        self.db = bot.db
        self.combat = bot.combatSystem

    async def interaction_check(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.userID:
            await interaction.response.send_message("This isn't your fight!", ephemeral = True)
            return False
        return True
    
    async def on_timeout(self):
        self.combat.endCombat(self.userID)
        for item in self.children:
            item.disabled = True

        try:
            embed = discord.Embed(
                title = "Combat Timeout",
                description = "The monster got bored while your were hiding so it walked away.",
                color = discord.Color.gray()
            )
            await self.message.edit(embed = embed, view = self)
        except:
            pass

    def updateEmbed(self):
        combatState = self.combat.getCombatState(self.userID)
        character = self.db.getCharacter(self.userID)
        if not combatState or not character:
            return None
        
        monster = combatState["monster"]
        embed = discord.Embed(
            title = "❗ Combat in Progress ❗",
            description = f"Fighting: **{monster['name']}**\n\n"
                          f"{monster['description']}",
            color = discord.Color.dark_red()  
        )
        embed.add_field(
            name = "Monster's Stats",
            value = f"❤️ Health: {monster['currentHealth']}/{monster['maxHealth']}\n"
                    f"⚔️ Attack: {monster['attack']}\n"
                    f"🛡️ Defense: {monster['defense']}\n"
                    f"🌟 Rarity: {monster['rarity']}",
            inline = True
        )
        embed.add_field(
            name = f"{character['name']}'s Stats",
            value = f"❤️ Health: {character['health']}/{character['maxHealth']}\n"
                    f"⚔️ Attack: {character['attack']}\n"
                    f"🛡️ Defense: {character['defense']}\n"
                    f"🔮 Mana: {character.get('mana', 50)}/{character.get('maxMana', 50)}",
            inline = True
        )

        if combatState["turn"] == "player":
            embed.set_footer(text = "🟢 Your turn - Choose an action!")
        else:
            embed.set_footer(text = "🔴 Monster's turn - Prepare to defend!")
        return embed
    
    @discord.ui.view(label = "Attack", style = discord.ButtonStyle.danger, emoji = "⚔️")
    async def attackButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        combatState = self.combat.getCombatState(self.userID)
        if not combatState or combatState["turn"] != "player":
            return
        
        await self.processAttack(interaction)
    
    @discord.ui.view(label = "Skills", style = discord.ButtonStyle.primary, emoji = "🔥")
    async def skillsButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.showSkillMenu(interaction)
    
    @discord.ui.view(label = "Flee", style = discord.ButtonStyle.primary, emoji = "🏃")
    async def fleeButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.processFlee(interaction)
    
    async def processAttack(self, interaction):
        result = self.combat.processPlayerAttack(self.userID)
        combatState = self.combat.getCombatState(self.userID)

        if "error" in result:
            embed = discord.Embed(
                title = "Your attack failed!",
                description = result["error"],
                color = discord.Color.red()
            )
            await interaction.followup.send(embed = embed, ephemeral = True)
            return
        
        monster = combatState["monster"]
        embed = discord.Embed(
            title = "⚔️ Attack Successful! ⚔️",
            description = result["message"],
            color = discord.Color.blurple()
        )
        embed.add_field(
            name = "Monster's Health",
            value = f"❤️ {monster['currentHealth']}/{monster['maxHealth']}",
            inline = True
        )
        await interaction.followup.send(embed = embed)

        if result.get("monsterDefeated"):
            await self.handleVictory(interaction, monster)
            return
        
        await asyncio.sleep(1)
        await self.processMonsterTurn(interaction)
    
    async def processMonsterTurn(self, interaction):
        combatState = self.combat.getCombatState(self.userID)
        character = self.db.getCharacter(self.userID)
        monsterResult = self.combat.processMonsterTurn(self.userID)
        character = self.db.getCharacter(self.userID)

        if "error" in monsterResult:
            embed = discord.Embed(
                title = "Monster's attack failed!",
                description = monsterResult["error"],
                color = discord.Color.red()
            )
            await interaction.followup.send(embed = embed)
            return
        
        embed = discord.Embed(
            title = "Monster's Turn",
            description = monsterResult["message"],
            color = discord.Color.dark_red()
        )
        embed.add_field(
            name = f"{character['name']}'s Health",
            value = f"❤️ {monsterResult['playerHealth']}/{character['maxHealth']}",
            inline = True
        )
        await interaction.followup.send(embed = embed)

        if monsterResult.get("playerDefeated"):
            embed = discord.Embed(
                title = "💀 Defeat! 💀",
                description = "You were unfortunatly defeated by the monster. Go get some rest before you start hunting monsters agains.",
                color = discord.Color.red()
            )
            await interaction.followup.send(embed = embed)
            self.combat.endCombat(self.userID)
            self.stop()
            return False
        
        updatedEmbed = self.updateEmbed()
        if updatedEmbed:
            await interaction.edit_original_response(embed = updatedEmbed, view = self)
        return True
    
    async def processFlee(self, interaction):
        if random.randint(1, 100) <= 70:
            embed = discord.Embed(
                title = "💨 You successfully ran away! 💨",
                description = "You managed to distract the monster and run away from it!",
                color = discord.Color.green()
            )
            self.combat.endCombat(self.userID)
            self.stop()
            await interaction.followup.send(embed = embed)
        else:
            embed = discord.Embed(
                title = "❌ You couldn't outrun the monster! ❌",
                description = "The monster was enraged by your measle attempt of a distraction, and went to attack your right away.",
                color = discord.Color.red()
            )
            await interaction.followup.send(embed = embed)
            await asyncio.sleep(1)
            await self.processMonsterTurn(interaction)
    
    async def showSkillMenu(self, interaction):
        character = self.db.getCharacter(self.userID)
        availableSkills = self.combat.getAvailableSkills(self.userID)
        skillView = SkillSelectionView(self.bot, self.userID, self, availableSkills)

        embed = discord.Embed(
            title = "🔥 Choose your skills 🔥",
            description = "Select a skill that you would like to use:",
            color = discord.Color.dark_magenta()         
        )
        for skill in availableSkills:
            status = "✅ Ready" if skill["canUse"] else f"❌ Cooldown: {skill['cooldownRemaining']} turns"
            manaCost = self.combat.defaultSkills[skill["name"]].get("manaCose", 0)
            manaStatus = "💙" if character.get("mana", 0) >= manaCost else "💔"
            embed.add_field(
                name = f"{skill['name']} {manaStatus}({manaCost} mana)",
                value = f"{skill['data']['description']}\n"
                        f"{status}",
                inline = False          
            )
        
        await interaction.followup.send(embed = embed, view = skillView, ephemeral = True)
    
    async def handleVictory(self, interaction, monster):
        rewards = self.combat.distributeRewards(self.userID, monster)
        embed = discord.Embed(
            title = "Victory!",
            description = f"YOu defeated the **{monster['name']}**! And earned {rewards['xp']} XP and {rewards['coins']} coins!",
            color = discord.Color.green()
        )
        if rewards.get("items"):
            loot = "\n".join([f"{item['quanity']}x {item['name']}" for item in rewards["items"]])
            embed.add_field(
                name = "loot",
                value = loot,
                inline = False
            )
        
        if rewards.get("levelUP"):
            embed.add_field(
                name = "Level up!",
                value = f"Congratulations! You reached level {rewards['levelUP']['newLevel']}!",
                inline = False
            )
        
        self.combat.endCombat(self.userID)
        self.stop()
        await interaction.followup.send(embed = embed)

class SkillSelectionView(discord.ui.View):
    def __init__(self, bot, userID, combatView, availableSkills):
        super().__init__(timeout = 60)
        self.bot = bot
        self.userID = userID
        self.combatView = combatView
        self.availableSkills = availableSkills

        skillEmojis = ["⚡", "🔥", "💚", "🛡️"]

        for i, skill in enumerate(availableSkills[:4]):
            emoji = skillEmojis[i] if i < len(skillEmojis) else "🎯"
            button = discord.ui.Button(
                label = skill["name"],
                emojo = emoji,
                style = discord.ButtonStyle.success if skill["canUse"] else discord.ButtonStyle.secondary,
                disabled = not skill["canUse"],
                custom_id = f"skill{skill['name']}"
            )

            async def skillCallback(interaction, skillName = skill["name"]):
                await interaction.response.defer()
                await self.useSkill(interaction, skillName)
            
            button.callback = skillCallback
            self.add_item(button)
    
    async def interaction_check(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.userID:
            await interaction.response.send_message("This isn't your skill menu!", ephemeral = True)
            return False
        return True
    
    @discord.ui.button(label = "Back", emoji = "🔙", style = discord.ButtonStyle.secondary, row = 4)
    async def backButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()
    
    async def userSkill(self, interaction, skillName):
        combatState = self.combatView.combat.getCombatState(self.userID)
        if not combatState or combatState["turn"] != "player":
            return

        result = self.combatView.combat.processPlayerAttack(self.userID, skillName)
        if "error" in result:
            embed = discord.Embed(
                title = "Skill Failed!",
                description = result["error"],
                color = discord.Color.red()
            )
            await interaction.followup.send(embed = embed, ephemeral = True)
            return

        skillEmbeds = {
            "Healing Pulse": ("💚 Healing Pulse 💚", discord.Color.green()),
            "Defensive Stance": ("🛡️ Defensive Stance 🛡️", discord.Color.blue()),
            "Fire Ball": ("🔥 Fire Ball 🔥", discord.Color.red()),
            "Power Strike": ("⚡ Power Strike ⚡", discord.Color.gold())
        }

        title, color = skillEmbeds.get(result["action"], ("✨ Skill Used ✨", discord.Color.purple()))
        embed = discord.Embed(
            title = title,
            description = result["message"],
            color = color
        )

        if result.get("damage", 0) > 0:
            monster = combatState["monster"]
            embed.add_field(
                name = "Monster's Health",
                value = f"❤️ {monster['currentHealth']}/{monster['maxHealth']}",
                inline = True
            )
        
        await interaction.delete_original_response()
        await interaction.followup.send(embed = embed)

        if result.get("monsterDefeated"):
            await self.combatView.handleVictory(interaction, combatState["monster"])
            return

        await asyncio.sleep(1)
        await self.combatView.processMonsterTurn(interaction)