from enum import Enum
from dataclasses import dataclass
from typing import Dict
from .config import RoomData

class RoomType(Enum):
    ENTRANCE = "entrance"
    COMBAT = "combat"
    TREASURE = "treasure"
    TRAP = "trap"
    BOSS = "boss"
    SHOP = "shop"
    HEALING = "healing"
    PUZZLE = "puzzle"
    EMPTY = "empty"

@dataclass(frozen = True)
class Position:
    x: int
    y: int

    def neighbors(self) -> Dict[str, "Position"]:
        return {
            "north": Position(self.x, self.y - 1),
            "south": Position(self.x, self.y + 1),
            "east": Position(self.x + 1, self.y),
            "west": Position(self.x - 1, self.y)
        }

class Room:
    def __init__(self, roomType: RoomType, position: Position, config: RoomData):
        self.roomType = roomType
        self.position = position
        self.config = config
        self.visited = False
        self.cleared = False
        self.connections: Dict[str, bool] = {d: False for d in ("north", "south", "east", "west")}

    def visit(self) -> None:
        self.visited = True
    
    def clear(self) -> None:
        self.cleared = True
    
    def setConnection(self, direction: str, canTravel: bool) -> None:
        if direction in self.connections:
            self.connections[direction] = canTravel

    def getEmoji(self) -> str:
        if not self.visited:
            return self.config.emojiUnvisited
        elif self.cleared:
            return self.config.emojiCleared
        else:
            return self.config.emojiVisited    
