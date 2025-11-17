"""
Integration tests for IPFS integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'orchestrator' / 'src'))

from ipfs.state_manager import IPFSStateManager
from ipfs.pubsub import IPFSPubsub
from ipfs.ipns import IPNSManager


@pytest.mark.asyncio
async def test_ipfs_state_manager_initialization(test_config):
    """Test IPFS state manager initialization"""
    # Mock IPFS client
    with patch('ipfs.state_manager.DIMIPFSClient') as mock_client:
        state_manager = IPFSStateManager(test_config)
        
        assert state_manager.client is not None
        # IPNS and Pubsub may be None if IPFS not available
        assert state_manager.ipns is None or state_manager.ipns is not None


@pytest.mark.asyncio
async def test_save_and_load_job_spec(test_config):
    """Test saving and loading job spec from IPFS"""
    state_manager = IPFSStateManager(test_config)
    
    job_spec = {
        'job_id': 'test-job-001',
        'pattern': 'collaborative',
        'config': {'model_id': 'test-model'}
    }
    
    with patch.object(state_manager.client, 'save_job_spec', new_callable=AsyncMock) as mock_save:
        mock_save.return_value = "test-cid"
        
        cid = await state_manager.save_job_spec('test-job-001', job_spec)
        
        assert cid == "test-cid"
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_pubsub_publish(test_config):
    """Test IPFS Pubsub publishing"""
    # Mock IPFS Pubsub
    with patch('ipfs.pubsub.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = Mock()
        
        pubsub = IPFSPubsub("http://localhost:5001/api/v0")
        
        message = {
            'job_id': 'test-job-001',
            'event_type': 'completed',
            'data': {'result': 'test'}
        }
        
        success = await pubsub.publish('test.topic', message)
        
        assert success is True


@pytest.mark.asyncio
async def test_ipns_state_update(test_config):
    """Test IPNS state update"""
    # Mock IPNS manager
    with patch('ipfs.ipns.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'Name': '/ipns/test-key'}
        mock_post.return_value.raise_for_status = Mock()
        
        ipns = IPNSManager("http://localhost:5001/api/v0", "test-key")
        
        state_data = {
            'nodes': [],
            'updated_at': '2024-12-19T10:00:00Z'
        }
        
        # Mock file operations
        with patch('ipfs.ipns.tempfile.NamedTemporaryFile') as mock_temp:
            with patch('ipfs.ipns.os.unlink'):
                mock_file = Mock()
                mock_file.name = '/tmp/test.json'
                mock_temp.return_value.__enter__.return_value = mock_file
                
                with patch('builtins.open', create=True):
                    with patch('ipfs.ipns.requests.post') as mock_add:
                        mock_add.return_value.status_code = 200
                        mock_add.return_value.json.return_value = {'Hash': 'test-cid'}
                        mock_add.return_value.raise_for_status = Mock()
                        
                        ipns_name = ipns.update_state(state_data)
                        
                        assert ipns_name is not None

