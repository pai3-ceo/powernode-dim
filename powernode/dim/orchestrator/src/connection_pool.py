"""
Connection Pool - Manages gRPC connections to daemons and pattern engines
"""

import asyncio
import grpc
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class ConnectionPool:
    """Manages pooled gRPC connections"""
    
    def __init__(self, config: Dict):
        """
        Initialize connection pool
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.max_connections = config.get('connection_pool', {}).get('max_connections_per_endpoint', 10)
        self.connection_timeout = config.get('connection_pool', {}).get('connection_timeout_seconds', 30)
        self.idle_timeout = timedelta(seconds=config.get('connection_pool', {}).get('idle_timeout_seconds', 300))
        
        # Connection pools: endpoint -> list of channels
        self.pools: Dict[str, list] = defaultdict(list)
        self.channel_metadata: Dict[grpc.aio.Channel, Dict] = {}  # channel -> metadata
        
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()
        
        logger.info("Connection Pool initialized")
    
    async def get_channel(self, endpoint: str, secure: bool = False) -> grpc.aio.Channel:
        """
        Get or create gRPC channel from pool
        
        Args:
            endpoint: Endpoint address (host:port)
            secure: Whether to use secure connection (TLS)
            
        Returns:
            gRPC channel
        """
        async with self.lock:
            # Check for available channel in pool
            if endpoint in self.pools:
                for channel in self.pools[endpoint]:
                    metadata = self.channel_metadata.get(channel)
                    if metadata and metadata.get('available', True):
                        # Check if channel is still healthy
                        if await self._is_channel_healthy(channel):
                            metadata['available'] = False
                            metadata['last_used'] = datetime.now()
                            logger.debug(f"Reusing channel to {endpoint}")
                            return channel
                        else:
                            # Remove unhealthy channel
                            await self._remove_channel(endpoint, channel)
            
            # Create new channel if pool not full
            if len(self.pools[endpoint]) < self.max_connections:
                channel = await self._create_channel(endpoint, secure)
                self.pools[endpoint].append(channel)
                self.channel_metadata[channel] = {
                    'available': False,
                    'created_at': datetime.now(),
                    'last_used': datetime.now(),
                    'endpoint': endpoint
                }
                logger.debug(f"Created new channel to {endpoint}")
                return channel
            
            # Pool is full, wait for available channel or create temporary
            logger.warning(f"Connection pool full for {endpoint}, creating temporary channel")
            return await self._create_channel(endpoint, secure)
    
    async def return_channel(self, channel: grpc.aio.Channel):
        """
        Return channel to pool
        
        Args:
            channel: Channel to return
        """
        async with self.lock:
            metadata = self.channel_metadata.get(channel)
            if metadata:
                metadata['available'] = True
                metadata['last_used'] = datetime.now()
                logger.debug(f"Returned channel to pool: {metadata.get('endpoint')}")
    
    async def _create_channel(self, endpoint: str, secure: bool) -> grpc.aio.Channel:
        """Create new gRPC channel"""
        options = [
            ('grpc.keepalive_time_ms', 30000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', True),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.min_ping_interval_without_data_ms', 300000),
        ]
        
        if secure:
            # TODO: Add TLS credentials when implemented
            channel = grpc.aio.insecure_channel(endpoint, options=options)
        else:
            channel = grpc.aio.insecure_channel(endpoint, options=options)
        
        return channel
    
    async def _is_channel_healthy(self, channel: grpc.aio.Channel) -> bool:
        """Check if channel is healthy"""
        try:
            state = channel.get_state()
            return state == grpc.ChannelConnectivity.READY or state == grpc.ChannelConnectivity.IDLE
        except Exception:
            return False
    
    async def _remove_channel(self, endpoint: str, channel: grpc.aio.Channel):
        """Remove channel from pool"""
        if channel in self.pools[endpoint]:
            self.pools[endpoint].remove(channel)
        if channel in self.channel_metadata:
            del self.channel_metadata[channel]
        await channel.close()
        logger.debug(f"Removed unhealthy channel to {endpoint}")
    
    async def cleanup_idle_connections(self):
        """Clean up idle connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                async with self.lock:
                    now = datetime.now()
                    to_remove = []
                    
                    for channel, metadata in self.channel_metadata.items():
                        if metadata.get('available', False):
                            last_used = metadata.get('last_used')
                            if last_used and now - last_used > self.idle_timeout:
                                to_remove.append((metadata.get('endpoint'), channel))
                    
                    for endpoint, channel in to_remove:
                        await self._remove_channel(endpoint, channel)
                        logger.debug(f"Removed idle connection to {endpoint}")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)
    
    async def close_all(self):
        """Close all connections in pool"""
        async with self.lock:
            for endpoint, channels in self.pools.items():
                for channel in channels:
                    try:
                        await channel.close()
                    except Exception as e:
                        logger.warning(f"Error closing channel to {endpoint}: {e}")
            
            self.pools.clear()
            self.channel_metadata.clear()
            logger.info("All connections closed")

