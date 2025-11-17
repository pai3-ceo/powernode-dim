"""
Unit tests for DIM Daemon
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'daemon' / 'src'))

from daemon import DIMDaemon


@pytest.mark.asyncio
async def test_daemon_initialization(test_config):
    """Test daemon initialization"""
    daemon = DIMDaemon(test_config)
    
    assert daemon.config == test_config
    assert daemon.node_id == 'test-node-001'
    assert daemon.active_jobs == {}
    assert daemon.stats['total_jobs'] == 0


@pytest.mark.asyncio
async def test_submit_job(test_config):
    """Test job submission to daemon"""
    daemon = DIMDaemon(test_config)
    
    job_spec = {
        'job_id': 'test-job-001',
        'model_id': 'test-model-001',
        'data_source': 'test-cabinet-001',
        'timeout': 120,
        'priority': 1
    }
    
    with patch.object(daemon.resource_manager, 'can_accept_job', return_value=True):
        with patch.object(daemon.job_queue, 'enqueue', new_callable=AsyncMock):
            result = await daemon.submit_job(job_spec)
            
            assert result['job_id'] == 'test-job-001'
            assert result['status'] == 'queued'
            assert daemon.stats['total_jobs'] == 1


@pytest.mark.asyncio
async def test_get_job_status(test_config):
    """Test getting job status"""
    daemon = DIMDaemon(test_config)
    
    job_spec = {
        'job_id': 'test-job-001',
        'model_id': 'test-model-001',
        'timeout': 120
    }
    
    with patch.object(daemon.resource_manager, 'can_accept_job', return_value=True):
        with patch.object(daemon.job_queue, 'enqueue', new_callable=AsyncMock):
            await daemon.submit_job(job_spec)
            
            status = await daemon.get_job_status('test-job-001')
            
            assert status is not None
            assert status['status'] == 'queued'


@pytest.mark.asyncio
async def test_cancel_job(test_config):
    """Test job cancellation"""
    daemon = DIMDaemon(test_config)
    
    job_spec = {
        'job_id': 'test-job-001',
        'model_id': 'test-model-001',
        'timeout': 120
    }
    
    with patch.object(daemon.resource_manager, 'can_accept_job', return_value=True):
        with patch.object(daemon.job_queue, 'enqueue', new_callable=AsyncMock):
            await daemon.submit_job(job_spec)
            
            with patch.object(daemon.job_queue, 'remove', new_callable=AsyncMock):
                with patch.object(daemon.agent_manager, 'cancel_agent', new_callable=AsyncMock):
                    success = await daemon.cancel_job('test-job-001')
                    
                    assert success is True


@pytest.mark.asyncio
async def test_get_health(test_config):
    """Test getting daemon health"""
    daemon = DIMDaemon(test_config)
    
    with patch.object(daemon.resource_manager, 'get_status', return_value={
        'cpu_percent': 50.0,
        'memory_percent': 60.0,
        'cpu_available': 10,
        'memory_available_gb': 32,
        'gpu_available': True
    }):
        with patch.object(daemon.model_cache, 'get_cached_models', return_value=['model-1', 'model-2']):
            health = await daemon.get_health()
            
            assert health['status'] in ['healthy', 'degraded', 'unhealthy']
            assert 'resources' in health
            assert 'cached_models' in health
            assert health['node_id'] == 'test-node-001'


@pytest.mark.asyncio
async def test_get_stats(test_config):
    """Test getting daemon statistics"""
    daemon = DIMDaemon(test_config)
    
    daemon.stats = {
        'total_jobs': 100,
        'successful_jobs': 95,
        'failed_jobs': 5,
        'execution_times': [10.0, 20.0, 30.0]
    }
    
    with patch.object(daemon.resource_manager, 'get_status', return_value={
        'cpu_available': 10,
        'memory_available_gb': 32,
        'gpu_available': True,
        'cpu_percent': 50.0,
        'memory_percent': 60.0
    }):
        with patch.object(daemon.model_cache, 'get_cached_models', return_value=['model-1']):
            with patch.object(daemon.model_cache, 'get_cache_size', return_value=1024 * 1024):
                stats = await daemon.get_stats()
                
                assert stats['total_jobs'] == 100
                assert stats['successful_jobs'] == 95
                assert stats['failed_jobs'] == 5
                assert stats['avg_execution_time'] == 20.0
                assert stats['cached_models_count'] == 1


@pytest.mark.asyncio
async def test_resource_check_failure(test_config):
    """Test job submission when resources insufficient"""
    daemon = DIMDaemon(test_config)
    
    job_spec = {
        'job_id': 'test-job-001',
        'model_id': 'test-model-001',
        'timeout': 120
    }
    
    with patch.object(daemon.resource_manager, 'can_accept_job', return_value=False):
        with pytest.raises(Exception):  # Should raise ResourceError
            await daemon.submit_job(job_spec)

