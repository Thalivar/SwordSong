import sqlite3
from pathlib import Path

class Database:
    def __init__(self):
        self.db_path = Path(__file__).parent / "game.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.setup_database()

    # === Seting up the database ===
    def setup_database(self):

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
        
        self.conn.commit()

    # === Creates a new character into the databse ===
    def createCharacter(self, userID: str, name: str):
        try:
            self.cursor.execute(
                "INSERT INTO characters (userID, name) VALUEs (?, ?)",
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
            self.cursor.execute("SELECT quantity FROM inventory WHERE userID + ? AND itemName = ?", (userID, itemName))
            existing = self.cursor.fetchone()

            if existing:
                newQuantity = existing[0] + quantity
                self.cursor.execute("UPDATE inventory SET quantity = ? WHERE userID = ? AND itemName = ?", (newQuantity, userID, itemName))
            
            else:
                self.cursor.execute("INSERT INTO inventory (userID, itemName, quantity) VALUES (?, ?, ?)", (newQuantity, userID, itemName))
            
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
        
    # === Closes the database connection when the object is deleted ===
    def __del__(self):
        self.conn.close()