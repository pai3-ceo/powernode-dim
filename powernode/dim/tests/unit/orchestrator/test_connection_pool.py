"""
Unit tests for Connection Pool
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'orchestrator' / 'src'))

from connection_pool import ConnectionPool


@pytest.mark.asyncio
async def test_connection_pool_initialization(test_config):
    """Test connection pool initialization"""
    pool = ConnectionPool(test_config)
    
    assert pool.max_connections == 10
    assert pool.connection_timeout == 30
    assert len(pool.pools) == 0


@pytest.mark.asyncio
async def test_get_channel(test_config):
    """Test getting channel from pool"""
    pool = ConnectionPool(test_config)
    
    with patch('connection_pool.grpc.aio.insecure_channel') as mock_channel:
        mock_ch = Mock()
        mock_channel.return_value = mock_ch
        
        channel = await pool.get_channel('localhost:50051')
        
        assert channel is not None
        assert 'localhost:50051' in pool.pools


@pytest.mark.asyncio
async def test_return_channel(test_config):
    """Test returning channel to pool"""
    pool = ConnectionPool(test_config)
    
    with patch('connection_pool.grpc.aio.insecure_channel') as mock_channel:
        mock_ch = Mock()
        mock_channel.return_value = mock_ch
        
        channel = await pool.get_channel('localhost:50051')
        await pool.return_channel(channel)
        
        # Channel should be marked as available
        metadata = pool.channel_metadata.get(channel)
        assert metadata is not None
        assert metadata['available'] is True


@pytest.mark.asyncio
async def test_connection_pool_reuse(test_config):
    """Test connection reuse"""
    pool = ConnectionPool(test_config)
    
    with patch('connection_pool.grpc.aio.insecure_channel') as mock_channel:
        mock_ch = Mock()
        mock_channel.return_value = mock_ch
        
        # Get channel twice
        ch1 = await pool.get_channel('localhost:50051')
        await pool.return_channel(ch1)
        ch2 = await pool.get_channel('localhost:50051')
        
        # Should reuse same channel
        assert ch1 == ch2


@pytest.mark.asyncio
async def test_connection_pool_max_size(test_config):
    """Test connection pool max size"""
    config = test_config.copy()
    config['connection_pool'] = {'max_connections_per_endpoint': 2}
    
    pool = ConnectionPool(config)
    
    with patch('connection_pool.grpc.aio.insecure_channel') as mock_channel:
        mock_ch = Mock()
        mock_channel.return_value = mock_ch
        
        # Get max connections
        ch1 = await pool.get_channel('localhost:50051')
        ch2 = await pool.get_channel('localhost:50051')
        
        # Pool should be full
        assert len(pool.pools['localhost:50051']) == 2

