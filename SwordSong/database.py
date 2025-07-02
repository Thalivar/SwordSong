import sqlite3
from pathlib import Path

class Database:
    def __init__(self):
        self.db_path = Path(__file__).parent / "game.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.setupDatabase()

    # === Seting up the database ===
    def setupDatabase(self):

        # === Creates a character table ===
        self.cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS characters (
                userID TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                xpToLevel INTEGER DEFAULT 100,
                health INTEGER DEFAULT 100,
                maxHealth INTEGER DEFAULT 100,
                attack INTEGER DEFAULT 10,
                defense INTEGER DEFAULT 5,
                coins INTEGER DEFAULT 0,
                currentArea TEXT DEFAULT 'Starter Village'
            )''')
        
        # === Creates the inventory table ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userID TEXT,
                itemName TEXT,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (userID) REFERENCES characters(userID)
            )''')
        
        # === Created the equipment table ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                userID TEXT,
                slot TEXT,
                itemName TEXT,
                FOREIGN KEY (userID) REFERENCES characters(userID),
                PRIMARY KEY (userID, slot)
            )''')
        
        # === Creates the monster table ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS monsters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                area TEXT,
                health INTEGER,
                attack INTEGER,
                defense INTEGER,
                xpReward INTEGER,
                type TEXT,
                effect TEXT,
                description TEXT
            )''')
        
        # === Creates the shop items table ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shopItems (
                itemName TEXT PRIMARY KEY,
                buyPrice INTEGER,
                sellPrice INTEGER,
                type TEXT,
                effect TEXT,
                description TEXT
            )''')
        
        # === Creates a table to track the amount of fights the character did ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fightStats (
                userID TEXT PRIMARY KEY,
                totalFights INTEGER DEFAULT 0,
                fightsSinceBoss INTEGER DEFAULT 0,
                lastFightTimestap INTEGER DEFAULT 0,
                FOREIGN KEY (userID) REFERENCES characters(userID)
            )''')
        
        # === A table to track the cooldowns of the skills of the character ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS skillCooldowns (
                userID TEXT,
                skillName TEXT,
                turnsRemaining INTEGER DEFAULT 0,
                PRIMARY KEY (userID, skillName),
                FOREIGN KEY (userID) REFERENCES characters(userID)
            )''')
        
        # === Add a mana colums to already existing characters before i added mana ===
        try:
            self.cursor.execute("ALTER TABLE characters ADD COLUMN mana INTEGER DEFAULT 50")
            self.cursor.execute("ALTER TABLE characters ADD COLUMN maxMana INTEGER DEFAULT 50")
        except sqlite3.OperationalError:
            pass
        
        self.conn.commit()

    # === Creates a new character into the databse ===
    def createCharacter(self, userID: str, name: str):
        try:
            self.cursor.execute(
                "INSERT INTO characters (userID, name) VALUES (?, ?)",
                (userID, name)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"The character with the userID: {userID} already exists.")
            return False
        except sqlite3.Error as e:
            print(f"There was a database error while creating the character: {e}")
            return False
        
    # === Fetches the character data from the database ===
    def getCharacter(self, userID: str) -> dict:
        try:
            self.cursor.execute("SELECT * FROM characters WHERE userID = ?", (userID,))
            result = self.cursor.fetchone()
            if not result:
                return None
            
            colums = [description[0] for description in self.cursor.description]
            return dict(zip(colums, result))
        except sqlite3.Error as e:
            print(f"There was a database error while fetching the character: {e}")

    # === Updates the characters data in the database ===
    def updateCharacter(self, userID: str, updates: dict) -> bool:
        if not updates:
            return True
        
        try:
            setValues = ", ".join([f"{k} = ?" for k in updates.keys()])
            query = f"UPDATE characters SET {setValues} WHERE userID = ?"
            values = list(updates.values()) + [userID]

            self.cursor.execute(query, values)
            self.conn.commit()
            return self.cursor.rowcount > 0 # Only returns True if it actually updated
        except sqlite3.Error as e:
            print(f"There was an error while updating the character with userID: {userID}: {e}")
            return False
        
    # === Deletes a character from the database ===
    def deleteCharacter(self, userID: str) -> bool:
        try:
            self.cursor.execute("DELETE FROM characters WHERE userID = ?", (userID,))
            self.cursor.execute("DELETE FROM inventory WHERE userID = ?", (userID,))
            self.cursor.execute("DELETE FROM equipment WHERE userID = ?", (userID,))
            self.conn.commit()
            return True
        
        except sqlite3.Error as e:
            print("There was an error while delting the character: {e}")
            self.conn.rollback()
            return False
        
    # === Fetches the inventory data of a character ===
    def getInventory(self, userID: str) -> list:
        try:
            self.cursor.execute("SELECT itemName, quantity FROM inventory WHERE userID = ?", (userID,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"There was a database error while fetching the inventory: {e}")
            return []
    
    # === Adds an item to the inventory of a character ===
    def addItem(self, userID: str, itemName: str, quantity: int = 1) -> bool:
        if quantity <= 0:
            print("The quantity must be greater than 0.")
            return False
        
        if not self.getCharacter(userID):
            print(f"The character with userID: {userID} does not exist.")
            return False
        
        try:
            self.cursor.execute("SELECT quantity FROM inventory WHERE userID = ? AND itemName = ?", (userID, itemName))
            existing = self.cursor.fetchone()

            if existing:
                newQuantity = existing[0] + quantity
                self.cursor.execute("UPDATE inventory SET quantity = ? WHERE userID = ? AND itemName = ?", (newQuantity, userID, itemName))
            
            else:
                self.cursor.execute("INSERT INTO inventory (userID, itemName, quantity) VALUES (?, ?, ?)", (quantity, userID, itemName))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"There was an error while adding the item {itemName} to the inventory of {userID}: {e}")
            return False

    # === Removes an item from the inventory of a character ===
    def removeItem(self, userID: str, itemName: str, quantity: int = 1) -> bool:
        if quantity <= 0:
            print("The quantity must be greater than 0.")
            return False
        
        try:
            self.cursor.execute("SELECT quantity FROM inventory WHERE userID = ? and itemName = ?", (userID, itemName))
            result = self.cursor.fetchone()

            if not result:
                print(f"The item {itemName} has not been found in the inventory of {userID}")
                return False
            
            currentQuantity = result[0]

            if currentQuantity < quantity:
                print(f"There is not enough quantity of {itemName} in inventory. You have: {currentQuantity}, need: {quantity}")
                return False
            
            newQuantity = currentQuantity - quantity

            if newQuantity <= 0:
                self.cursor.execute("DELETE FROM inventory WHERE userID = ? AND itemName = ?", (userID, itemName))
            
            else:
                self.cursor.execute("UPDATE inventory SET quantity = ? WHERE userID = ? AND itemName = ?", (newQuantity, userID, itemName))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"There was an error while removing the item {itemName} from the inventory of {userID}: {e}")
            return False

    # === Equips an item to a character ===
    def equipItem(self, userID: str, slot: str, itemName: str) -> bool:
        try:
            self.cursor.execute("INSERT OR REPLACE INTO equipment (userID, slot, itemName) VALUES (?, ?, ?)", (userID, slot, itemName))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"There was an error while equipping the item; {e}")
            return False
        
    # === Gets all the equipment items of a character ===
    def getEquipment(self, userID: str) -> dict[str, str]:
        try:
            self.cursor.execute("SELECT slot, itemName FROM equipment WHERE userID = ?", (userID,))
            return dict(self.cursor.fetchall())
        except sqlite3.Error as e:
            print(f"There was an error while fetching the equipment of {userID}: {e}")
            return {}
        
    # === unequips the item from a character ===
    def unequipItem(self, userID: str, slot: str) -> bool:
        try:
            self.cursor.execute("DELETE FROM equipment WHERE userID = ? AND slot = ?", (userID, slot))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"There was an error while unequipping the item from {userID} in slot {slot}: {e}")
            return False
        
    # === Fighting mechanics management methods ===
    # === Initializes the fighting stat for chacteractes ===
    def initializeFightStats(self, userID: str) -> bool:
        try:
            self.cursor.execute("INSERT OR IGNORE INTO fightStats (userID) VALUES (?)", (userID,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"There was an error initializing fight stats for {userID}: {e}")
            return False
        
    # === Pulls the fight stats from the data base ===
    def getFightStats(self, userID: str) -> dict:
        try:
            self.cursor.execute("SELECT totalFights, fightsSinceBoss, lastFightTimestamp FROM fightStats WHERE userID = ?", (userID,))
            result = self.cursor.fetchone()

            if not result:
                return None
            
            return {
                "totalFights": result[0],
                "fightsSinceBoss": result[1],
                "lastFightTimestamp": result[2]
            }
        except sqlite3.Error as e:
            print(f"There was an error while getting the fights stats for {userID}: {e}")
            return None
        
    # === Updates the fights stats for the user's character ===
    def updateFightStats(self, userID: str, updates: dict) -> bool:
        if not updates:
            return True
        
        try:
            self.initializeFightStats(userID) # <= Makes sure the fight stats recods exists

            setValues = ", ".join([f"{k} = ?" for k in updates.keys()])
            query = f"UPDATE fightStats SET {setValues} WHERE userID = ?"
            values = list(updates.values()) + [userID]

            self.cursor.execute(query, values)
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"There was an error that occured while updating fight stats for {userID}: {e}")
            return False
        
    # === Sets the cooldowns for the skills ===
    def setSkillCooldown(self, userID: str, skillName: str, turns: int) -> bool:
        try:
            self.cursor.execute("INSERT OR REPLACE INTO skillCooldowns (userID, skillName, turnsRemaining) VALUES (?, ?, ?)", (userID, skillName, turns ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"There was an error while setting the skil cooldowns for {userID}: {e}")
            return False
        
    # === Gets the skill cooldowns for the characters ===
    def getSkillCooldown(self, userID: str, skillName: str) -> int:
        try:
            self.cursor.execute("SELECT turnsRemaining FROM skillCooldowns WHERE userID = ? AND skillName = ?", (userID, skillName))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            print(f"There was an error while getting the skill cooldowns for {userID}: {e}")
            return 0
    
    # === Checks if a skill is currently on cooldown ===
    def isSkillOnCooldown(self, userID: str, skillName: str) -> bool:
        return self.getSkillCooldown(userID, skillName) > 0
    
    # === Updates the skill cooldown and reduces it by 1 turn
    def updateSkillCooldown(self, userID: str) -> bool:
        try:
            self.cursor.execute("UPDATE skillCooldowns SET turnsRemaining = turnsRemaining - 1 WHERE userID = ? and turnsRemaining > 0", (userID,))

            self.cursor.execute("DELETE FROM skillCooldowns WHERE userID = ? and turnsRemaining <= 0", (userID,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"There was an error while updating the skill cooldowns for {userID}: {e}")
            return False
        
    # === Gets alss the skill cooldowns for the user ===
    def getALlSkillCooldown(self, userID: str) -> dict:
        try:
            self.cursor.execute("SELECT skillName, turnsRemaining FROM skillCooldowns WHERE userID = ? and turnsRemaining > 0", (userID,))
            return dict(self.cursor.fetchall())
        except sqlite3.Error as e:
            print(f"There was an error while getting all the skill cooldowns for {userID}: {e}")
            return {} 
    
    # === Self note: Add shop management methods here ===

    # === Closes the database connection when the object is deleted ===
    def __del__(self):
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass # <= Ignores errors dring th cleanup proccess