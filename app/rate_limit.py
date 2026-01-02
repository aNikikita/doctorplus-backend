"""
Rate limiting for Doctor+ Backend
In-memory implementation for MVP (consider Redis for production scale)
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from .config import Config


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.
    Tracks requests per IP address.
    """
    
    def __init__(self, rpm: int):
        self.rpm = rpm
        self.window_size = 60  # 1 minute window
        # Store: {ip: [(timestamp, ...), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
    
    def check_rate_limit(self, client_ip: str) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Returns:
            (allowed, remaining, reset_timestamp)
        """
        now = time.time()
        window_start = now - self.window_size
        
        # Clean old requests outside window
        requests = self._requests[client_ip]
        requests = [ts for ts in requests if ts > window_start]
        self._requests[client_ip] = requests
        
        # Check limit
        current_count = len(requests)
        allowed = current_count < self.rpm
        remaining = max(0, self.rpm - current_count)
        
        # Calculate reset time (end of current window)
        reset_time = int(now + self.window_size)
        
        if allowed:
            # Record this request
            self._requests[client_ip].append(now)
        
        return allowed, remaining, reset_time


# Global rate limiter instance
_rate_limiter = RateLimiter(rpm=Config.DOCTORPLUS_RPM)


def check_rate_limit(client_ip: str) -> Tuple[bool, int, int]:
    """
    Check rate limit for client IP.
    Returns (allowed, remaining, reset_timestamp)
    """
    return _rate_limiter.check_rate_limit(client_ip)
