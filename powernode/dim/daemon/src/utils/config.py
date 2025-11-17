"""
Configuration utilities for DIM Daemon
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
            Path(__file__).parent.parent.parent.parent.parent,
            'config',
            'dev.yaml'
        )
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        # Default configuration
        config = {
            'daemon': {
                'node_id': 'node-001',
                'grpc_address': 'localhost:50052',
                'log_level': 'INFO',
                'cache_dir': '/var/lib/dim/models',
                'max_cache_gb': 50,
                'max_concurrent_jobs': 10
            },
            'ipfs': {
                'api_url': '/ip4/127.0.0.1/tcp/5001'
            }
        }
    
    # Override with environment variables
    if 'DIM_IPFS_API' in os.environ:
        config.setdefault('ipfs', {})['api_url'] = os.environ['DIM_IPFS_API']
    
    if 'NODE_ID' in os.environ:
        config.setdefault('daemon', {})['node_id'] = os.environ['NODE_ID']
    
    return config

