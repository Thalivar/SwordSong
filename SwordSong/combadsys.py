import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class combSystem:
    def __init__(self, db, areasData, itemsData):
        self.db = db
        self.areas = areasData
        self.item = itemsData
        self.activeCombats = []

        self.rarityWeight = {
            "common": 60,
            "uncommonn": 25,
            "rare": 12,
            "legendary": 3
        }

        