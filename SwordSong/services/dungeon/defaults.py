from .models import RoomType
from .config import RoomData

entranceData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "🚪",
    emojiCleared = "🚪",
    generationWeight = 0.0,
    canBeBranch = False,
    canBeReplaced = False,
)

combatData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "⚔️",
    emojiCleared  = "✅",
    generationWeight = 45.0,
    canBeBranch = True,
    canBeReplaced = True,
)

treasureData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "💰",
    emojiCleared = "📦",
    generationWeight = 20.0,
    canBeBranch = True,
    canBeReplaced = False,
)

trapData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "🕳️",
    emojiCleared = "⚠️",
    generationWeight = 15.0,
    canBeBranch = True,
    canBeReplaced = True,
)

bossData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "👑",
    emojiCleared = "🏆",
    generationWeight = 0.0,
    canBeBranch = False,
    canBeReplaced = False,
)

shopData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "🏪",
    emojiCleared = "🏪",
    generationWeight = 10.0,
    canBeBranch = True,
    canBeReplaced = True,
)

healingData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "💚",
    emojiCleared = "💚",
    generationWeight = 10.0,
    canBeBranch = True,
    canBeReplaced = True,
)

puzzleData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "🧩",
    emojiCleared = "✨",
    generationWeight = 5.0,
    canBeBranch = True,
    canBeReplaced = True,
)

emptyData = RoomData(
    emojiUnvisited = "⬛",
    emojiVisited = "⬜",
    emojiCleared = "⬜",
    generationWeight = 40.0,
    canBeBranch = True,
    canBeReplaced = True,
)

# Central dict for default mapping
defaultRoomData = {
    RoomType.ENTRANCE: entranceData,
    RoomType.COMBAT:   combatData,
    RoomType.TREASURE: treasureData,
    RoomType.TRAP:     trapData,
    RoomType.BOSS:     bossData,
    RoomType.SHOP:     shopData,
    RoomType.HEALING:  healingData,
    RoomType.PUZZLE:   puzzleData,
    RoomType.EMPTY:    emptyData,
}
