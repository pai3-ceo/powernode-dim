"""
Node Discovery - Discovers nodes via IPFS Pubsub heartbeats
"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from .node_registry import NodeRegistryManager
from .ipfs.state_manager import IPFSStateManager
from .models.node_info import NodeInfo
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class NodeDiscovery:
    """Discovers nodes via IPFS Pubsub and updates registry"""
    
    def __init__(self, registry_manager: NodeRegistryManager, state_manager: IPFSStateManager, config: Dict):
        """
        Initialize node discovery
        
        Args:
            registry_manager: Node registry manager
            state_manager: IPFS state manager
            config: Configuration dictionary
        """
        self.registry_manager = registry_manager
        self.state_manager = state_manager
        self.config = config
        self.heartbeat_timeout = config.get('node_discovery', {}).get('heartbeat_timeout_seconds', 120)
        self.discovered_nodes: Dict[str, datetime] = {}  # node_id -> last_seen
        self.running = False
        
        logger.info("Node Discovery initialized")
    
    async def start(self):
        """Start node discovery service"""
        if self.running:
            return
        
        self.running = True
        
        # Subscribe to node heartbeats
        await self.state_manager.subscribe_to_node_heartbeats(self._handle_heartbeat)
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_stale_nodes())
        
        logger.info("Node Discovery started")
    
    async def stop(self):
        """Stop node discovery service"""
        self.running = False
        logger.info("Node Discovery stopped")
    
    async def _handle_heartbeat(self, message: Dict):
        """Handle node heartbeat from Pubsub"""
        try:
            node_id = message.get('node_id')
            if not node_id:
                return
            
            # Update discovered nodes
            self.discovered_nodes[node_id] = datetime.now()
            
            # Update registry with heartbeat
            await self.registry_manager.update_node_heartbeat(node_id, message)
            
            logger.debug(f"Received heartbeat from node {node_id}")
            
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}", exc_info=True)
    
    async def _cleanup_stale_nodes(self):
        """Periodically clean up nodes that haven't sent heartbeats"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.now()
                timeout = timedelta(seconds=self.heartbeat_timeout)
                
                # Find stale nodes
                stale_nodes = []
                for node_id, last_seen in self.discovered_nodes.items():
                    if now - last_seen > timeout:
                        stale_nodes.append(node_id)
                
                # Remove stale nodes from discovered list
                for node_id in stale_nodes:
                    del self.discovered_nodes[node_id]
                    logger.info(f"Node {node_id} marked as stale (no heartbeat)")
                
                # Optionally update registry to mark nodes as inactive
                # (We keep them in registry but mark status)
                registry = await self.registry_manager.get_registry()
                for node in registry.nodes:
                    if node.node_id in stale_nodes:
                        if node.status == 'active':
                            node.status = 'inactive'
                            logger.info(f"Marked node {node_id} as inactive")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)
    
    async def discover_nodes(self) -> List[NodeInfo]:
        """
        Discover active nodes
        
        Returns:
            List of discovered active nodes
        """
        # Get active nodes from registry
        active_nodes = await self.registry_manager.get_active_nodes()
        
        # Filter to only recently discovered nodes
        now = datetime.now()
        timeout = timedelta(seconds=self.heartbeat_timeout)
        
        discovered = []
        for node in active_nodes:
            if node.node_id in self.discovered_nodes:
                last_seen = self.discovered_nodes[node.node_id]
                if now - last_seen < timeout:
                    discovered.append(node)
        
        return discovered
    
    async def wait_for_node(self, node_id: str, timeout: int = 60) -> bool:
        """
        Wait for a specific node to appear
        
        Args:
            node_id: Node identifier to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if node discovered, False if timeout
        """
        start_time = datetime.now()
        timeout_delta = timedelta(seconds=timeout)
        
        while datetime.now() - start_time < timeout_delta:
            # Check if node is in discovered nodes
            if node_id in self.discovered_nodes:
                return True
            
            # Check registry
            node = await self.registry_manager.get_node(node_id)
            if node and node.status == 'active':
                return True
            
            await asyncio.sleep(2)  # Check every 2 seconds
        
        return False

