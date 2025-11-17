"""
Unit tests for Collaborative Pattern Engine
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'pattern_engines' / 'collaborative'))

from engine import CollaborativeEngine


@pytest.mark.asyncio
async def test_collaborative_engine_execute(test_config):
    """Test collaborative engine execution"""
    engine = CollaborativeEngine(test_config)
    
    job_spec = {
        'job_id': 'test-job-001',
        'config': {
            'model_id': 'test-model',
            'nodes': ['node-001', 'node-002'],
            'aggregation': {'method': 'federated_averaging'}
        }
    }
    
    with patch.object(engine, 'send_to_daemon', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {'result': [1, 2, 3]}
        
        result = await engine.execute_pattern('test-job-001', job_spec)
        
        assert result is not None
        assert mock_send.call_count == 2  # Called for each node

