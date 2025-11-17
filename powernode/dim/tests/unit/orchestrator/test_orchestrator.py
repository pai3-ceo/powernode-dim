"""
Unit tests for DIM Orchestrator
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'orchestrator' / 'src'))

from orchestrator import DIMOrchestrator
from models.job_spec import JobSpec, Pattern, Priority
from models.job_status import JobState


@pytest.mark.asyncio
async def test_orchestrator_initialization(test_config):
    """Test orchestrator initialization"""
    orchestrator = DIMOrchestrator(test_config)
    
    assert orchestrator.config == test_config
    assert orchestrator.active_jobs == {}
    assert orchestrator.grpc_server is None


@pytest.mark.asyncio
async def test_submit_job(test_config, sample_job_spec_collaborative):
    """Test job submission"""
    orchestrator = DIMOrchestrator(test_config)
    
    # Mock dependencies
    with patch.object(orchestrator.state_manager, 'save_job_spec', new_callable=AsyncMock) as mock_save:
        with patch.object(orchestrator.coordinator, 'select_orchestrator_for_job', new_callable=AsyncMock) as mock_select:
            with patch.object(orchestrator.coordinator, 'assign_job_to_orchestrator', new_callable=AsyncMock) as mock_assign:
                mock_save.return_value = "test-cid"
                mock_select.return_value = None  # Execute locally
                
                spec = JobSpec(**sample_job_spec_collaborative)
                job_id = await orchestrator.submit_job(spec, "test-user-001")
                
                assert job_id is not None
                assert job_id.startswith("job-")
                assert job_id in orchestrator.active_jobs
                mock_save.assert_called_once()
                mock_select.assert_called_once()


@pytest.mark.asyncio
async def test_get_job_status(test_config, sample_job_spec_collaborative):
    """Test getting job status"""
    orchestrator = DIMOrchestrator(test_config)
    
    spec = JobSpec(**sample_job_spec_collaborative)
    job_id = await orchestrator.submit_job(spec, "test-user-001")
    
    status = await orchestrator.get_job_status(job_id)
    
    assert status is not None
    assert status.job_id == job_id
    assert status.state == JobState.PENDING


@pytest.mark.asyncio
async def test_cancel_job(test_config, sample_job_spec_collaborative):
    """Test job cancellation"""
    orchestrator = DIMOrchestrator(test_config)
    
    spec = JobSpec(**sample_job_spec_collaborative)
    job_id = await orchestrator.submit_job(spec, "test-user-001")
    
    success = await orchestrator.cancel_job(job_id, "test-user-001")
    
    assert success is True
    assert orchestrator.active_jobs[job_id].state == JobState.CANCELLED


@pytest.mark.asyncio
async def test_validate_spec(test_config):
    """Test job spec validation"""
    orchestrator = DIMOrchestrator(test_config)
    
    # Valid collaborative spec
    valid_spec = JobSpec(
        pattern=Pattern.COLLABORATIVE,
        config={'model_id': 'test-model', 'nodes': ['node-1', 'node-2']},
        priority=Priority.NORMAL
    )
    validation = orchestrator.validate_spec(valid_spec)
    assert validation['valid'] is True
    
    # Invalid collaborative spec (not enough nodes)
    invalid_spec = JobSpec(
        pattern=Pattern.COLLABORATIVE,
        config={'model_id': 'test-model', 'nodes': ['node-1']},
        priority=Priority.NORMAL
    )
    validation = orchestrator.validate_spec(invalid_spec)
    assert validation['valid'] is False
    assert 'at least 2 nodes' in validation['error']


@pytest.mark.asyncio
async def test_update_job_state(test_config, sample_job_spec_collaborative):
    """Test updating job state"""
    orchestrator = DIMOrchestrator(test_config)
    
    spec = JobSpec(**sample_job_spec_collaborative)
    job_id = await orchestrator.submit_job(spec, "test-user-001")
    
    await orchestrator.update_job_state(job_id, JobState.RUNNING)
    
    assert orchestrator.active_jobs[job_id].state == JobState.RUNNING
    assert orchestrator.active_jobs[job_id].started_at is not None


@pytest.mark.asyncio
async def test_generate_job_id(test_config):
    """Test job ID generation"""
    orchestrator = DIMOrchestrator(test_config)
    
    job_id1 = orchestrator.generate_job_id()
    job_id2 = orchestrator.generate_job_id()
    
    assert job_id1 != job_id2
    assert job_id1.startswith("job-")
    assert len(job_id1) > 10


@pytest.mark.asyncio
async def test_job_distribution(test_config, sample_job_spec_collaborative):
    """Test job distribution to another orchestrator"""
    orchestrator = DIMOrchestrator(test_config)
    
    with patch.object(orchestrator.coordinator, 'select_orchestrator_for_job', new_callable=AsyncMock) as mock_select:
        with patch.object(orchestrator.coordinator, 'assign_job_to_orchestrator', new_callable=AsyncMock) as mock_assign:
            mock_select.return_value = "orchestrator-002"
            
            spec = JobSpec(**sample_job_spec_collaborative)
            job_id = await orchestrator.submit_job(spec, "test-user-001")
            
            mock_select.assert_called_once()
            mock_assign.assert_called_once_with("orchestrator-002", job_id, spec.dict())


@pytest.mark.asyncio
async def test_monitoring_integration(test_config, sample_job_spec_collaborative):
    """Test monitoring integration"""
    orchestrator = DIMOrchestrator(test_config)
    
    if orchestrator.monitoring:
        spec = JobSpec(**sample_job_spec_collaborative)
        job_id = await orchestrator.submit_job(spec, "test-user-001")
        
        # Check that metrics were recorded
        metrics = orchestrator.monitoring.get_metrics()
        assert 'counters' in metrics
        assert 'dim.jobs.submitted' in str(metrics['counters'])

