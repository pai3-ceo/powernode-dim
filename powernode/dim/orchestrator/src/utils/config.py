"""
Configuration utilities for DIM Orchestrator
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment
    
    Args:
        config_path: Path to config file (default: config/dev.yaml)
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Default to dev config
        config_path = os.path.join(
            Path(__file__).parent.parent.parent.parent,
            'config',
            'dev.yaml'
        )
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        # Default configuration
        config = {
            'orchestrator': {
                'grpc_address': 'localhost:50051',
                'log_level': 'INFO',
                'engines': {
                    'collaborative': 'http://localhost:8001',
                    'comparative': 'http://localhost:8002',
                    'chained': 'http://localhost:8003'
                }
            },
            'ipfs': {
                'api_url': '/ip4/127.0.0.1/tcp/5001',
                'gateway_url': 'http://localhost:8080',
                'pubsub': {
                    'job_updates': 'dim.jobs.updates',
                    'node_heartbeat': 'dim.nodes.heartbeat',
                    'results_ready': 'dim.results.ready'
                }
            }
        }
    
    # Override with environment variables
    if 'DIM_IPFS_API' in os.environ:
        config.setdefault('ipfs', {})['api_url'] = os.environ['DIM_IPFS_API']
    
    if 'DIM_GRPC_ADDRESS' in os.environ:
        config.setdefault('orchestrator', {})['grpc_address'] = os.environ['DIM_GRPC_ADDRESS']
    
    return config

