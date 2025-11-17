"""
Unit tests for Node Registry Manager
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'orchestrator' / 'src'))

from node_registry import NodeRegistryManager
from models.node_info import NodeInfo, NodeRegistry


@pytest.mark.asyncio
async def test_register_node(test_config, sample_node_info):
    """Test node registration"""
    mock_state_manager = Mock()
    mock_state_manager.update_node_registry = AsyncMock(return_value="/ipns/test-key")
    mock_state_manager.get_node_registry = AsyncMock(return_value={'nodes': [], 'updated_at': datetime.now().isoformat()})
    
    registry_manager = NodeRegistryManager(mock_state_manager, test_config)
    
    node = NodeInfo(**sample_node_info)
    ipns_name = await registry_manager.register_node(node)
    
    assert ipns_name == "/ipns/test-key"
    mock_state_manager.update_node_registry.assert_called_once()


@pytest.mark.asyncio
async def test_get_registry(test_config, sample_node_info):
    """Test getting registry"""
    mock_state_manager = Mock()
    mock_state_manager.get_node_registry = AsyncMock(return_value={
        'nodes': [sample_node_info],
        'updated_at': datetime.now().isoformat()
    })
    
    registry_manager = NodeRegistryManager(mock_state_manager, test_config)
    
    registry = await registry_manager.get_registry()
    
    assert len(registry.nodes) == 1
    assert registry.nodes[0].node_id == 'test-node-001'


@pytest.mark.asyncio
async def test_get_active_nodes(test_config, sample_node_info):
    """Test getting active nodes"""
    mock_state_manager = Mock()
    now = datetime.now()
    
    nodes_data = [
        {**sample_node_info, 'node_id': 'active-1', 'last_heartbeat': now.isoformat()},
        {**sample_node_info, 'node_id': 'stale-1', 'last_heartbeat': (now - timedelta(seconds=200)).isoformat()},
        {**sample_node_info, 'node_id': 'active-2', 'last_heartbeat': (now - timedelta(seconds=30)).isoformat()}
    ]
    
    mock_state_manager.get_node_registry = AsyncMock(return_value={
        'nodes': nodes_data,
        'updated_at': now.isoformat()
    })
    
    registry_manager = NodeRegistryManager(mock_state_manager, test_config)
    
    active_nodes = await registry_manager.get_active_nodes()
    
    assert len(active_nodes) >= 2
    assert any(node.node_id == 'active-1' for node in active_nodes)
    assert any(node.node_id == 'active-2' for node in active_nodes)
    assert not any(node.node_id == 'stale-1' for node in active_nodes)


@pytest.mark.asyncio
async def test_update_node_heartbeat(test_config, sample_node_info):
    """Test updating node heartbeat"""
    mock_state_manager = Mock()
    mock_state_manager.get_node_registry = AsyncMock(return_value={
        'nodes': [sample_node_info],
        'updated_at': datetime.now().isoformat()
    })
    mock_state_manager.update_node_registry = AsyncMock(return_value="/ipns/test-key")
    
    registry_manager = NodeRegistryManager(mock_state_manager, test_config)
    
    heartbeat_data = {
        'status': 'active',
        'resources': {'cpu_available': 18, 'memory_available': 60}
    }
    
    await registry_manager.update_node_heartbeat('test-node-001', heartbeat_data)
    
    mock_state_manager.update_node_registry.assert_called_once()


@pytest.mark.asyncio
async def test_remove_node(test_config, sample_node_info):
    """Test removing node from registry"""
    mock_state_manager = Mock()
    mock_state_manager.get_node_registry = AsyncMock(return_value={
        'nodes': [sample_node_info],
        'updated_at': datetime.now().isoformat()
    })
    mock_state_manager.update_node_registry = AsyncMock(return_value="/ipns/test-key")
    
    registry_manager = NodeRegistryManager(mock_state_manager, test_config)
    
    await registry_manager.remove_node('test-node-001')
    
    mock_state_manager.update_node_registry.assert_called_once()
    # Verify node was removed
    call_args = mock_state_manager.update_node_registry.call_args[0][0]
    assert len(call_args['nodes']) == 0

