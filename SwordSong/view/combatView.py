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
        self.combatLog = []

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
    
    def addToCombatLog(self, message, messagType = "info"):
        emojis = {
            "playerAttack": "⚔️",
            "monsterAttack": "🔴",
            "skill": "✨",
            "heal": "💚",
            "defense": "🛡️",
            "flee": "💨",
            "info": "ℹ️"
        }
        emoji = emojis.get(messagType, "•")
        self.combatLog.append(f"{emoji} {message}")
        if len(self.combatLog) > 4:
            self.combatLog.pop(0)

    def updateEmbed(self, include_log = True):
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

        if include_log and self.combatLog:
            logText = "\n".join(self.combatLog)
            embed.add_field(
                name = "📜 Recent actions 📜",
                value = logText,
                inline = False
            )

        if combatState["turn"] == "player":
            embed.set_footer(text = "🟢 Your turn - Choose an action!")
        else:
            embed.set_footer(text = "🔴 Monster's turn - Prepare to defend!")
        return embed
    
    @discord.ui.button(label = "Attack", style = discord.ButtonStyle.danger, emoji = "⚔️")
    async def attackButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        combatState = self.combat.getCombatState(self.userID)
        if not combatState or combatState["turn"] != "player":
            return
        
        await self.processAttack(interaction)
    
    @discord.ui.button(label = "Skills", style = discord.ButtonStyle.primary, emoji = "🔥")
    async def skillsButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.showSkillMenu(interaction)
    
    @discord.ui.button(label = "Flee", style = discord.ButtonStyle.primary, emoji = "🏃")
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
        self.addToCombatLog(
            f"You dealth {result['damage']} damage to {monster['name']}! ({monster['currentHealth']}/{monster['maxHealth']} HP)",
            "playerAttack"
        )

        if result.get("monsterDefeated"):
            await self.handleVictory(interaction, monster)
            return
        
        updatedEmbed = self.updateEmbed()
        if updatedEmbed:
            await interaction.edit_original_response(embed = updatedEmbed, view = self)
        
        await asyncio.sleep(1)
        await self.processMonsterTurn(interaction)
    
    async def processMonsterTurn(self, interaction):
        combatState = self.combat.getCombatState(self.userID)
        character = self.db.getCharacter(self.userID)
        monsterResult = self.combat.processMonsterTurn(self.userID)
        character = self.db.getCharacter(self.userID)

        if "error" in monsterResult:
            self.addToCombatLog(f"Monster's attack failed: {monsterResult['error']}", "info")
        else:
            monster = combatState["monster"]
            self.addToCombatLog(
                f"{monster['name']} dealt {monsterResult['damage']} to you! ({monsterResult['playerHealth']}/{character['maxHealth']} HP)",
                "monsterAttack"
            )

        if monsterResult.get("playerDefeated"):
            self.addToCombatLog("You have been defeated!", "info")
            defeatedEmbed = self.updateEmbed()
            defeatedEmbed.title = "💀 Defeat! 💀"
            defeatedEmbed.description = "You were unfortunately defeated by the monster. Go get some rest before you go back hunting monsters."
            defeatedEmbed.color = discord.Color.red()

            await interaction.edit_original_response(embed = defeatedEmbed, view = None)
            self.combat.endCombat(self.userID)
            self.stop()
            return False
        
        updatedEmbed = self.updateEmbed()
        if updatedEmbed:
            await interaction.edit_original_response(embed = updatedEmbed, view = self)
        return True
    
    async def processFlee(self, interaction):
        if random.randint(1, 100) <= 70:
            self.addToCombatLog("You successfully escaped from the monster!", "flee")

            fleeEmbed = self.updateEmbed()
            fleeEmbed.title = "💨 You successfully ran away! 💨"
            fleeEmbed.description = "YOu manged to distract the monster and run away from it!"
            fleeEmbed.color = discord.Color.green()

            await interaction.edit_original_response(embed = fleeEmbed, view = None)
            self.combat.endCombat(self.userID)
            self.stop()
        else:
            self.addToCombatLog("You failed to escape! The monster is enraged!", "info")
            updatedEmbed = self.updateEmbed()
            if updatedEmbed:
                await interaction.edit_original_response(embed = updatedEmbed, view = self)
            
            await asyncio.sleep(1)
            await self.processMonsterTurn(interaction)
    
    async def processSkillUsage(self, interaction, skillName, result):
        if result.get("damage", 0) > 0:
            CombatState = self.combat.getCombatState(self.userID)
            monster = CombatState["monster"]
            self.addToCombatLog(
                f"Used {skillName}! Dealth {result['damage']} damage to {monster['name']}",
                "skill"
            )
        elif skillName == "Healing Pulse":
            self.addToCombatLog(
                f"Used Healing Pulse! Restored {result.get('healAmount', 0)} HP!",
                "heal"
            )
        elif skillName == "Defensive Stance":
            self.addToCombatLog("Entered Defensive Stance! Damage reduced!", "defense")
        else:
            self.addToCombatLog(f"Used {skillName}!", "skill")
        
        updateEmbed = self.updateEmbed()
        if updateEmbed:
            await interaction.edit_original_message(embed = updateEmbed, view = self)
    
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
            manaCost = self.combat.defaultSkills[skill["name"]].get("manaCost", 0)
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
        self.addToCombatLog(f"Victory! You defeated {monster['name']}!", "info")

        victoryEmbed = self.updateEmbed()
        victoryEmbed.title = "🎉 Victory! 🎉"
        victoryEmbed.color = discord.Color.green()

        rewardsText = f"**Rewards Earned:**\n• {rewards['xp']} XP\n• {rewards['coins']} coins"
        if rewards.get("items"):
            lootList = [f"• {item['quantity']}x {item['name']}" for item in rewards["items"]]
            rewardsText += f"\n• **Loot** {', '.join([item['name'] for item in rewards['items']])}"

        if rewards.get("levelUP"):
            rewardsText += f"\n• **🎊 LEVEL UP! 🎊 You reached level {rewards['levelUP']['newLevel']}!"

        victoryEmbed.add_field(
            name = "🏆 Fangs of Fortune 🏆",
            value = rewardsText,
            inline = False
        ) 

        await interaction.edit_original_response(embed = victoryEmbed, view = None)
        self.combat.endCombat(self.userID)
        self.stop()

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
                emoji = emoji,
                style = discord.ButtonStyle.success if skill["canUse"] else discord.ButtonStyle.secondary,
                disabled = not skill["canUse"],
                custom_id = f"skill_{skill['name']}"
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
    
    async def useSkill(self, interaction, skillName):
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
        
        await interaction.delete_original_response()
        await self.combatView.processSkillUsage(interaction, skillName, result)

        if result.get("monsterDefeated"):
            await self.combatView.handleVictory(interaction, combatState["monster"])
            return

        await asyncio.sleep(1)
        await self.combatView.processMonsterTurn(interaction)