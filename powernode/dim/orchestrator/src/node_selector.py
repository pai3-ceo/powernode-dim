"""
Node Selector - Selects optimal nodes for job execution
"""

from typing import List, Dict, Optional
import random
from .models.node_info import NodeInfo, NodeRegistry
from .node_registry import NodeRegistryManager
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class NodeSelector:
    """Selects optimal nodes for job execution"""
    
    def __init__(self, config: Dict):
        """
        Initialize node selector
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.state_manager = None  # Will be set by orchestrator
        self.registry_manager: Optional[NodeRegistryManager] = None
        self.registry_cache: Dict[str, NodeRegistry] = {}
    
    def set_state_manager(self, state_manager):
        """Set state manager for IPNS access"""
        self.state_manager = state_manager
    
    def set_registry_manager(self, registry_manager: NodeRegistryManager):
        """Set node registry manager"""
        self.registry_manager = registry_manager
    
    async def select_nodes(self, requirements: Dict) -> List[str]:
        """
        Select nodes based on requirements
        
        Args:
            requirements: {
                'count': int,
                'reputation_min': float,
                'data_type': str (optional),
                'location': str (optional)
            }
        
        Returns:
            List of selected node IDs
        """
        # Load node registry (from IPNS if available)
        registry = await self.load_node_registry()
        
        # Filter by requirements
        eligible_nodes = []
        for node in registry.nodes:
            if self.meets_requirements(node, requirements):
                eligible_nodes.append(node)
        
        if not eligible_nodes:
            logger.warning(f"No eligible nodes found for requirements: {requirements}")
            return []
        
        # Sort by reputation (descending)
        eligible_nodes.sort(key=lambda n: n.reputation, reverse=True)
        
        # Select top N with some randomization
        count = requirements.get('count', 1)
        selected = self.weighted_random_selection(eligible_nodes, count)
        
        node_ids = [node.node_id for node in selected]
        logger.info(f"Selected {len(node_ids)} nodes: {node_ids}")
        
        return node_ids
    
    def meets_requirements(self, node: NodeInfo, requirements: Dict) -> bool:
        """
        Check if node meets requirements
        
        Args:
            node: Node information
            requirements: Requirements dictionary
            
        Returns:
            True if node meets requirements
        """
        # Reputation check
        if node.reputation < requirements.get('reputation_min', 0.0):
            return False
        
        # Status check
        if node.status != 'active':
            return False
        
        # Data type check
        if 'data_type' in requirements:
            if requirements['data_type'] not in node.data_types:
                return False
        
        # Location check (optional)
        if 'location' in requirements and requirements['location']:
            if node.location != requirements['location']:
                return False
        
        return True
    
    def weighted_random_selection(self, nodes: List[NodeInfo], count: int) -> List[NodeInfo]:
        """
        Select nodes with weighted randomness (reputation-based)
        
        Args:
            nodes: List of eligible nodes
            count: Number of nodes to select
            
        Returns:
            List of selected nodes
        """
        if len(nodes) <= count:
            return nodes
        
        # Weight by reputation
        weights = [node.reputation for node in nodes]
        
        # Random sample with weights
        selected = random.choices(nodes, weights=weights, k=count)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_selected = []
        for node in selected:
            if node.node_id not in seen:
                seen.add(node.node_id)
                unique_selected.append(node)
        
        # If we need more nodes, add from top of list
        while len(unique_selected) < count and len(unique_selected) < len(nodes):
            for node in nodes:
                if node.node_id not in seen:
                    unique_selected.append(node)
                    seen.add(node.node_id)
                    break
        
        return unique_selected[:count]
    
    async def load_node_registry(self) -> NodeRegistry:
        """
        Load node registry from IPNS or fallback to mock
        
        Returns:
            NodeRegistry instance
        """
        # Use registry manager if available (Phase 2)
        if self.registry_manager:
            try:
                return await self.registry_manager.get_registry()
            except Exception as e:
                logger.warning(f"Failed to load node registry: {e}")
        
        # Try to load from IPNS if state manager is available
        if self.state_manager and self.state_manager.ipns:
            try:
                registry_dict = await self.state_manager.get_node_registry()
                if registry_dict and 'nodes' in registry_dict:
                    # Convert dict to NodeRegistry
                    nodes = [NodeInfo(**node_dict) for node_dict in registry_dict.get('nodes', [])]
                    from datetime import datetime
                    return NodeRegistry(
                        nodes=nodes,
                        updated_at=datetime.fromisoformat(registry_dict.get('updated_at', datetime.now().isoformat()))
                    )
            except Exception as e:
                logger.warning(f"Failed to load node registry from IPNS: {e}")
        
        # Fallback to mock registry for development
        if 'mock' in self.registry_cache:
            return self.registry_cache['mock']
        
        # Create mock registry for development
        from datetime import datetime
        mock_registry = NodeRegistry(
            nodes=[
                NodeInfo(
                    node_id='node-001',
                    status='active',
                    reputation=0.95,
                    node_type='power',
                    data_types=['medical', 'legal'],
                    cached_models=[],
                    cpu_available=20,
                    memory_available=64,
                    gpu_available=True,
                    tailscale_ip='100.64.1.1',
                    last_heartbeat=datetime.now(),
                    registered_at=datetime.now()
                ),
                NodeInfo(
                    node_id='node-002',
                    status='active',
                    reputation=0.90,
                    node_type='power',
                    data_types=['medical', 'financial'],
                    cached_models=[],
                    cpu_available=20,
                    memory_available=64,
                    gpu_available=True,
                    tailscale_ip='100.64.1.2',
                    last_heartbeat=datetime.now(),
                    registered_at=datetime.now()
                )
            ],
            updated_at=datetime.now()
        )
        
        self.registry_cache['mock'] = mock_registry
        return mock_registry
