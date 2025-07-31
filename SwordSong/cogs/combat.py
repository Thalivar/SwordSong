import discord
import asyncio
import random
from discord.ext import commands
from services.combadsys import combatSystem

class CombatCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.combat = bot.combatSystem

        self.combatEmojis = {
            "⚔️": "attack",
            "🔥": "skillMenu",
            "🏃": "flee",
            "❌": "cancel"
        }
        self.skillEmojis = {
            "⚡": "Power Strike",
            "🔥": "Fire Ball",
            "💚": "Healing Pulse",
            "🛡️": "Defensive Stance",
            "🔙": "back"
        }
        
    @commands.command(name = "fight")
    async def fight(self, ctx):
        print("The fight command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)

        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild.",
                description = "You're not part of SwordSong, so you're not able to see your profile.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        if self.combat.getCombatState(userID):
            embed = discord.Embed(
                title = "You are already in combat!",
                description = "You're already fighting a monster, watch out!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        if character["health"] <= 0:
            embed = discord.Embed(
                title = "You are to weak to fight!",
                description = "You are to weak to fight, go rest up at the campfire before going hunting again.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        currentArea = character.get("currentArea", "forest")
        monster = self.combat.spawnMonster(userID, currentArea)
        if not monster:
            embed = discord.Embed(
                title = f"There were no monsters found in {currentArea}!",
                description = "Try again later or try hunting somewhere else!",
                color = discord.Color.orange()
            )
            await ctx.send(embed = embed)
            return
        
        combatState = self.combat.startCombat(userID, monster)
        embed = discord.Embed(
            title = "❗Watch out! You ran into a monster❗",
            description = f"A wild **{monster["name"]}** appears!\n\n{monster["description"]}",
            color = discord.Color.dark_red()
        )
        embed.add_field(
            name = "Monster's Stats",
            value = f"❤️ Health: {monster["currentHealth"]}/{monster["maxHealth"]}"
                    f"⚔️ Attack: {monster["attack"]}"
                    f"🛡️ Defense: {monster["defense"]}"
                    f"🌟 Rarity: {monster["rarity"]}",
            inline = True
        )
        embed.add_field(
            name = f"{character["name"]}'s Stats",
            value = f"❤️ Health: {character["health"]}/{character["maxHealth"]}"
                    f"⚔️ Attack: {character["attack"]}"
                    f"🛡️ Defense: {character["defense"]}",
            inline = True
        )
        embed.add_field(
            name = "Combat Commands",
            value = "Use `.attack` - to attack the monster.\n"
                    "Use `.flee` - to try and escape from the monster.\n"
                    "Use `.skill` - to use a skill.",
            inline = False
        )

        await ctx.send(embed = embed)

    @commands.command(name = "rest")
    async def rest(self, ctx):
        print("The rest command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        currentHealth = character["health"]
        maxHealth = character["maxHealth"]
        ticks = 10
        percentPerTick = 10
        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild!",
                description = "You're not part of SwordSong, So you're not allowed in the guilds resting area.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if currentHealth >= maxHealth:
            embed = discord.Embed(
                title = "You are already at full health!",
                description = "You're already at full health, so don' worry about resting.",
                color = discord.Color.green()
            )
            await ctx.send(embed = embed)
            return
        
        embed = discord.Embed(
            title = "🔥 Resting at the campfire 🔥",
            description = "Eat some s'mores and rest for a while to regain your strength.",
            color = discord.Color.gold()
        )
        embed.add_field(
            name = "Resting...",
            value = f"❤️ {currentHealth}/{maxHealth}",
            inline = True
        )
        message = await ctx.send(embed = embed)

        for i in range(ticks):
            healAmount = int(maxHealth * (percentPerTick / 100))
            newHealth = min(currentHealth + healAmount, maxHealth)
            self.db.updateCharacter(userID, {"health": newHealth})
            currentHealth = newHealth
            
            embed.set_field_at(
                0,
                name = "Resting...",
                value = f"❤️ {currentHealth}/{maxHealth}",
                inline = True
            )
            embed.set_footer(
                text = f"Resting for {i + 1}/{ticks}"
            )
            await message.edit(embed = embed)

            if newHealth >= maxHealth:
                break
            await asyncio.sleep(1)
        embed.title = "🔥 Resting complete! 🔥"
        embed.description = "You had enough s'mores for now, get back up and continue fighting!"
        embed.set_footer(text = None)
        await message.edit(embed = embed)

    # === Helper Functions ===
    async def handleCombatVictory(self, ctx, userID, monster):
        rewards = self.combat.distributeRewards(userID, monster)
        embed = discord.Embed(
            title = "Victory!",
            description = f"You defeated the **{monster["name"]}**! And earned {rewards["xp"]} XP and {rewards["coins"]} coins!",
            color = discord.Color.green()
        )
        if rewards.get("items"):
            loot = "\n".join([f"{item["quantity"]}x {item["name"]}" for item in rewards["items"]])
            embed.add_field(
                name = "Loot",
                value = loot,
                inline = False
            )
        if rewards.get("levelUp"):
            embed.add_field(
                name = "Level up!",
                value = f"Congratulations! You reached level {rewards['levelUP']['newLevel']}! Stats increased.",
                inline = False
            )
        
        await ctx.send(embed = embed)

    async def processMonsterTurn(self, ctx, userID, character, monster):
        monsterResult = self.combat.processMonsterTurn(userID)
        character = self.db.getCharacter(userID)

        if "error" in monsterResult:
            embed = discord.Embed(
                title = "Monster's attack failed!",
                description = monsterResult["error"],
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        embed = discord.Embed(
            title = "Monster's Turn",
            description = monsterResult["message"],
            color = discord.Color.dark_red()
        )
        embed.add_field(
            name = f"{character["name"]}'s Health",
            value = f"❤️ {monsterResult["playerHealth"]}/{character["maxHealth"]}",
            inline = True
        )

        await ctx.send(embed = embed)

        if monsterResult.get("playerDefeated"):
            embed = discord.Embed(
                title = "💀 Defeat!",
                description = "You were unfortunatly defeated by the monster. Go get some rest before hunting again.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            self.combat.endCombat(userID)
            return False
        return True

    async def showSkillMenu(self, ctx, originalMessage, userID):
        character = self.db.getCharacter(userID)
        availableSkills = self.combat.getAvailableSkills(userID)

        embed = discord.Embed(
            title = "🔥 Choose your skills",
            description = "Select a skill that you would like to use:",
            color = discord.Color.dark_magenta()
        )

        skillMap = {}
        emojiList = ["⚡", "🔥", "💚", "🛡️"]

        for i, skill in enumerate(availableSkills):
            if i < len(emojiList):
                emoji = emojiList[i]
                skillMap[emoji] = skill["name"]

                status = "✅ Ready" if skill["canUse"] else f"❌ Cooldown: {skill['cooldownRemaining']} turns"
                manaCost = self.combat.defaultSkills[skill["name"]].get("manaCost", 0)
                manaStatus = "💙" if character.get("mana", 0) >= manaCost else "💔"

                embed.add_field(
                    name = f"{emoji} {skill['name']} {manaStatus}({manaCost} mana)",
                    value = f"{skill['data']['description']}\n{status}",
                    inline = False
                )
            embed.add_field(
                name = "🔙 Back to Combat",
                value = "Return to to the main combat menu",
                inline = False
            )

        skillMessage = await ctx.send(embed = embed)

        for emoji in skillMap.keys():
            await skillMessage.add_reaction(emoji)
        await skillMessage.add_reaction("🔙")

        def skillCheck(reaction, user):
            return (user.id == int(userID) and str(reaction.emoji) in list(skillMap.keys()) + ["🔙"] and reaction.message.id == skillMessage.id)
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout = 30.0, check = skillCheck)

            if str(reaction.emoji) == "🔙":
                await skillMessage.delete()
                return
            
            skillName = skillMap.get(str(reaction.emoji))
            if skillName:
                await skillMessage.delete()
                await self.processSkill(ctx, originalMessage, userID, skillName)
        
        except asyncio.TimeoutError:
            await skillMessage.delete()
    
    async def updateCombatDisplay(self, message, userID):
        combatState = self.combat.getCombatState(userID)
        character = self.db.getCharacter(userID)
        monster = combatState["monster"]
        if not combatState:
            return
        
        embed = discord.Embed(
            title = "❗ Combat in Progress ❗",
            description = f"Fighting: **{monster['name']}**\n\n{monster['description']}",
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
        embed.add_field(
            name = "Combat Actions",
            value = "⚔️ - Attack the monster\n"
                    "🔥 - Use skills\n"
                    "🏃 - Try to flee\n"
                    "❌ - Cancel action",
            inline = False
        )

        if combatState["turn"] == "player":
            embed.set_footer(text = "🟢 Your turn - Choose an action!")
        else:
            embed.set_footer(text = "🔴 Monster's turn - Prepare to defend!")
        try:
            await message.edit(embed = embed)
        except:
            pass

    async def processAttack(self, ctx, message, userID):
        combatState = self.combat.getCombatState(userID)
        character = self.db.getCharacter(userID)
        monster = combatState["monster"]
        result = self.combat.processPlayerAttack(userID)
        if not combatState or combatState["turn"] != "player":
            return
        
        if "error" in result:
            embed = discord.Embed(
                title = "Your attack failed!",
                description = result["error"],
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
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
        await ctx.send(embed = embed)

        if result.get("monsterDefeated"):
            await self.handleCombatVictory(ctx, userID, monster)
            await message.clear_reactions()
            self.combat.endCombat
            return
        
        await asyncio.sleep(1)
        await self.processMonsterTurn(ctx, userID, character, monster)
        await self.updateCombatDisplay(message, userID)

    async def processSkill(self, ctx, message, userID, skillName):
        combatState = self.combat.getCombatstate(userID)
        character = self.db.getCharacter(userID)
        monster = combatState["monster"]
        if not combatState or combatState["turn"] != "player":
            return
        
        result = self.combat.processPlayerAttack(userID, skillName)
        if "error" in result:
            embed = discord.Embed(
                title = "Skill Failed!",
                description = result["error"],
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if result["action"] == "Healing Pulse":
            embed = discord.Embed(
                title = "💚 Healing Pulse 💚",
                description = result["message"],
                color = discord.Color.green()
            )
        elif result["action"] == "Defensive Stance":
            embed = discord.Embed(
                title = "🛡️ Defensive Stance 🛡️",
                description = result["message"],
                color = discord.Color.blue()
            )
        elif result["action"] == "Fire Ball":
            embed = discord.Embed(
                title = "🔥 Fire Ball 🔥",
                description = result["message"],
                color = discord.Color.red()
            )
        elif result["action"] == "Power Strike":
            embed = discord.Embed(
                title = "⚡ Power Strike ⚡",
                description = result["message"],
                color = discord.Color.gold()
            )

        if result.get("damage", 0) > 0:
            embed.add_field(
                name = "Monster's Health",
                value = f"❤️ {monster['currentHealth']}/{monster['maxHealth']}",
                inline = True
            )
        await ctx.send(embed = embed)

        if result.get("monsterDefeated"):
            await self.handleCombatVictory(ctx, userID, monster)
            await message.clear_reactions()
            self.combat.endCombat(userID)
            return
        
        await asyncio.sleep(1)
        await self.processMonsterTurn(ctx, userID, character, monster)
        await self.updateCombatDisplay(message, userID)
    
    async def processFlee(self, ctx, message, userID):
        combatState = self.combat.getCombatState(userID)
        character = self.db.getCharacter(userID)
        if not combatState:
            return
        
        if random.randint(1, 100) <= 70:
            embed = discord.Embed(
                title = "💨 You successfully fled! 💨",
                description = "You managed to succsessfully escape from the monster!",
                color = discord.Color.green()
            )
            await message.clear_reactions()
            self.combat.endCombat(userID)
            await ctx.send(embed = embed)
        else:
            embed = discord.Embed(
                title = "❌ Your Flee Attempt Failed! ❌",
                description = "YOu couldn't escape the monster!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)

            await asyncio.sleep(1)
            await self.processMonsterTurn(ctx, userID, character, combatState["monster"])
            await self.updateCombatDisplay(message, userID)

    async def handleCombatReactions(self, ctx, message, userID):

        def check(reaction, user):
            return (user.id == int(userID) and str(reaction.emoji) in self.combat_emojis and reaction.message.id == message.id)

        while True:
            combatState = self.combat.getCombatSate(userID)
            if not combatState:
                break

            if combatState["turn"] != "player":
                await asyncio.sleep(0.5)
                continue

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60.0, check = check)
                action = self.combatEmojis[str(reaction.emoji)]

                try:
                    await message.remove_reaction(reaction.emoji, user)
                except:
                    pass

                if action == "attack":
                    await self.processAttack(ctx, message, userID)
                elif action == "skillMenu":
                    await self.showSkillMenu(ctx, message, userID)
                elif action == "flee":
                    await self.processFlee(ctx, message, userID)
                elif action == "cancel":
                    continue

            except asyncio.TimeoutError:

                embed = discord.Embed(
                    title = "Combat Timeout",
                    description = "The monster got bored while you were hiding so it walked away.",
                    color = discord.Color.orange()
                )
                await message.edit(embed = embed)
                await message.clear_reactions()
                self.combat.endCombat(userID)
                break

async def setup(bot):
    await bot.add_cog(CombatCog(bot))