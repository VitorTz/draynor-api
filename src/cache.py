from collections import OrderedDict
from threading import Lock
from threading import RLock
from src.util import singleton
from pydantic import BaseModel
from typing import Callable, TypeVar, Any, Type
import pickle
import time
import sys


class RedisLikeCache:
    _instance = None
    _lock = RLock()

    MAX_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_cache()
            return cls._instance

    def _init_cache(self):
        self.cache = {}
        self.current_size = 0
        self.counter = 0

    def _cleanup_expired(self):
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if v["expires"] < now]
        for k in expired_keys:
            self._evict_key(k)

    def _evict_key(self, key):
        entry = self.cache.pop(key, None)
        if entry:
            self.current_size -= entry["size"]

    def _evict_oldest_until_fit(self):
        # Sorted by insertion order (ts)
        while self.current_size > self.MAX_SIZE_BYTES and self.cache:
            oldest_key = min(self.cache.items(), key=lambda kv: kv[1]["ts"])[0]
            self._evict_key(oldest_key)

    def set(self, key, value, ttl_seconds):
        with self._lock:
            self._cleanup_expired()

            expires = time.time() + ttl_seconds
            serialized = pickle.dumps(value)
            size = len(serialized)
            self.counter += 1
            
            if key in self.cache:
                self._evict_key(key)
            
            self.cache[key] = {
                "value": serialized,
                "expires": expires,
                "size": size,
                "ts": self.counter
            }
            self.current_size += size            
            self._evict_oldest_until_fit()

    def get(self, key):
        with self._lock:
            self._cleanup_expired()

            entry = self.cache.get(key)
            if not entry:
                return None

            if entry["expires"] < time.time():
                self._evict_key(key)
                return None

            return pickle.loads(entry["value"])


T = TypeVar("T", bound=BaseModel)

@singleton
class SizeBasedAPICache:
    
    def __init__(self, max_memory_mb: float = 4.0):        
        self.cache = OrderedDict()
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.current_memory_usage = 0
        self.lock = Lock()

    def _get_deep_size(self, obj, seen=None):        
        size = sys.getsizeof(obj)
        if seen is None:
            seen = set()
        
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        
        seen.add(obj_id)

        if isinstance(obj, dict):
            size += sum([self._get_deep_size(v, seen) + self._get_deep_size(k, seen) for k, v in obj.items()])
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
            size += sum([self._get_deep_size(i, seen) for i in obj])
            
        return size

    def get(self, key: str):        
        with self.lock:
            if key not in self.cache:
                return None
                        
            self.cache.move_to_end(key)
                        
            return self.cache[key][0]

    def set(self, key: str, value):        
        with self.lock:            
            item_size = self._get_deep_size(key) + self._get_deep_size(value)
            
            if item_size > self.max_memory_bytes:
                print(f"⚠️ Item muito grande ({item_size} bytes). Não cacheado.")
                return
            
            if key in self.cache:
                old_size = self.cache[key][1]
                self.current_memory_usage -= old_size
                self.cache.move_to_end(key)
            
            self.cache[key] = (value, item_size)
            self.current_memory_usage += item_size
            
            while self.current_memory_usage > self.max_memory_bytes:                
                evicted_key, (evicted_value, evicted_size) = self.cache.popitem(last=False)
                self.current_memory_usage -= evicted_size                
                print(f"🧹 Removendo '{evicted_key}' para liberar {evicted_size} bytes.")
                
    async def get_or_compute(
        self, 
        key: str, 
        fetch_func: Callable[[], Any], 
        response_model: Type[T]
    ) -> T:                
        cached_data = self.get(key)
        if cached_data:
            print(f"[CACHED] [{key}]")
            return response_model(**cached_data)
        
        result = await fetch_func()
        self.set(key, result.model_dump(mode='json'))
        return result

    def info(self):        
        with self.lock:
            mb_used = self.current_memory_usage / (1024 * 1024)
            return {
                "itens": len(self.cache),
                "uso_bytes": self.current_memory_usage,
                "uso_mb": round(mb_used, 4),
                "max_mb": self.max_memory_bytes / (1024 * 1024)
            }