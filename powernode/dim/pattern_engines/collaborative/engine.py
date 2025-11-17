"""
Collaborative Inference Engine
Same model on different data sets (data parallel)
"""

import asyncio
from typing import Dict, List
import sys
from pathlib import Path

# Add base engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'base'))
from base_engine import BasePatternEngine
from orchestrator.src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CollaborativeEngine(BasePatternEngine):
    """
    Collaborative Inference: Same model on different data sets
    
    Use case: Drug discovery across multiple hospitals
    """
    
    async def validate_spec(self, spec: Dict) -> Dict:
        """Validate collaborative pattern spec"""
        required = ['model_id', 'nodes', 'aggregation']
        
        for field in required:
            if field not in spec.get('config', {}):
                return {'valid': False, 'error': f"Missing field: {field}"}
        
        config = spec.get('config', {})
        if len(config.get('nodes', [])) < 2:
            return {'valid': False, 'error': "Collaborative requires at least 2 nodes"}
        
        return {'valid': True}
    
    async def execute_pattern(self, job_id: str, spec: Dict) -> List[Dict]:
        """
        Execute collaborative pattern
        
        Steps:
        1. Distribute same model to all nodes
        2. Execute in parallel
        3. Collect results
        """
        config = spec.get('config', {})
        model_id = config['model_id']
        nodes = config['nodes']
        
        logger.info(f"Executing collaborative pattern: job={job_id}, model={model_id}, nodes={len(nodes)}")
        
        # Create job spec for each node
        node_jobs = []
        for node_id in nodes:
            node_job = {
                'job_id': f"{job_id}-{node_id}",
                'model_id': model_id,
                'data_requirements': config.get('data_requirements', {}),
                'timeout': config.get('timeout', 120)
            }
            node_jobs.append((node_id, node_job))
        
        # Execute in parallel
        tasks = [
            self.send_to_daemon(node_id, job_spec)
            for node_id, job_spec in node_jobs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Node {nodes[i]} failed: {result}")
            else:
                valid_results.append({
                    'node_id': nodes[i],
                    'result': result
                })
        
        logger.info(f"Collaborative pattern completed: {len(valid_results)}/{len(nodes)} nodes succeeded")
        return valid_results
    
    async def aggregate_results(self, job_id: str, results: List[Dict]) -> Dict:
        """
        Aggregate results using specified method
        
        Supports:
        - Federated averaging
        - Weighted average
        - Median
        - Differential privacy
        """
        # Load job spec to get aggregation config
        job_spec = await self.load_job_spec(job_id)
        if not job_spec:
            # Fallback to default
            agg_config = {'method': 'federated_averaging'}
        else:
            agg_config = job_spec.get('config', {}).get('aggregation', {'method': 'federated_averaging'})
        
        method = agg_config.get('method', 'federated_averaging')
        
        logger.info(f"Aggregating {len(results)} results using method: {method}")
        
        # Simple aggregation (for Phase 1)
        # In Phase 2, implement proper federated averaging, etc.
        if method == 'federated_averaging':
            # For now, just combine results
            aggregated = {
                'method': 'federated_averaging',
                'node_results': results,
                'node_count': len(results),
                'aggregated_output': 'mock_aggregated_result'  # Placeholder
            }
        elif method == 'weighted_average':
            aggregated = {
                'method': 'weighted_average',
                'node_results': results,
                'node_count': len(results),
                'aggregated_output': 'mock_weighted_average'  # Placeholder
            }
        else:
            # Default: simple combination
            aggregated = {
                'method': method,
                'node_results': results,
                'node_count': len(results),
                'aggregated_output': 'mock_result'
            }
        
        return {
            'pattern': 'collaborative',
            'job_id': job_id,
            'aggregation': aggregated,
            'nodes_used': [r['node_id'] for r in results]
        }

