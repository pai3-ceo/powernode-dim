"""
Unit tests for Model Pre-warmer
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'daemon' / 'src'))

from model_prewarmer import ModelPrewarmer


@pytest.mark.asyncio
async def test_prewarmer_initialization(test_config):
    """Test pre-warmer initialization"""
    mock_cache = Mock()
    prewarmer = ModelPrewarmer(mock_cache, test_config)
    
    assert prewarmer.model_cache == mock_cache
    assert prewarmer.enabled == False  # Disabled in test config
    assert prewarmer.running == False


@pytest.mark.asyncio
async def test_record_model_access(test_config):
    """Test recording model access"""
    mock_cache = Mock()
    prewarmer = ModelPrewarmer(mock_cache, test_config)
    
    prewarmer.record_model_access('model-001')
    prewarmer.record_model_access('model-001')
    prewarmer.record_model_access('model-002')
    
    assert 'model-001' in prewarmer.model_access_times
    assert len(prewarmer.model_access_times['model-001']) == 2
    assert len(prewarmer.model_access_times['model-002']) == 1


@pytest.mark.asyncio
async def test_prewarm_model(test_config):
    """Test manual model pre-warming"""
    mock_cache = Mock()
    mock_cache.get_model = AsyncMock(return_value='/path/to/model')
    
    prewarmer = ModelPrewarmer(mock_cache, test_config)
    
    await prewarmer.prewarm_model('model-001')
    
    mock_cache.get_model.assert_called_once_with('model-001')


@pytest.mark.asyncio
async def test_prewarm_popular_models(test_config):
    """Test pre-warming popular models"""
    mock_cache = Mock()
    mock_cache.get_model = AsyncMock(return_value='/path/to/model')
    
    config = test_config.copy()
    config['prewarming'] = {
        'enabled': True,
        'popular_models': ['model-001', 'model-002']
    }
    
    prewarmer = ModelPrewarmer(mock_cache, config)
    
    await prewarmer.start()
    await asyncio.sleep(0.1)  # Give it time to start
    await prewarmer.stop()
    
    # Should have attempted to pre-warm both models
    assert mock_cache.get_model.call_count >= 2

