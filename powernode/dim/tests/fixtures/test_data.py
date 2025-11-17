"""
Test data fixtures
"""

from datetime import datetime
from typing import Dict, List


def get_sample_job_specs() -> Dict[str, Dict]:
    """Get sample job specifications for all patterns"""
    return {
        'collaborative': {
            'pattern': 'collaborative',
            'config': {
                'model_id': 'test-model-001',
                'nodes': ['node-001', 'node-002'],
                'aggregation': {'method': 'federated_averaging'}
            },
            'priority': 'normal',
            'max_cost': 1000
        },
        'comparative': {
            'pattern': 'comparative',
            'config': {
                'model_ids': ['model-001', 'model-002'],
                'node_id': 'node-001',
                'data_source': 'cabinet-001',
                'consensus': {'method': 'weighted_vote', 'minAgreement': 0.75}
            },
            'priority': 'normal',
            'max_cost': 1000
        },
        'chained': {
            'pattern': 'chained',
            'config': {
                'pipeline': [
                    {
                        'step': 1,
                        'name': 'Step1',
                        'model_id': 'model-001',
                        'node_id': 'node-001',
                        'input_source': 'client_data',
                        'timeout': 60
                    },
                    {
                        'step': 2,
                        'name': 'Step2',
                        'model_id': 'model-002',
                        'node_id': 'node-001',
                        'input_source': 'step_1_output',
                        'timeout': 60
                    }
                ]
            },
            'priority': 'normal',
            'max_cost': 1000
        }
    }


def get_sample_nodes() -> List[Dict]:
    """Get sample node configurations"""
    return [
        {
            'node_id': 'node-001',
            'status': 'active',
            'reputation': 0.95,
            'node_type': 'power',
            'data_types': ['medical', 'legal'],
            'cached_models': ['model-001'],
            'cpu_available': 20,
            'memory_available': 64,
            'gpu_available': True,
            'tailscale_ip': '100.64.1.1',
            'last_heartbeat': datetime.now().isoformat(),
            'registered_at': datetime.now().isoformat()
        },
        {
            'node_id': 'node-002',
            'status': 'active',
            'reputation': 0.90,
            'node_type': 'power',
            'data_types': ['medical', 'financial'],
            'cached_models': ['model-002'],
            'cpu_available': 20,
            'memory_available': 64,
            'gpu_available': True,
            'tailscale_ip': '100.64.1.2',
            'last_heartbeat': datetime.now().isoformat(),
            'registered_at': datetime.now().isoformat()
        }
    ]


def get_sample_models() -> List[Dict]:
    """Get sample model configurations"""
    return [
        {
            'model_id': 'model-001',
            'format': 'mlx',
            'size_mb': 100,
            'framework': 'mlx'
        },
        {
            'model_id': 'model-002',
            'format': 'coreml',
            'size_mb': 200,
            'framework': 'coreml'
        }
    ]

