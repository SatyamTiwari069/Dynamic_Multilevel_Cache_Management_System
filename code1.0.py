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
            print(f"Added Cache Level with size {size} and eviction policy {evictionPolicy}")

    def removeCacheLevel(self, level: int) -> None:
        with self.lock:
            if 0 <= level < len(self.levels):
                self.levels.pop(level)
                print(f"Removed Cache Level {level + 1}")
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
            print(f"Inserted {key} into L1 cache")

    def _move_up(self, key: str, value: str) -> None:
        for i in range(1, len(self.levels)):
            if self.levels[i].get(key) is not None:
                self.levels[i].remove(key)
                self.levels[i].put(key, value)

    def displayCache(self) -> None:
        with self.lock:
            for i, level in enumerate(self.levels):
                print(f"L{i + 1} Cache: {level}")

def main():
    cache_system = MultilevelCacheSystem()
    
    while True:
        print("\nOptions:")
        print("1. Add Cache Level")
        print("2. Remove Cache Level")
        print("3. Put Data")
        print("4. Get Data")
        print("5. Display Cache")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")

        if choice == '1':
            size = int(input("Enter cache size: "))
            evictionPolicy = input("Enter eviction policy (LRU/LFU): ")
            cache_system.addCacheLevel(size, evictionPolicy)
        elif choice == '2':
            level = int(input("Enter cache level to remove (1 for L1, 2 for L2, etc.): ")) - 1
            cache_system.removeCacheLevel(level)
        elif choice == '3':
            key = input("Enter key: ")
            value = input("Enter value: ")
            cache_system.put(key, value)
        elif choice == '4':
            key = input("Enter key to get: ")
            value = cache_system.get(key)
            if value is not None:
                print(f"Value for key '{key}': {value}")
            else:
                print(f"Key '{key}' not found.")
        elif choice == '5':
            cache_system.displayCache()
        elif choice == '6':
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    main()
