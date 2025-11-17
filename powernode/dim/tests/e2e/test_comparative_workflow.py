"""
End-to-end test for Comparative pattern workflow
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'orchestrator' / 'src'))

from orchestrator import DIMOrchestrator
from models.job_spec import JobSpec, Pattern, Priority


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_comparative_workflow_complete(test_config, sample_job_spec_comparative):
    """Test complete comparative workflow"""
    orchestrator = DIMOrchestrator(test_config)
    
    with patch('orchestrator.pattern_router.PatternEngineClient') as mock_engine:
        mock_engine.execute = AsyncMock(return_value={
            'result': {'consensus': 'test-result'},
            'models_used': 2
        })
        
        spec = JobSpec(**sample_job_spec_comparative)
        job_id = await orchestrator.submit_job(spec, "test-user-001")
        
        assert job_id is not None

