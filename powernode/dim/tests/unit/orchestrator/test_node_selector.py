"""
Unit tests for Node Selector
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'orchestrator' / 'src'))

from node_selector import NodeSelector
from models.node_info import NodeInfo, NodeRegistry


@pytest.mark.asyncio
async def test_node_selector_initialization(test_config):
    """Test node selector initialization"""
    selector = NodeSelector(test_config)
    
    assert selector.config == test_config
    assert selector.registry_manager is None


@pytest.mark.asyncio
async def test_select_nodes(test_config, sample_node_info):
    """Test node selection"""
    selector = NodeSelector(test_config)
    
    # Mock registry
    mock_registry = NodeRegistry(
        nodes=[
            NodeInfo(**sample_node_info),
            NodeInfo(**{**sample_node_info, 'node_id': 'test-node-002', 'reputation': 0.90})
        ],
        updated_at=datetime.now()
    )
    
    with patch.object(selector, 'load_node_registry', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = mock_registry
        
        requirements = {
            'count': 2,
            'reputation_min': 0.85
        }
        
        selected = await selector.select_nodes(requirements)
        
        assert len(selected) == 2
        assert 'test-node-001' in selected
        assert 'test-node-002' in selected


@pytest.mark.asyncio
async def test_select_nodes_reputation_filter(test_config, sample_node_info):
    """Test node selection with reputation filter"""
    selector = NodeSelector(test_config)
    
    # Create nodes with different reputations
    nodes = [
        NodeInfo(**{**sample_node_info, 'node_id': 'node-high', 'reputation': 0.95}),
        NodeInfo(**{**sample_node_info, 'node_id': 'node-medium', 'reputation': 0.80}),
        NodeInfo(**{**sample_node_info, 'node_id': 'node-low', 'reputation': 0.70})
    ]
    
    mock_registry = NodeRegistry(nodes=nodes, updated_at=datetime.now())
    
    with patch.object(selector, 'load_node_registry', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = mock_registry
        
        requirements = {
            'count': 2,
            'reputation_min': 0.85
        }
        
        selected = await selector.select_nodes(requirements)
        
        assert len(selected) == 2
        assert 'node-high' in selected
        assert 'node-medium' not in selected
        assert 'node-low' not in selected


@pytest.mark.asyncio
async def test_select_nodes_data_type_filter(test_config, sample_node_info):
    """Test node selection with data type filter"""
    selector = NodeSelector(test_config)
    
    nodes = [
        NodeInfo(**{**sample_node_info, 'node_id': 'node-medical', 'data_types': ['medical']}),
        NodeInfo(**{**sample_node_info, 'node_id': 'node-legal', 'data_types': ['legal']}),
        NodeInfo(**{**sample_node_info, 'node_id': 'node-both', 'data_types': ['medical', 'legal']})
    ]
    
    mock_registry = NodeRegistry(nodes=nodes, updated_at=datetime.now())
    
    with patch.object(selector, 'load_node_registry', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = mock_registry
        
        requirements = {
            'count': 2,
            'data_type': 'medical'
        }
        
        selected = await selector.select_nodes(requirements)
        
        assert len(selected) == 2
        assert 'node-medical' in selected or 'node-both' in selected
        assert 'node-legal' not in selected


@pytest.mark.asyncio
async def test_weighted_random_selection(test_config):
    """Test weighted random selection"""
    selector = NodeSelector(test_config)
    
    nodes = [
        NodeInfo(node_id='node-high', reputation=0.95, status='active', node_type='power', data_types=[], cached_models=[], cpu_available=20, memory_available=64, gpu_available=True, tailscale_ip='100.64.1.1', last_heartbeat=datetime.now(), registered_at=datetime.now()),
        NodeInfo(node_id='node-medium', reputation=0.80, status='active', node_type='power', data_types=[], cached_models=[], cpu_available=20, memory_available=64, gpu_available=True, tailscale_ip='100.64.1.2', last_heartbeat=datetime.now(), registered_at=datetime.now()),
        NodeInfo(node_id='node-low', reputation=0.60, status='active', node_type='power', data_types=[], cached_models=[], cpu_available=20, memory_available=64, gpu_available=True, tailscale_ip='100.64.1.3', last_heartbeat=datetime.now(), registered_at=datetime.now())
    ]
    
    selected = selector.weighted_random_selection(nodes, 2)
    
    assert len(selected) == 2
    assert all(node.node_id in ['node-high', 'node-medium', 'node-low'] for node in selected)


@pytest.mark.asyncio
async def test_no_eligible_nodes(test_config):
    """Test when no nodes meet requirements"""
    selector = NodeSelector(test_config)
    
    mock_registry = NodeRegistry(nodes=[], updated_at=datetime.now())
    
    with patch.object(selector, 'load_node_registry', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = mock_registry
        
        requirements = {
            'count': 2,
            'reputation_min': 0.95
        }
        
        selected = await selector.select_nodes(requirements)
        
        assert len(selected) == 0

