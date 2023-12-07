import time
from collections import OrderedDict, namedtuple
from threading import Lock
from log import log

Entry = namedtuple('Entry', ['created', 'size', 'content'])

class ProxyCache():
    """
    Manages the cache for the proxy. The cache is implemented as an OrderedDict:
        * keys are URLs
        * values are tuples of (time_created, size, content)
        * ordering is LRU, most recently used is moved to end

    Parameters set on creation are max cache size (in bytes) and TTL (in seconds)
    """
    
    def __init__(self, max_size, ttl):
        self.max_size: int = max_size
        self.ttl: int = ttl
        self.cur_size: int = 0
        self.lock: Lock = Lock()
        self.cache: OrderedDict[str, Entry] = OrderedDict()


    def get(self, url):
        """
        Fetch the content for a URL from the cache. If it exists, return it and
        update the LRU order.
        If it doesn't exist, return None, indicating the client should add it.
        """
        cur_time = time.time()
        if url not in self.cache: # not in cache
            return None
        
        self.lock.acquire()
        entry = self.cache[url]
        if cur_time - entry.created > self.ttl: # in cache but too old: evict
            self.cur_size -= entry.size
            del self.cache[url]
            self.lock.release()
            return None
        else: # in cache and recent enough: update LRU order & return
            self.cache.move_to_end(url)
            self.lock.release()
            return entry.content


    def insert(self, new_url, new_content) -> bool:
        """
        Insert a new entry into the cache, evicting others to make room.
        Eviction policy:
            1. Remove any entries that are too old
            2. Remove the largest least recently used entry and repeat if needed
        """
        cur_time = time.time()
        new_entry = self.make_entry(new_content, cur_time)

        if new_entry.size > self.max_size: # new entry can never fit
            return False

        self.lock.acquire(blocking=True)
        for url, entry in self.cache.items(): # evict expired entries
            if cur_time - entry.created > self.ttl:
                self.cur_size -= entry.size
                del self.cache[url]

        while (new_entry.size + self.cur_size) > self.max_size: # evict LRU
            evicted = self.cache.popitem(last=False)
            self.cur_size -= evicted[1].size

        self.cache[new_url] = new_entry
        self.cur_size += new_entry.size
        self.lock.release()
        return True


    @staticmethod
    def make_entry(content, cur_time) -> Entry:
        """Construct an Entry tuple for a new piece of content."""
        return Entry(created=cur_time,
                     size=len(content),
                     content=content)
