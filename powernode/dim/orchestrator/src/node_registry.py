"""
Node Registry - Manages node registration and discovery via IPFS/IPNS
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .models.node_info import NodeInfo, NodeRegistry
from .ipfs.state_manager import IPFSStateManager
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class NodeRegistryManager:
    """Manages node registry via IPNS"""
    
    def __init__(self, state_manager: IPFSStateManager, config: Dict):
        """
        Initialize node registry manager
        
        Args:
            state_manager: IPFS state manager
            config: Configuration dictionary
        """
        self.state_manager = state_manager
        self.config = config
        self.registry_ipns = config.get('ipfs', {}).get('registry_ipns')
        self.heartbeat_timeout = config.get('node_registry', {}).get('heartbeat_timeout_seconds', 120)
        self.local_cache: Optional[NodeRegistry] = None
        self.last_update: Optional[datetime] = None
        self.cache_ttl = timedelta(seconds=30)  # Cache for 30 seconds
        
        logger.info("Node Registry Manager initialized")
    
    async def register_node(self, node_info: NodeInfo) -> str:
        """
        Register a node in the registry
        
        Args:
            node_info: Node information
            
        Returns:
            IPNS name where registry is published
        """
        try:
            # Load current registry
            registry = await self.get_registry()
            
            # Add or update node
            existing_index = None
            for i, node in enumerate(registry.nodes):
                if node.node_id == node_info.node_id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Update existing node
                registry.nodes[existing_index] = node_info
                logger.info(f"Updated node {node_info.node_id} in registry")
            else:
                # Add new node
                registry.nodes.append(node_info)
                logger.info(f"Added node {node_info.node_id} to registry")
            
            # Update timestamp
            registry.updated_at = datetime.now()
            
            # Publish to IPNS
            registry_dict = {
                'nodes': [node.dict() for node in registry.nodes],
                'updated_at': registry.updated_at.isoformat()
            }
            
            ipns_name = await self.state_manager.update_node_registry(registry_dict)
            
            if ipns_name:
                self.registry_ipns = ipns_name
                # Update cache
                self.local_cache = registry
                self.last_update = datetime.now()
            
            return ipns_name or ""
            
        except Exception as e:
            logger.error(f"Failed to register node: {e}", exc_info=True)
            raise
    
    async def get_registry(self) -> NodeRegistry:
        """
        Get node registry from IPNS
        
        Returns:
            NodeRegistry instance
        """
        # Check cache first
        if self.local_cache and self.last_update:
            if datetime.now() - self.last_update < self.cache_ttl:
                return self.local_cache
        
        try:
            # Load from IPNS
            registry_dict = await self.state_manager.get_node_registry()
            
            if registry_dict and 'nodes' in registry_dict:
                # Convert dict to NodeRegistry
                nodes = []
                for node_dict in registry_dict.get('nodes', []):
                    try:
                        # Parse datetime fields
                        if 'last_heartbeat' in node_dict and node_dict['last_heartbeat']:
                            node_dict['last_heartbeat'] = datetime.fromisoformat(node_dict['last_heartbeat'])
                        if 'registered_at' in node_dict and node_dict['registered_at']:
                            node_dict['registered_at'] = datetime.fromisoformat(node_dict['registered_at'])
                        
                        nodes.append(NodeInfo(**node_dict))
                    except Exception as e:
                        logger.warning(f"Failed to parse node info: {e}")
                        continue
                
                registry = NodeRegistry(
                    nodes=nodes,
                    updated_at=datetime.fromisoformat(registry_dict.get('updated_at', datetime.now().isoformat()))
                )
                
                # Update cache
                self.local_cache = registry
                self.last_update = datetime.now()
                
                return registry
            
            # Return empty registry if not found
            return NodeRegistry(nodes=[], updated_at=datetime.now())
            
        except Exception as e:
            logger.warning(f"Failed to get registry from IPNS: {e}")
            # Return cached registry if available
            if self.local_cache:
                return self.local_cache
            # Return empty registry
            return NodeRegistry(nodes=[], updated_at=datetime.now())
    
    async def get_active_nodes(self) -> List[NodeInfo]:
        """
        Get list of active nodes (with recent heartbeats)
        
        Returns:
            List of active NodeInfo
        """
        registry = await self.get_registry()
        now = datetime.now()
        timeout = timedelta(seconds=self.heartbeat_timeout)
        
        active_nodes = []
        for node in registry.nodes:
            # Check if node has recent heartbeat
            if node.last_heartbeat:
                if now - node.last_heartbeat < timeout:
                    active_nodes.append(node)
            elif node.status == 'active':
                # If no heartbeat but status is active, include it
                # (might be a new node)
                active_nodes.append(node)
        
        return active_nodes
    
    async def update_node_heartbeat(self, node_id: str, heartbeat_data: Dict):
        """
        Update node heartbeat in registry
        
        Args:
            node_id: Node identifier
            heartbeat_data: Heartbeat data from Pubsub
        """
        try:
            registry = await self.get_registry()
            
            # Find node
            node_found = False
            for node in registry.nodes:
                if node.node_id == node_id:
                    # Update heartbeat
                    node.last_heartbeat = datetime.now()
                    
                    # Update status if provided
                    if 'status' in heartbeat_data:
                        node.status = heartbeat_data['status']
                    
                    # Update resources if provided
                    if 'resources' in heartbeat_data:
                        resources = heartbeat_data['resources']
                        if 'cpu_available' in resources:
                            node.cpu_available = resources['cpu_available']
                        if 'memory_available' in resources:
                            node.memory_available = resources['memory_available']
                        if 'gpu_available' in resources:
                            node.gpu_available = resources.get('gpu_available', False)
                    
                    # Update cached models if provided
                    if 'cached_models' in heartbeat_data:
                        node.cached_models = heartbeat_data['cached_models']
                    
                    node_found = True
                    break
            
            if not node_found:
                logger.warning(f"Node {node_id} not found in registry for heartbeat update")
                return
            
            # Update timestamp
            registry.updated_at = datetime.now()
            
            # Publish to IPNS
            registry_dict = {
                'nodes': [node.dict() for node in registry.nodes],
                'updated_at': registry.updated_at.isoformat()
            }
            
            await self.state_manager.update_node_registry(registry_dict)
            
            # Update cache
            self.local_cache = registry
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to update node heartbeat: {e}", exc_info=True)
    
    async def remove_node(self, node_id: str):
        """
        Remove node from registry
        
        Args:
            node_id: Node identifier
        """
        try:
            registry = await self.get_registry()
            
            # Remove node
            registry.nodes = [n for n in registry.nodes if n.node_id != node_id]
            
            # Update timestamp
            registry.updated_at = datetime.now()
            
            # Publish to IPNS
            registry_dict = {
                'nodes': [node.dict() for node in registry.nodes],
                'updated_at': registry.updated_at.isoformat()
            }
            
            await self.state_manager.update_node_registry(registry_dict)
            
            # Update cache
            self.local_cache = registry
            self.last_update = datetime.now()
            
            logger.info(f"Removed node {node_id} from registry")
            
        except Exception as e:
            logger.error(f"Failed to remove node: {e}", exc_info=True)
    
    async def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """
        Get specific node by ID
        
        Args:
            node_id: Node identifier
            
        Returns:
            NodeInfo or None
        """
        registry = await self.get_registry()
        
        for node in registry.nodes:
            if node.node_id == node_id:
                return node
        
        return None

