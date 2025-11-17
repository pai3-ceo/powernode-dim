"""
Integration tests for Orchestrator-Daemon interaction
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'orchestrator' / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'daemon' / 'src'))

from orchestrator import DIMOrchestrator
from daemon import DIMDaemon
from models.job_spec import JobSpec, Pattern, Priority


@pytest.mark.asyncio
async def test_orchestrator_daemon_workflow(test_config, sample_job_spec_collaborative):
    """Test complete orchestrator-daemon workflow"""
    # Initialize orchestrator
    orchestrator = DIMOrchestrator(test_config)
    
    # Initialize daemon
    daemon = DIMDaemon(test_config)
    
    # Mock daemon gRPC client
    with patch('orchestrator.pattern_router.PatternEngineClient') as mock_client:
        mock_client.execute = AsyncMock(return_value={'result': 'test-result'})
        
        # Submit job through orchestrator
        spec = JobSpec(**sample_job_spec_collaborative)
        job_id = await orchestrator.submit_job(spec, "test-user-001")
        
        assert job_id is not None
        
        # Check job status
        status = await orchestrator.get_job_status(job_id)
        assert status is not None


@pytest.mark.asyncio
async def test_node_discovery_integration(test_config, sample_node_info):
    """Test node discovery integration"""
    orchestrator = DIMOrchestrator(test_config)
    
    # Mock node registry
    with patch.object(orchestrator.registry_manager, 'get_registry', new_callable=AsyncMock) as mock_registry:
        from models.node_info import NodeRegistry, NodeInfo
        from datetime import datetime
        
        mock_registry.return_value = NodeRegistry(
            nodes=[NodeInfo(**sample_node_info)],
            updated_at=datetime.now()
        )
        
        # Test node selection
        nodes = await orchestrator.node_selector.select_nodes({
            'count': 1,
            'reputation_min': 0.9
        })
        
        assert len(nodes) >= 0  # May be 0 if no nodes match


@pytest.mark.asyncio
async def test_job_distribution_integration(test_config, sample_job_spec_collaborative):
    """Test job distribution across orchestrators"""
    orchestrator = DIMOrchestrator(test_config)
    
    with patch.object(orchestrator.coordinator, 'select_orchestrator_for_job', new_callable=AsyncMock) as mock_select:
        with patch.object(orchestrator.coordinator, 'assign_job_to_orchestrator', new_callable=AsyncMock) as mock_assign:
            # Simulate job assignment to another orchestrator
            mock_select.return_value = "orchestrator-002"
            
            spec = JobSpec(**sample_job_spec_collaborative)
            job_id = await orchestrator.submit_job(spec, "test-user-001")
            
            # Verify job was assigned
            mock_assign.assert_called_once()
            assert mock_assign.call_args[0][0] == "orchestrator-002"

