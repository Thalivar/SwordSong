import discord
import asyncio
from discord.ext import commands
from services.combadsys import combatSystem
from view.combatView import CombatView

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
                title = "You are too weak to fight!",
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
        combatView = CombatView(self.bot, userID)
        embed = discord.Embed(
            title = "❗Watch out! You ran into a monster❗",
            description = f"A wild **{monster["name"]}** appears!\n\n{monster["description"]}",
            color = discord.Color.dark_red()
        )
        embed.add_field(
            name = "Monster's Stats",
            value = f"❤️ Health: {monster["currentHealth"]}/{monster["maxHealth"]}\n"
                    f"⚔️ Attack: {monster["attack"]}\n"
                    f"🛡️ Defense: {monster["defense"]}\n"
                    f"🌟 Rarity: {monster["rarity"]}",
            inline = True
        )
        embed.add_field(
            name = f"{character["name"]}'s Stats",
            value = f"❤️ Health: {character["health"]}/{character["maxHealth"]}\n"
                    f"⚔️ Attack: {character["attack"]}\n"
                    f"🛡️ Defense: {character["defense"]}\n"
                    f"🔮 Mana: {character.get('mana', 50)}/{character.get('maxMana', 50)}",
            inline = True
        )

        message = await ctx.send(embed = embed, view = combatView)
        combatView.message = message
        

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
                description = "You're already at full health, so don't worry about resting.",
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
            healAmount = int(maxHealth * (percentPerTick / maxHealth))
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

async def setup(bot):
    await bot.add_cog(CombatCog(bot))