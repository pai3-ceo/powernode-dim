"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

# Test configuration
TEST_CONFIG = {
    'orchestrator': {
        'orchestrator_id': 'test-orchestrator-001',
        'grpc_address': 'localhost:50051',
        'log_level': 'DEBUG',
        'engines': {
            'collaborative': 'http://localhost:8001',
            'comparative': 'http://localhost:8002',
            'chained': 'http://localhost:8003'
        }
    },
    'daemon': {
        'node_id': 'test-node-001',
        'grpc_address': 'localhost:50052',
        'log_level': 'DEBUG',
        'cache_dir': '/tmp/dim-test-models',
        'max_cache_gb': 10,
        'max_concurrent_jobs': 5
    },
    'ipfs': {
        'api_url': '/ip4/127.0.0.1/tcp/5001',
        'ipns_key_name': 'test-dim-key',
        'pubsub': {
            'job_updates': 'test.dim.jobs.updates',
            'node_heartbeat': 'test.dim.nodes.heartbeat',
            'results_ready': 'test.dim.results.ready'
        }
    },
    'monitoring': {
        'enabled': True
    },
    'rate_limiting': {
        'enabled': False  # Disable for tests
    },
    'prewarming': {
        'enabled': False  # Disable for tests
    }
}


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Provide test configuration"""
    return TEST_CONFIG.copy()


@pytest.fixture
def sample_job_spec_collaborative() -> Dict:
    """Sample collaborative job specification"""
    return {
        'pattern': 'collaborative',
        'config': {
            'model_id': 'test-model-001',
            'nodes': ['test-node-001', 'test-node-002'],
            'aggregation': {'method': 'federated_averaging'}
        },
        'priority': 'normal',
        'max_cost': 1000
    }


@pytest.fixture
def sample_job_spec_comparative() -> Dict:
    """Sample comparative job specification"""
    return {
        'pattern': 'comparative',
        'config': {
            'model_ids': ['test-model-001', 'test-model-002'],
            'node_id': 'test-node-001',
            'data_source': 'test-cabinet-001',
            'consensus': {'method': 'weighted_vote', 'minAgreement': 0.75}
        },
        'priority': 'normal',
        'max_cost': 1000
    }


@pytest.fixture
def sample_job_spec_chained() -> Dict:
    """Sample chained job specification"""
    return {
        'pattern': 'chained',
        'config': {
            'pipeline': [
                {
                    'step': 1,
                    'name': 'Step1',
                    'model_id': 'test-model-001',
                    'node_id': 'test-node-001',
                    'input_source': 'client_data',
                    'timeout': 60
                },
                {
                    'step': 2,
                    'name': 'Step2',
                    'model_id': 'test-model-002',
                    'node_id': 'test-node-001',
                    'input_source': 'step_1_output',
                    'timeout': 60
                }
            ]
        },
        'priority': 'normal',
        'max_cost': 1000
    }


@pytest.fixture
def sample_node_info() -> Dict:
    """Sample node information"""
    return {
        'node_id': 'test-node-001',
        'status': 'active',
        'reputation': 0.95,
        'node_type': 'power',
        'data_types': ['medical', 'legal'],
        'cached_models': ['test-model-001'],
        'cpu_available': 20,
        'memory_available': 64,
        'gpu_available': True,
        'tailscale_ip': '100.64.1.1',
        'last_heartbeat': datetime.now().isoformat(),
        'registered_at': datetime.now().isoformat()
    }


@pytest.fixture
def mock_ipfs_client(monkeypatch):
    """Mock IPFS client for testing"""
    class MockIPFSClient:
        def __init__(self, *args, **kwargs):
            self.added_files = {}
            self.pinned_cids = set()
        
        async def add_file(self, file_path: str, pin: bool = True) -> str:
            cid = f"QmMock{hash(file_path)}"
            if pin:
                self.pinned_cids.add(cid)
            self.added_files[cid] = file_path
            return cid
        
        async def get_file(self, cid: str, output_path: str) -> bool:
            if cid in self.added_files:
                # Create mock file
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_text("mock content")
                return True
            return False
        
        async def pin(self, cid: str) -> bool:
            self.pinned_cids.add(cid)
            return True
        
        async def unpin(self, cid: str) -> bool:
            self.pinned_cids.discard(cid)
            return True
    
    return MockIPFSClient()


@pytest.fixture
def mock_model_cache(monkeypatch):
    """Mock model cache for testing"""
    class MockModelCache:
        def __init__(self, *args, **kwargs):
            self.cached_models = {}
        
        async def get_model(self, model_id: str) -> str:
            if model_id not in self.cached_models:
                # Create mock model path
                model_path = f"/tmp/test-models/{model_id}"
                Path(model_path).parent.mkdir(parents=True, exist_ok=True)
                Path(model_path).write_text("mock model")
                self.cached_models[model_id] = model_path
            return self.cached_models[model_id]
        
        def get_cached_models(self) -> list:
            return list(self.cached_models.keys())
        
        def get_cache_size(self) -> int:
            return len(self.cached_models) * 1024  # Mock size
    
    return MockModelCache()

