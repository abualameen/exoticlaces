# lacesstore/rate_limit.py
from django.core.cache import cache
import time

class RateLimiter:
    """Simple rate limiter to stop bots"""
    
    def __init__(self, limit=30, window=60):  # 30 requests per minute
        self.limit = limit
        self.window = window
    
    def is_allowed(self, key):
        """Check if request is allowed"""
        current = int(time.time())
        cache_key = f"rate_limit_{key}"
        
        # Get existing requests
        requests = cache.get(cache_key, [])
        
        # Clean old requests
        requests = [t for t in requests if current - t < self.window]
        
        # Check limit
        if len(requests) >= self.limit:
            return False
        
        # Add current request
        requests.append(current)
        cache.set(cache_key, requests, timeout=self.window + 10)
        
        return True