import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class combatSystem:
    def __init__(self, db, areasData, itemsData):
        self.db = db
        self.areas = areasData
        self.item = itemsData
        self.activeCombats = {}

        self.rarityWeight = { # <= Sets the weight of the rarities of the different monsters
            "common": 60,
            "uncommon": 25,
            "rare": 12,
            "legendary": 3
        }

        self.defaultSkills= { # <= Sets the multipliers and stats for the skills
            "Power Strike": {
                "damageMultiplier": 1.5,
                "cooldown": 3,
                "manaCost": 10,
                "description": "A powerful strike that deals 150% damage"
            },
            "Fire Ball": {
                "damageMultiplier": 2.0,
                "cooldown": 4,
                "manaCost": 20,
                "description": "A magical ball of fire dealing 2x damage"
            },
            "Healing Pulse": {
                "healPercent": 0.4,
                "cooldown": 4,
                "manaCost": 1.5,
                "description": "A magical pulse that heals 30% of your maximum health"
            },
            "Defensive Stance": {
                "damageMultiplier": 0.5,
                "defenseBoost": 2.0,
                "duration": 3,
                "cooldown": 5,
                "manaCost": 20,
                "description": "Take 50% for 3 turns but at a cost of dealing less damage"
            }
        }

    # === Creates a monster instance with HP tracking ===
    def _createMonsterInstance(self, monsterTemplate: Dict) -> Dict:
        monster = monsterTemplate.copy()
        monster["currentHealth"] = monster["health"]
        monster["maxHealth"] = monster["health"]
        return monster

    # === Spawns monsters based on the rarity system and boss logic ===
    def spawnMonster(self, userID: str, area: str = "forest") -> Dict:
        # Checks the fight count for spawning in a boss monster
        fightStats = self.db.getFightStats(userID)
        if not fightStats:
            self.db.initializeFightStats(userID)
            fightStats = {"fightsSinceBoss": 0, "totalFights": 0}

        # Forces a boss to spawn every 15 fights
        if fightStats["fightsSinceBoss"] > 14:
            monsters = [m for m in self.areas["areas"][area]["monsters"] if m["rarity"] == "boss"]
            if monsters:
                selectedMonster = random.choice(monsters)
                self.db.updateFightStats(userID, {"fightsSinceBoss": 0})
                return self._createMonsterInstance(selectedMonster)
        
        # Spawns the regular monsters based on the rarity
        availableMonsters = []
        for monster in self.areas["areas"][area]["monsters"]:
            if monster["rarity"] != "boss":
                weight = self.rarityWeight[monster["rarity"]]
                availableMonsters.extend([monster] * weight)

        if not availableMonsters:
            return None
        
        selectedMonster = random.choice(availableMonsters)

        # Updates the fight stats in the db
        self.db.updateFightStats(userID, {
            "totalFights": fightStats["totalFights"] + 1,
            "fightsSinceBoss": fightStats["fightsSinceBoss"] + 1
        })
        return self._createMonsterInstance(selectedMonster)
    
    # === Initializes a new combat session ===
    def startCombat(self, userID: str, monster: Dict) -> Dict:
       combatState = {
            "userID": userID,
            "monster": monster,
            "turn": "player",
            "turnCount": 1,
            "playerEffects": {}, # <= Stores temporary stats like defensive stance or burn effects for in the future
            "monsterEffects": {}
        }
       
       self.activeCombats[userID] = combatState
       return combatState
    
    # === Fetches the current combat state for a user ===
    def getCombatState(self, userID: str) -> Optional[Dict]:
        return self.activeCombats.get(userID)
    
    # === Ends the combat session after its over and clean it up ===
    def endCombat(self, userID: str):
        if userID in self.activeCombats:
            del self.activeCombats[userID]

    # === Calculates the damage that is done with skill multipliers and randomizations ===
    def calculateDamage(self, attackerStats: Dict, defenderStats: Dict, skillData: Optional[Dict] = None) -> int:
        baseAttack = attackerStats.get("attack", 10)
        baseDefense = defenderStats.get("defense", 0)

        multiplier = 1.0
        if skillData and "damageMultiplier" in skillData: # <- Applies the skill multiplier
            multiplier = skillData["damageMultiplier"] 

        baseDamage = baseAttack * multiplier - (defenderStats["defense"] * 0.5) # <- The base damage formula
        finalDamage = baseDamage * random.uniform(0.8, 1.2) # <- Adds a randomization to the damage (80%, 120%)

        return max(1, int(finalDamage)) # <- Ensures the minimum damage deal is 1
    
    # === Processes the player's attack turns ===
    def processPlayerAttack(self, userID: str, skillName: Optional[str] = None) -> Dict:
        # Checks if the user is in combat
        combatState = self.activeCombats.get(userID)
        if not combatState:
            return{"error": "There is no active combat found"}
        
        # Checks if the user has a character in the database
        character = self.db.getCharacter(userID)
        if not character:
            return {"error": "Character is not found"}
        
        monster = combatState["monster"]
        result = {"action": "attack", "damage": 0, "message": ""}

        # Handles skill usage
        skillData = None
        if skillName and skillName in self.defaultSkills:
            # Checks if the skill is on cooldown
            if self.db.isSkillOnCooldown(userID, skillName):
                cooldownLeft = self.db.getSkillCooldown(userID, skillName)
                return {"error": f"{skillName} is still on cooldown for {cooldownLeft} more turns"}
            
            skillData = self.defaultSkills[skillName]

            # This will check the mana cost of the skill
            if character.get("mana", 0) < skillData.get("manaCost", 0):
                return {"error": "Not enough mana to use still skill"}
            
            # This will apply the new mana ammount to the character after using a skill
            newMana = character["mana"] - skillData["manaCost"]
            self.db.updateCharacter(userID, {"mana": newMana})

            # After the skill has been cast this will apply a cooldown
            self.db.setSkillCooldown(userID, skillName, skillData["cooldown"])

        # This will handle the heal skill
        if skillName == "Heal Pulse":
            healAmount = int(character["maxHealth"] * skillData["healPercent"])
            newHealth = min(character["maxHealth"], character["health"] + healAmount)
            self.db.updateCharacter(userID, {"health": newHealth})

            result["action"] = "heal"
            result["healAmount"] = healAmount
            result["message"] = f"YOu healed for {healAmount} HP!"

        # This will handle the defensive stance skill
        elif skillName == "Defensive Stance":
            combatState["playerEffects"]["defensiveStance"] = skillData["duration"]

            result["action"] = "defensiveStance"
            result["message"] = "You have entered a defensive stance!"
        
        # This will handle a regular attack or a attack skill
        else:
            playerStats = {
                "attack": character["attack"],
                "defense": character["defense"]
            }

            monsterStats = {
                "attack": monster["attack"],
                "defense": monster["defense"]
            }

            damage = self.calculateDamage(playerStats, monsterStats, skillData)
            monster["currentHealth"] -= damage

            result["damage"] = damage
            result["message"] = f"You have dealt {damage} damage to the {monster["name"]}!"

            if skillName:
                result["message"] = f"You used {skillName} and dealth {damage} damage to the {monster["name"]}!"

        # Checks if the monster is defeated
        if monster["currentHealth"] <= 0:
            result["monsterDefeated"] = True
            return result
        
        # If it's not defeated it will switch to the monsters turn
        combatState["turn"] = "monster"
        return result
    
    # === Processes the monsters turn ===
    def processMonsterTurn(self, userID: str) -> Dict:
        combatState = self.activeCombats.get(userID)
        if not combatState:
            return {"error": "No is no active combat found"}
        
        character = self.db.getCharacter(userID)
        monster = combatState["monster"]

        monsterStats = {
            "attack": monster["attack"],
            "defense": monster["defense"]
        }

        playerStats = {
            "attack": character["attack"],
            "defense": character["defense"]
        }

        # Checks for defensive stance, if the user has defensive stance on applies the damage reduction
        damageReduction = 1.0
        if "defensiveStance" in combatState["playerEffects"]:
            damageReduction = 0.5
            combatState["playerEffects"]["defensiveStance"] -= 1
            if combatState["playerEffects"]["defensiveStance"] <= 0:
                del combatState["playerEffects"]["defensiveStance"]

        # Calculates the damage the monster will do to the user
        damage = self.calculateDamage(monsterStats, playerStats)
        damage = int(damage * damageReduction)

        # Applies the damage
        newHealth = character["health"] - damage
        self.db.updateCharacter(userID, {"health": newHealth})

        result = {
            "damage": damage,
            "message": f"The {monster["name"]} attacked you for {damage} damage!",
            "playerHealth": newHealth
        }

        # Checks if the user is defeated
        if newHealth <= 0:
            result["playerDefeated"] = True
            return result
        
        # If the user is still alive updates the turn count + skill cooldowns
        combatState["turnCount"] += 1
        combatState["turn"] = "player"
        self.db.updateSkillCooldown(userID)

        return result
    
    # === Gives the user the rewards after winning the battle ===
    def distributeRewards(self, userID: str, monster: Dict) -> Dict:
        character = self.db.getCharacter(userID)
        rewards = {
            "xp": monster["xpReward"],
            "coins": random.randint(monster["xpReward"] // 2, monster["xpReward"]),
            "items": []
        }

        # Calculates the character is getting and checks for level up
        newXP = character["xp"] + rewards["xp"]
        newCoins = character["coins"] + rewards["coins"]
        updates = {"xp": newXP, "coins": newCoins}

        # Checks for level up
        levelUP = False
        if newXP >= character["xpToLevel"]:
            newLevel = character["level"] + 1
            remainingXP = newXP - character["xpToLevel"]
            newXPToLevel = character["xpToLevel"] + (newLevel * 50) # Sets the scaling for levelup

            # If the user lavel's up the stats increase
            newMaxHealth = character["maxHealth"] + 20
            newAttack = character["attack"] + 4
            newDefense = character["defense"] + 2
            newMana = character.get("maxMana", 50) + 10

            updates.update({
                "level": newLevel,
                "xp": remainingXP,
                "xpToLevel": newXPToLevel,
                "maxHealth": newMaxHealth,
                "health": newMaxHealth, # <= refreshes the health back to full
                "attack": newAttack,
                "defense": newDefense,
                "maxMana": newMana,
                "mana": newMana # <= Refreses the mana back to full
            })

            levelUP = True
            rewards["levelUP"] = {
                "newLevel": newLevel,
                "healthIncrease": 20,
                "attackIncrease": 4,
                "defenseIncrease": 2,
                "manaIncrease": 10
            }
        
        # Handles loot drops
        if "lootTable" in monster:
            for itemName, lootData in monster["lootTable"].items():
                if random.randint(1, 100) <= lootData["chance"]:
                    quantity = lootData["quantity"]
                    if isinstance(quantity, list):
                        quantity = random.randint(quantity[0], quantity[1])

                    self.db.addItem(userID, itemName, quantity)
                    rewards["items"].append({"name": itemName, "quantity": quantity})
        
        # Applies the level up update to the character
        self.db.updateCharacter(userID, updates)
        return rewards
    
    # === Checks all the skills that are not on cooldown ===
    def getAvailableSkills(self, userID: str) -> List[Dict]:
        available = []
        character = self.db.getCharacter(userID)

        for skillName, skillData in self.defaultSkills.items():
            cooldownRemaining = self.db.getSkillCooldown(userID, skillName)
            canUse = (cooldownRemaining == 0 and character.get("mana", 0) >= skillData.get("manaCost", 0))

            available.append({
                "name": skillName,
                "data": skillData,
                "cooldownRemaining": cooldownRemaining,
                "canUse": canUse
            })

        return available