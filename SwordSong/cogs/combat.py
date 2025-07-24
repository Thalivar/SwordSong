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

    @commands.command(name = "attack")
    async def attack(self, ctx):
        print("The attack command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        combatState = self.combat.getCombatState(userID)
        monster = combatState.get("monster", None)
        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild.",
                description = "You're not part of SwordSong, so you're not allowed to hunt monsters or fight them.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        if not combatState:
            embed = discord.Embed(
                title = "You're are not in combat!",
                description = "You're not in combat, use `.fight` to start hunting monsters.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        if combatState["turn"] != "player":
            embed = discord.Embed(
                title = "It's not your turn!",
                description = "Focus on dodging the monster's attacks before attack back!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        result = self.combat.processPlayerAttack(userID)
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
            value = f"❤️ {monster["currentHealth"]}/{monster["maxHealth"]}",
            inline = True
        )
        await ctx.send(embed = embed)

        if result.get("monsterDefeated"):
            await self.handleCombatVictory(ctx, userID, monster)
            self.combat.endCombat(userID)
            return
        
        await asyncio.sleep(1)
        await self.processMonsterTurn(ctx, userID, character, monster)
    
    @commands.command(name = "skill")
    async def skill(self, ctx, *, skillName = None):
        print(f"Skill command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        combatState = self.combat.getCombatState(userID)
        monster = combatState["monster"]
        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild!",
                description = "You're not part of SwordSong! So you're not allowed to use skills.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        if not combatState:
            embed = discord.Embed(
                title = "You're not in combat!",
                description = "You're not allowed to use skills outside of combat.",
                color = discord.Color.orange()
            )
            await ctx.send(embed = embed)
            return
        if combatState["turn"] != "player":
            embed = discord.Embed(
                title ="It's not your turn!",
                description = "Focus on dodging the monsters attacks before using a skill!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if not skillName:
            availableSkills = self.combat.getAvailableSkills(userID)

            embed = discord.Embed(
                title = "Available Skills",
                description = "Please choose a skill to use:",
                color = discord.Color.dark_blue()
            )

            for skill in availableSkills:
                status = "✅ Ready" if skill["canUse"] else f"❌ Cooldown: {skill["cooldownRemaining"]} turn"

                embed.add_field(
                    name = skill["name"],
                    value = f"{skill["data"]["description"]}\n{status}",
                    inline = True
                )
            embed.add_field(
                name = "Usage",
                value = "Use `.skill <Skill Name> to cast a skill",
                inline = False
            )
            await ctx.send(embed = embed)
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
        
        if result["action"] == "Heal Pulse":
            embed = discord.Embed(
                title = "💚 Heal Pulse 💚",
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
        else:
            embed = discord.Embed(
                title = "Unknown Skill",
                description = "You don't know that skill, please try casting one that you know.",
                color = discord.Color.red()
            )

        if result.get("damage", 0) > 0:
            embed.add_field(
                name = "Monster's Health",
                value = f"❤️ {monster["currentHealth"]}/{monster["maxHealth"]}",
                inline = True
            )

        await ctx.send(embed = embed)

        if result.get("monsterDefeated"):
            await self.handleCombatVictory(ctx, userID, monster)
            self.combat.endCombat(userID)
            return
        await asyncio.sleep(1)
        await self.processMonsterTurn(ctx, userID, character, monster)

    @commands.command(name = "flee")
    async def flee(self, ctx):
        print(f"The flee command was called by:", ctx.author.name)
        userID = str(ctx.author.id)
        character = self.db.getCharacter(userID)
        combatState = self.combat.getCombatState(userID)
        if not character:
            embed = discord.Embed(
                title = "You're not part of the guild!",
                description = "You're not part of SwordSong, so you're able hunt monsters.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        if not combatState:
            embed = discord.Embed(
                title = "You're not in combat!",
                description = "You're not in combat, use `.fight` to start hunting monsters.",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)
            return
        
        if random.randint(1, 100) <= 70:
            embed = discord.Embed(
                title = "💨 You successfully fled! 💨",
                description = "You managed to successfully escape from the monster!",
                color = discord.Color.green()
            )
            self.combat.endCombat(userID)
        else:
            embed = discord.Embed(
                title = "❌ Flee Failed! ❌",
                description = "You couldn't escape! The monster managed to catch up to you!",
                color = discord.Color.red()
            )
            await ctx.send(embed = embed)

            await asyncio.sleep(1)
            await self.processMonsterTurn(ctx, userID, character, combatState["monster"])
            return
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

async def setup(bot):
    await bot.add_cog(CombatCog(bot))