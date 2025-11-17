"""
Chained Inference Engine
Sequential pipeline of models (workflow)
"""

from typing import Dict, List
import sys
from pathlib import Path

# Add base engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'base'))
from base_engine import BasePatternEngine
from orchestrator.src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ChainedEngine(BasePatternEngine):
    """
    Chained Inference: Sequential pipeline of models
    
    Use case: Triage → Diagnosis → Treatment → Medication review
    """
    
    async def validate_spec(self, spec: Dict) -> Dict:
        """Validate chained pattern spec"""
        config = spec.get('config', {})
        
        if 'pipeline' not in config:
            return {'valid': False, 'error': "Missing pipeline"}
        
        pipeline = config['pipeline']
        
        if len(pipeline) < 2:
            return {'valid': False, 'error': "Chained requires at least 2 steps"}
        
        # Validate dependencies (step N+1 depends on step N)
        for i, step in enumerate(pipeline):
            if 'step' not in step or step['step'] != i + 1:
                return {'valid': False, 'error': f"Invalid step numbering at index {i}"}
        
        return {'valid': True}
    
    async def execute_pattern(self, job_id: str, spec: Dict) -> List[Dict]:
        """
        Execute chained pattern
        
        Steps:
        1. Execute steps in order
        2. Pass output of step N to step N+1
        3. Handle failures/rollback
        """
        config = spec.get('config', {})
        pipeline = config['pipeline']
        
        logger.info(f"Executing chained pattern: job={job_id}, steps={len(pipeline)}")
        
        results = []
        previous_output = None
        
        for step in pipeline:
            step_num = step['step']
            
            logger.info(f"Executing step {step_num}: {step.get('name', 'unnamed')}")
            
            # Prepare job spec
            job_spec = {
                'job_id': f"{job_id}-step-{step_num}",
                'model_id': step['model_id'],
                'timeout': step.get('timeout', 120)
            }
            
            # Input source
            if step.get('input_source') == 'client_data':
                job_spec['input_data'] = spec.get('input_data')
            elif previous_output is not None:
                job_spec['input_data'] = previous_output
            else:
                job_spec['input_data'] = {}
            
            # Execute step
            try:
                result = await self.send_to_daemon(step['node_id'], job_spec)
                
                results.append({
                    'step': step_num,
                    'name': step['name'],
                    'result': result
                })
                
                previous_output = result
                
            except Exception as e:
                # Handle failure
                error_handling = config.get('error_handling', {})
                
                if error_handling.get('on_failure') == 'rollback_and_retry':
                    # Retry logic (simplified for Phase 1)
                    logger.warning(f"Step {step_num} failed, retrying: {e}")
                    # For Phase 1, just fail
                    raise
                else:
                    # Fail entire pipeline
                    logger.error(f"Step {step_num} failed, failing pipeline: {e}")
                    raise
        
        logger.info(f"Chained pattern completed: {len(results)}/{len(pipeline)} steps succeeded")
        return results
    
    async def aggregate_results(self, job_id: str, results: List[Dict]) -> Dict:
        """
        Compile final result from last step
        
        Also includes all intermediate results for transparency
        """
        return {
            'pattern': 'chained',
            'job_id': job_id,
            'final_output': results[-1]['result'] if results else None,
            'pipeline_trace': results,
            'total_steps': len(results),
            'steps_completed': [r['step'] for r in results]
        }

