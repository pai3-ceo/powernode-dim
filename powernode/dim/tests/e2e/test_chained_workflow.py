"""
End-to-end test for Chained pattern workflow
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
async def test_chained_workflow_complete(test_config, sample_job_spec_chained):
    """Test complete chained workflow"""
    orchestrator = DIMOrchestrator(test_config)
    
    with patch('orchestrator.pattern_router.PatternEngineClient') as mock_engine:
        mock_engine.execute = AsyncMock(return_value={
            'result': {'step_output': 'test-result'},
            'steps_completed': 2
        })
        
        spec = JobSpec(**sample_job_spec_chained)
        job_id = await orchestrator.submit_job(spec, "test-user-001")
        
        assert job_id is not None

