from collections import OrderedDict, Counter
from threading import Lock
from typing import Dict, List, Tuple, Union

# Define a base class for the eviction policies
class EvictionPolicy:
    def __init__(self, size: int):
        self.size = size
        self.cache = OrderedDict()
        self.lock = Lock()

    def get(self, key: str) -> Union[str, None]:
        raise NotImplementedError

    def put(self, key: str, value: str) -> None:
        raise NotImplementedError

    def remove(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]

    def __str__(self):
        return str(self.cache)

# LRU Policy
class LRUPolicy(EvictionPolicy):
    def get(self, key: str) -> Union[str, None]:
        with self.lock:
            if key in self.cache:
                # Move to end to mark it as recently used
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def put(self, key: str, value: str) -> None:
        with self.lock:
            if key in self.cache:
                # Move to end to mark it as recently used
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.size:
                # Remove the first item (least recently used)
                self.cache.popitem(last=False)
            self.cache[key] = value

# LFU Policy
class LFUPolicy(EvictionPolicy):
    def __init__(self, size: int):
        super().__init__(size)
        self.frequency = Counter()

    def get(self, key: str) -> Union[str, None]:
        with self.lock:
            if key in self.cache:
                self.frequency[key] += 1
                return self.cache[key]
            return None

    def put(self, key: str, value: str) -> None:
        with self.lock:
            if key in self.cache:
                self.cache[key] = value
                self.frequency[key] += 1
            elif len(self.cache) >= self.size:
                # Evict the least frequently used item
                lfu_key = min(self.frequency, key=lambda k: self.frequency[k])
                self.cache.pop(lfu_key)
                del self.frequency[lfu_key]
            self.cache[key] = value
            self.frequency[key] = 1

# Multilevel Cache System
class MultilevelCacheSystem:
    def __init__(self):
        self.levels: List[EvictionPolicy] = []
        self.lock = Lock()

    def addCacheLevel(self, size: int, evictionPolicy: str) -> None:
        with self.lock:
            if evictionPolicy == 'LRU':
                policy = LRUPolicy(size)
            elif evictionPolicy == 'LFU':
                policy = LFUPolicy(size)
            else:
                raise ValueError(f"Unsupported eviction policy: {evictionPolicy}")
            self.levels.append(policy)

    def removeCacheLevel(self, level: int) -> None:
        with self.lock:
            if 0 <= level < len(self.levels):
                self.levels.pop(level)
            else:
                raise IndexError("Cache level out of range")

    def get(self, key: str) -> Union[str, None]:
        with self.lock:
            for level in self.levels:
                value = level.get(key)
                if value is not None:
                    # Move data up to higher levels
                    self._move_up(key, value)
                    return value
            return None

    def put(self, key: str, value: str) -> None:
        with self.lock:
            # Insert data into L1 cache
            self.levels[0].put(key, value)
            self._move_up(key, value)

    def _move_up(self, key: str, value: str) -> None:
        for i in range(1, len(self.levels)):
            if self.levels[i].get(key) is not None:
                self.levels[i].remove(key)
                self.levels[i].put(key, value)

    def displayCache(self) -> None:
        with self.lock:
            for i, level in enumerate(self.levels):
                print(f"L{i + 1} Cache: {level}")

# Sample Test Cases
if __name__ == "__main__":
    cache_system = MultilevelCacheSystem()
    
    print("Adding LRU Cache Level (Size 3)...")
    cache_system.addCacheLevel(3, 'LRU')
    
    print("Adding LFU Cache Level (Size 2)...")
    cache_system.addCacheLevel(2, 'LFU')
    
    print("Inserting data...")
    cache_system.put('a', 'value_a')
    cache_system.put('b', 'value_b')
    cache_system.put('c', 'value_c')  # Should evict 'a' from LRU level
    
    print("Retrieving data...")
    print(f"Get 'a': {cache_system.get('a')}")  # Should print None since 'a' is evicted
    print(f"Get 'b': {cache_system.get('b')}")  # Should print 'value_b'
    print(f"Get 'c': {cache_system.get('c')}")  # Should print 'value_c'
    
    print("Displaying Cache...")
    cache_system.displayCache()
    
    print("Removing LRU Cache Level...")
    cache_system.removeCacheLevel(0)  # Removing LRU level
    
    print("Displaying Cache after removal...")
    cache_system.displayCache()

    print("Adding another LRU Cache Level (Size 2)...")
    cache_system.addCacheLevel(2, 'LRU')
    
    print("Inserting more data...")
    cache_system.put('d', 'value_d')
    cache_system.put('e', 'value_e')  # Should evict 'b' from LFU level
    
    print("Retrieving data...")
    print(f"Get 'b': {cache_system.get('b')}")  # Should print None since 'b' is evicted
    print(f"Get 'd': {cache_system.get('d')}")  # Should print 'value_d'
    print(f"Get 'e': {cache_system.get('e')}")  # Should print 'value_e'
    
    print("Displaying Cache...")
    cache_system.displayCache()
