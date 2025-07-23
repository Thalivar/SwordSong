import discord
from discord.ext import commands
import asyncio
from services.combadsys import combatSystem

class CombatCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.combat = bot.combat
        
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
                color = discord.color.red()
            )
            await ctx.send(embed = embed)
            return
        
        currentArea = character.get("currentArea", "Forest")
        monster = self.combat.spawnMonster(userID, currentArea)
        if not monster:
            embed = discord.Embed(
                title = f"There were no monsters found in {currentArea}!",
                description = "Try again later or try hunting somewhere else!",
                color = discord.Color.orange()
            )
            await ctx.send(ebmed = embed)
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
        
        result = self.combat.attack(userID)
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
            combatSystem.endCombat(userID)
            return
        
        await asyncio.sleep(1)
        await self.processMonsterTurn(ctx, userID, character, monster)


    # === Helper Functions ===
    async def handleCombatVictory(ctx, userID, monster):
        rewards = combatSystem.handleVictory(userID, monster)
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
        monsterResult = self.combat.monsterAttack(userID)
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
            value = f"❤️ {monsterResult["playerHealth"]}/{monsterResult["maxHealth"]}",
            inline = True
        )



