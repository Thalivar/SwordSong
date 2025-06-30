import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class combSystem:
    def __init__(self, db, areasData, itemsData):
        self.db = db
        self.areas = areasData
        self.item = itemsData
        self.activeCombats = {}

        self.rarityWeight = {
            "common": 60,
            "uncommonn": 25,
            "rare": 12,
            "legendary": 3
        }

        self.defaultSkills= {
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
                "Description": "A magical pulse that heals 30% of your maximum health"
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

    # === Creates a monster instance with HP tracking
    def _createMonsterInstance(self, monsterTemplate: Dict) -> Dict:
        monster = monsterTemplate.copy()
        monster["currentHealth"] = monster["health"]
        monster["maxHealth"] = monster["health"]
        return monster

    # === Spawns monsters based on the rarity system and boss logic ===
    def spawnMonster(self, userID: str, area: str = "forest") -> Dict:
        fightStats = self.db.getFightStats(userID)
        if not fightStats:
            self.db.initializeFightStats(userID)
            fightStats = {"fightSinceBoss": 0, "totalFights": 0}

        if fightStats["fightsSinceBoss"] > 14:
            monsters = [m for m in self.areas["areas"][area]["monsters"] if m["rarity"] == "boss"]
            if monsters:
                selectedMonster = random.choice(monsters)
                self.db.updateFightStats(userID, {"fightsSinceBoss": 0})
                return self._createMonsterInstance(selectedMonster)
        
        availableMonsters = []
        for monster in self.areas["area"][area]["monsters"]:
            if monster["rarity"] != "boss":
                weight = self.rarityWeight(monster["rarity"], 1)
                availableMonsters.extend([monster] * weight)

        if not availableMonsters:
            return None
        
        selectedMonster = random.choice(availableMonsters)

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
            "playerEffects": {},
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

        baseDamage = baseAttack * multiplier - (defenderStats * 0.5) # <- The base damage formula
        finalDamage = baseDamage * random.uniform(0.8, 1.2) # <- Adds a randomization to the damage (80%, 120%)

        return max(1, int(finalDamage)) # <- Ensures the minimum damage deal is 1
    
    # === Processes the player's attack turns ===
    def processPlayerAttack(self, userID: str, skillName: Optional[str] = None) -> Dict:
        combatState = self.activeCombats.get(userID)
        if not combatState:
            return{"error": "There is no active combat found"}
        
        character = self.db.getCharacter(userID)
        if not character:
            return {"error": "Character is not found"}
        
        monster = combatState["monster"]
        result = {"action": "attack", "damage": 0, "message": ""}

        skillData = None
        if skillName and skillName in self.defaultSkills:
            if self.db.isSkillOnCooldown(userID, skillName):
                cooldownLeft = self.db.getSkillCooldown(userID, skillName)
                return {"Error": f"{skillName} is still on cooldown for {cooldownLeft} more turns"}
            
            skillName = self.defaultSkills[skillName]

            if character.get("mana", 0) < skillData.get("manaCost", 0):
                return {"error": "Not enough mana to use still skill"}
            
            newMana = character["mana"] - skillData["manaCost"]
            self.db.updateCharacter(userID, {"mana": newMana})
    