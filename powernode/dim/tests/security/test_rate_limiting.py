"""
Security tests for rate limiting
"""

import pytest
import asyncio
from unittest.mock import Mock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'orchestrator' / 'src'))

from rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_initialization():
    """Test rate limiter initialization"""
    config = {
        'rate_limiting': {
            'enabled': True,
            'default_rate_per_minute': 60,
            'burst_size': 10
        }
    }
    
    limiter = RateLimiter(config)
    
    assert limiter.enabled is True
    assert limiter.default_rate == 60
    assert limiter.burst_size == 10


@pytest.mark.asyncio
async def test_rate_limit_enforcement():
    """Test rate limit enforcement"""
    config = {
        'rate_limiting': {
            'enabled': True,
            'default_rate_per_minute': 10,  # 10 per minute
            'burst_size': 5
        }
    }
    
    limiter = RateLimiter(config)
    
    # Should allow burst
    for i in range(5):
        allowed, _ = await limiter.check_rate_limit('test-user')
        assert allowed is True
    
    # Next request should be rate limited
    allowed, error_msg = await limiter.check_rate_limit('test-user')
    assert allowed is False
    assert 'Rate limit exceeded' in error_msg


@pytest.mark.asyncio
async def test_per_user_rate_limits():
    """Test per-user rate limits"""
    config = {
        'rate_limiting': {
            'enabled': True,
            'default_rate_per_minute': 60,
            'burst_size': 10,
            'user_limits': {
                'premium-user': {
                    'rate_per_minute': 120,
                    'burst_size': 20
                }
            }
        }
    }
    
    limiter = RateLimiter(config)
    
    # Premium user should have higher limit
    for i in range(20):
        allowed, _ = await limiter.check_rate_limit('premium-user')
        assert allowed is True
    
    # Regular user should have default limit
    for i in range(10):
        allowed, _ = await limiter.check_rate_limit('regular-user')
        assert allowed is True


@pytest.mark.asyncio
async def test_rate_limit_status():
    """Test rate limit status API"""
    config = {
        'rate_limiting': {
            'enabled': True,
            'default_rate_per_minute': 60,
            'burst_size': 10
        }
    }
    
    limiter = RateLimiter(config)
    
    # Use some tokens
    await limiter.check_rate_limit('test-user')
    await limiter.check_rate_limit('test-user')
    
    status = limiter.get_rate_limit_status('test-user')
    
    assert status['identifier'] == 'test-user'
    assert status['tokens_available'] < 10
    assert status['tokens_max'] == 10
    assert status['rate_per_minute'] == 60


@pytest.mark.asyncio
async def test_rate_limit_reset():
    """Test rate limit bucket reset"""
    config = {
        'rate_limiting': {
            'enabled': True,
            'default_rate_per_minute': 60,
            'burst_size': 10
        }
    }
    
    limiter = RateLimiter(config)
    
    # Use tokens
    await limiter.check_rate_limit('test-user')
    
    # Reset
    limiter.reset_bucket('test-user')
    
    # Should have full tokens again
    status = limiter.get_rate_limit_status('test-user')
    assert status['tokens_available'] == 10

