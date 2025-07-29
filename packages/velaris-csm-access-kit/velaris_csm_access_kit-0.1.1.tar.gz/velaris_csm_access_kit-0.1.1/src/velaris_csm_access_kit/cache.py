import time
import logging

logger = logging.getLogger(__name__)

class TTLCache:
    def __init__(self, ttl):
        self.cache = {}
        # Let's keep it simple and use same TTL for all tokens
        self.ttl = ttl  # in seconds
    
    def set(self, key, value):
        expiry = time.time() + self.ttl
        self.cache[key] = (value, expiry)
    
    def get(self, key):
        value, expiry = self.cache.get(key, (None, 0))
        if time.time() < expiry:
            logger.debug(f"Token cache hit for {key}")
            return value
        else:
            self.cache.pop(key, None)  # Remove expired token
            return None
