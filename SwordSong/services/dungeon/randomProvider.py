from typing import Protocol, List, Any, Optional
import random as randomModule

class RandomProvider(Protocol):
    def random(self) -> float: # <- Generates a random float
        ...   
    def randint(self, a: int, b: int) -> int: # <- Random integer between a and b
        ...  
    def choice(self, sequence: List[Any]) -> Any: # <- Choose a random element from sequence
        ... 
    def choices(self, population: List[Any], weights: List[float], k: int = 1) -> List[Any]: # <- Choses a sequences in place
        ...
    def shuffle(self, sequence: List[Any]) -> None: # <- Shuffles the sequence in place
        ...
 
class StandardRandomProvider:
    def __init__(self, seed: Optional[int] = None):
        self._random = randomModule.Random(seed)

    def random(self) -> float:
        return self._random.random()
    
    def randint(self, a: int, b: int) -> int:
        return self._random.randint(a, b)
    
    def choice(self, sequence: List[Any]) -> Any:
        return self._random.choice(sequence)
    
    def choices(self, population: List[Any], weights: List[float], k: int = 1) -> List[Any]:
        return self._random.choices(population, weights = weights, k = k)
    
    def shuffle(self, sequence: List[Any]) -> None:
        self._random.shuffle(sequence)