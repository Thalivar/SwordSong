from dataclasses import dataclass, field
from typing import Dict
from .models import RoomType
from .defaults import defaultRoomData

@dataclass
class RoomData:
    emojiUnvisited: str
    emojiVisited: str 
    emojiCleared: str
    generationWeight: float 
    canBeBranch: bool
    canBeReplaced: bool 

@dataclass
class DungeonConfig:
    width: int = 9
    height: int = 7
    roomData: Dict[RoomType, RoomData] = field(default_factory = dict)

    def __post_init__(self):
        if not self.roomData:
            from .defaults import defaultRoomData
            self.roomData = defaultRoomData.copy()

