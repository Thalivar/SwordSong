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
                health INTEGET DEFAULT 100,
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
                usedID TEXT,
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
                butPrice INTEGER,
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
        
    # === Fetches the character data from the database ===
    def getCharacter(self, userID: str) -> dict:
        self.cursor.execute("SELECT * FROM characters WHERE userID = ?", (userID,))
        result = self.cursor.fetchone()
        if not result:
            return None
        
        colums = [description[0] for description in self.cursor.description]
        return dict(zip(colums, result))

    # === Updates the characters data in the database ===
    def updateCharacter(self, userID: str, updates: dict) -> bool:
        setValues = ", ".join([f"{k} = ?" for  in updates.keys()])
        query = f"UPDATE characters SET {setValues} WHERE userID = ?"
        values = list(updates.values()) + [userID]

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            return True
        except sqlite3.Error:
            print(f"There was an error updating the character with userID {userID}.")
            return False