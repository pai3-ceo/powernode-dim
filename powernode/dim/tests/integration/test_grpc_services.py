"""
Integration tests for gRPC services
"""

import pytest
import asyncio
import grpc
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'orchestrator' / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'daemon' / 'src'))

from orchestrator import DIMOrchestrator
from daemon import DIMDaemon
from grpc_server import OrchestratorGRPCServer
from daemon.src.grpc_server import DaemonGRPCServer


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_grpc_server_start(test_config):
    """Test orchestrator gRPC server startup"""
    orchestrator = DIMOrchestrator(test_config)
    grpc_server = OrchestratorGRPCServer(orchestrator, test_config)
    
    # Server should initialize
    assert grpc_server.address is not None
    assert grpc_server.orchestrator == orchestrator


@pytest.mark.integration
@pytest.mark.asyncio
async def test_daemon_grpc_server_start(test_config):
    """Test daemon gRPC server startup"""
    daemon = DIMDaemon(test_config)
    grpc_server = DaemonGRPCServer(daemon, test_config)
    
    # Server should initialize
    assert grpc_server.address is not None
    assert grpc_server.daemon == daemon


@pytest.mark.integration
@pytest.mark.asyncio
async def test_grpc_submit_job(test_config, sample_job_spec_collaborative):
    """Test gRPC job submission"""
    orchestrator = DIMOrchestrator(test_config)
    
    # Mock pattern engine
    with patch('orchestrator.pattern_router.PatternEngineClient') as mock_engine:
        mock_engine.execute = AsyncMock(return_value={'result': 'test'})
        
        # Create servicer
        from grpc_server import OrchestratorServicer
        servicer = OrchestratorServicer(orchestrator)
        
        # Create mock request
        from grpc_generated import orchestrator_pb2, common_pb2
        
        request = orchestrator_pb2.SubmitJobRequest(
            user_id="test-user",
            pattern=common_pb2.Pattern.PATTERN_COLLABORATIVE,
            config_json='{"model_id": "test-model", "nodes": ["node-1", "node-2"]}',
            priority=common_pb2.Priority.PRIORITY_NORMAL
        )
        
        # Mock context
        context = Mock()
        
        # Call servicer
        response = await servicer.SubmitJob(request, context)
        
        assert response.job_id is not None
        assert response.status in ['pending', 'running']

