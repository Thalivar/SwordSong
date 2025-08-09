import random
from typing import Dict, Optional
from dataclasses import dataclass
from .config import DungeonConfig
from .randomProvider import StandardRandomProvider, RandomProvider
from .models import Position, Room, RoomType

@dataclass
class MiniDungeon:
    size: int = 4
    config: DungeonConfig = None
    rng: RandomProvider = None
    rooms: Dict[Position, Room] = None
    playerPos: Position = None

    def __post_init__(self):
        if self.config is None:
            self.config = DungeonConfig(width = self.size, height = self.size)
        if self.rng is None:
            self.rng = StandardRandomProvider()
        self.generateGrid()
    
    def generateGrid(self):
        self.rooms = {}
        y0 = self.rng.randint(1, self.size - 2)
        y1 = self.rng.randint(1, self.size - 2)
        entrance = Position(0, y0)
        treasure = Position(self.size - 1, y1)
        roomData = self.config.roomData
        self.rooms[entrance] = Room(RoomType.ENTRANCE, entrance, roomData(RoomType.ENTRANCE))
        self.rooms[treasure] = Room(RoomType.TREASURE, treasure, roomData(RoomType.TREASURE))
        self.playerPos = entrance
        self.rooms[entrance].visit()

        for x in range(1, self.size - 1):
            for y in range(1, self.size - 1):
                pos = Position(x, y)
                roomType = self.rng.choices(
                    [RoomType.COMBAT, RoomType.TRAP, RoomType.PUZZLE, RoomType.EMPTY],
                    weights = [40, 15, 10, 35]
                )[0]
                configRoomData = self.config.roomData[roomType]
                self.rooms[pos] = Room(roomType, pos, configRoomData)
        
        for pos, room in list(self.rooms.items()):
            for direction, neighbor in pos.neighbors().items():
                if neighbor in self.rooms:
                    room.setConnection(direction, True)
    
    def movePlayer(self, direction: str) -> bool:
        current = self.playerPos
        room = self.rooms.get(current)
        if not room or not room.connections.get(direction, False):
            return False
        
        target = current.neighbors()[direction]
        if not target in self.rooms:
            self.playerPos = target
            self.rooms[target].visit()
            return True
        return False
    
    @property
    def currentRoom(self) -> str:
        out = []
        for y in range(self.size):
            line = ""
            for x in range(self.size):
                pos = Position(x, y)
                if pos == self.playerPos:
                    line += "👤"
                elif pos in self.rooms and self.rooms[pos].visited:
                    line += self.rooms[pos].getEmoji()
                else:
                    line += "🟫"
            out.append(line)
        return "\n".join(out)