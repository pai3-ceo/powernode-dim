"""
End-to-end test for Collaborative pattern workflow
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'orchestrator' / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'daemon' / 'src'))

from orchestrator import DIMOrchestrator
from models.job_spec import JobSpec, Pattern, Priority


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_collaborative_workflow_complete(test_config, sample_job_spec_collaborative):
    """Test complete collaborative workflow from submission to completion"""
    orchestrator = DIMOrchestrator(test_config)
    
    # Mock pattern engine
    with patch('orchestrator.pattern_router.PatternEngineClient') as mock_engine:
        mock_engine.execute = AsyncMock(return_value={
            'result': {'aggregated': 'test-result'},
            'nodes_used': 2,
            'execution_time': '45s'
        })
        
        # Submit job
        spec = JobSpec(**sample_job_spec_collaborative)
        job_id = await orchestrator.submit_job(spec, "test-user-001")
        
        assert job_id is not None
        
        # Wait for execution (mocked)
        await asyncio.sleep(0.1)
        
        # Check final status
        status = await orchestrator.get_job_status(job_id)
        assert status is not None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_collaborative_multiple_nodes(test_config):
    """Test collaborative pattern with multiple nodes"""
    orchestrator = DIMOrchestrator(test_config)
    
    spec = JobSpec(
        pattern=Pattern.COLLABORATIVE,
        config={
            'model_id': 'test-model',
            'nodes': ['node-001', 'node-002', 'node-003'],
            'aggregation': {'method': 'federated_averaging'}
        },
        priority=Priority.NORMAL
    )
    
    with patch('orchestrator.pattern_router.PatternEngineClient') as mock_engine:
        mock_engine.execute = AsyncMock(return_value={'result': 'test'})
        
        job_id = await orchestrator.submit_job(spec, "test-user")
        
        assert job_id is not None

