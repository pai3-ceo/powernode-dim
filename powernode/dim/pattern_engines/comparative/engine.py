"""
Comparative Inference Engine
Different models on same data set (model parallel)
"""

from typing import Dict, List
import sys
from pathlib import Path

# Add base engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'base'))
from base_engine import BasePatternEngine
from orchestrator.src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ComparativeEngine(BasePatternEngine):
    """
    Comparative Inference: Different models on same data set
    
    Use case: Multiple diagnostic models on patient data
    """
    
    async def validate_spec(self, spec: Dict) -> Dict:
        """Validate comparative pattern spec"""
        config = spec.get('config', {})
        required = ['model_ids', 'node_id', 'consensus']
        
        for field in required:
            if field not in config:
                return {'valid': False, 'error': f"Missing field: {field}"}
        
        if len(config.get('model_ids', [])) < 2:
            return {'valid': False, 'error': "Comparative requires at least 2 models"}
        
        return {'valid': True}
    
    async def execute_pattern(self, job_id: str, spec: Dict) -> List[Dict]:
        """
        Execute comparative pattern
        
        Steps:
        1. Load all models on single node
        2. Execute sequentially or in parallel
        3. Collect model outputs
        """
        config = spec.get('config', {})
        model_ids = config['model_ids']
        node_id = config['node_id']
        data_source = config.get('data_source')
        
        logger.info(f"Executing comparative pattern: job={job_id}, models={len(model_ids)}, node={node_id}")
        
        # Create jobs for each model
        results = []
        for model_id in model_ids:
            job_spec = {
                'job_id': f"{job_id}-{model_id}",
                'model_id': model_id,
                'data_source': data_source,
                'timeout': config.get('timeout', 120)
            }
            
            result = await self.send_to_daemon(node_id, job_spec)
            results.append({
                'model_id': model_id,
                'result': result
            })
        
        logger.info(f"Comparative pattern completed: {len(results)}/{len(model_ids)} models succeeded")
        return results
    
    async def aggregate_results(self, job_id: str, results: List[Dict]) -> Dict:
        """
        Build consensus from multiple model results
        
        Supports:
        - Majority vote
        - Weighted vote (by model reputation)
        - Expert review (if no consensus)
        """
        # Load job spec to get consensus config
        job_spec = await self.load_job_spec(job_id)
        if not job_spec:
            consensus_config = {'method': 'weighted_vote', 'min_agreement': 0.75}
        else:
            consensus_config = job_spec.get('config', {}).get('consensus', {'method': 'weighted_vote', 'min_agreement': 0.75})
        
        method = consensus_config.get('method', 'weighted_vote')
        min_agreement = consensus_config.get('min_agreement', 0.75)
        
        logger.info(f"Building consensus using method: {method}, min_agreement: {min_agreement}")
        
        # Simple consensus building (for Phase 1)
        # In Phase 2, implement proper consensus algorithms
        if method == 'majority_vote':
            # Count votes (simplified)
            consensus_result = {
                'method': 'majority_vote',
                'model_results': results,
                'consensus_output': 'mock_majority_result',
                'agreement_level': 0.8  # Placeholder
            }
        elif method == 'weighted_vote':
            # Weight by model reputation (simplified)
            consensus_result = {
                'method': 'weighted_vote',
                'model_results': results,
                'consensus_output': 'mock_weighted_result',
                'agreement_level': 0.85  # Placeholder
            }
        else:
            # Default: simple combination
            consensus_result = {
                'method': method,
                'model_results': results,
                'consensus_output': 'mock_consensus_result',
                'agreement_level': 0.75
            }
        
        return {
            'pattern': 'comparative',
            'job_id': job_id,
            'consensus': consensus_result,
            'models_used': [r['model_id'] for r in results]
        }

