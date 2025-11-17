"""
Rate Limiter - Implements rate limiting for API requests
"""

import time
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(self, config: Dict):
        """
        Initialize rate limiter
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Rate limiting configuration
        self.default_rate = config.get('rate_limiting', {}).get('default_rate_per_minute', 60)
        self.burst_size = config.get('rate_limiting', {}).get('burst_size', 10)
        self.enabled = config.get('rate_limiting', {}).get('enabled', True)
        
        # Per-user rate limits
        self.user_limits: Dict[str, Dict] = config.get('rate_limiting', {}).get('user_limits', {})
        
        # Token buckets: identifier -> bucket state
        self.buckets: Dict[str, Dict] = defaultdict(lambda: {
            'tokens': self.burst_size,
            'last_refill': time.time()
        })
        
        logger.info("Rate Limiter initialized")
    
    async def check_rate_limit(self, identifier: str, cost: int = 1) -> tuple[bool, Optional[str]]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: User ID or IP address
            cost: Cost of the request (default: 1)
            
        Returns:
            (allowed, error_message)
        """
        if not self.enabled:
            return True, None
        
        # Get rate limit for identifier
        rate = self.user_limits.get(identifier, {}).get('rate_per_minute', self.default_rate)
        burst = self.user_limits.get(identifier, {}).get('burst_size', self.burst_size)
        
        # Get or create bucket
        bucket_key = f"{identifier}"
        bucket = self.buckets[bucket_key]
        
        # Refill tokens
        now = time.time()
        elapsed = now - bucket['last_refill']
        tokens_to_add = (rate / 60.0) * elapsed  # Tokens per second
        bucket['tokens'] = min(burst, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
        
        # Check if enough tokens
        if bucket['tokens'] >= cost:
            bucket['tokens'] -= cost
            return True, None
        else:
            retry_after = int((cost - bucket['tokens']) / (rate / 60.0))
            error_msg = f"Rate limit exceeded. Retry after {retry_after} seconds"
            logger.warning(f"Rate limit exceeded for {identifier}: {error_msg}")
            return False, error_msg
    
    def reset_bucket(self, identifier: str):
        """Reset rate limit bucket for identifier"""
        bucket_key = f"{identifier}"
        if bucket_key in self.buckets:
            del self.buckets[bucket_key]
            logger.debug(f"Reset rate limit bucket for {identifier}")
    
    def get_rate_limit_status(self, identifier: str) -> Dict:
        """
        Get current rate limit status for identifier
        
        Args:
            identifier: User ID or IP address
            
        Returns:
            Status dictionary
        """
        bucket_key = f"{identifier}"
        bucket = self.buckets.get(bucket_key, {'tokens': 0, 'last_refill': time.time()})
        
        rate = self.user_limits.get(identifier, {}).get('rate_per_minute', self.default_rate)
        burst = self.user_limits.get(identifier, {}).get('burst_size', self.burst_size)
        
        return {
            'identifier': identifier,
            'tokens_available': bucket['tokens'],
            'tokens_max': burst,
            'rate_per_minute': rate,
            'reset_in_seconds': int((burst - bucket['tokens']) / (rate / 60.0)) if bucket['tokens'] < burst else 0
        }

