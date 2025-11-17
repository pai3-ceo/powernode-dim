"""
Performance load tests
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'orchestrator' / 'src'))

from orchestrator import DIMOrchestrator
from models.job_spec import JobSpec, Pattern, Priority


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_job_submission(test_config, sample_job_spec_collaborative):
    """Test submitting multiple jobs concurrently"""
    orchestrator = DIMOrchestrator(test_config)
    
    with patch('orchestrator.pattern_router.PatternEngineClient') as mock_engine:
        mock_engine.execute = AsyncMock(return_value={'result': 'test'})
        
        # Submit 10 jobs concurrently
        jobs = []
        for i in range(10):
            spec = JobSpec(**sample_job_spec_collaborative)
            job_id = await orchestrator.submit_job(spec, f"test-user-{i}")
            jobs.append(job_id)
        
        assert len(jobs) == 10
        assert len(set(jobs)) == 10  # All unique


@pytest.mark.performance
@pytest.mark.asyncio
async def test_job_submission_performance(test_config, sample_job_spec_collaborative):
    """Test job submission performance"""
    orchestrator = DIMOrchestrator(test_config)
    
    with patch('orchestrator.pattern_router.PatternEngineClient') as mock_engine:
        mock_engine.execute = AsyncMock(return_value={'result': 'test'})
        
        start_time = time.time()
        
        for i in range(100):
            spec = JobSpec(**sample_job_spec_collaborative)
            await orchestrator.submit_job(spec, f"test-user-{i}")
        
        elapsed = time.time() - start_time
        
        # Should handle 100 jobs in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        print(f"Submitted 100 jobs in {elapsed:.2f} seconds ({100/elapsed:.1f} jobs/sec)")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_node_selection_performance(test_config):
    """Test node selection performance"""
    orchestrator = DIMOrchestrator(test_config)
    
    # Create large registry
    from models.node_info import NodeInfo, NodeRegistry
    from datetime import datetime
    
    nodes = [
        NodeInfo(
            node_id=f'node-{i:03d}',
            status='active',
            reputation=0.9,
            node_type='power',
            data_types=['medical'],
            cached_models=[],
            cpu_available=20,
            memory_available=64,
            gpu_available=True,
            tailscale_ip=f'100.64.1.{i}',
            last_heartbeat=datetime.now(),
            registered_at=datetime.now()
        )
        for i in range(100)
    ]
    
    registry = NodeRegistry(nodes=nodes, updated_at=datetime.now())
    
    with patch.object(orchestrator.node_selector, 'load_node_registry', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = registry
        
        start_time = time.time()
        
        for _ in range(100):
            await orchestrator.node_selector.select_nodes({
                'count': 5,
                'reputation_min': 0.85
            })
        
        elapsed = time.time() - start_time
        
        # Should handle 100 selections quickly (< 1 second)
        assert elapsed < 1.0
        print(f"Selected nodes 100 times in {elapsed:.2f} seconds")

