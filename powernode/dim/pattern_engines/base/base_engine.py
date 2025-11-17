"""
Base Pattern Engine - Abstract base class for all pattern engines
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

# Add orchestrator models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'orchestrator' / 'src'))

from orchestrator.src.ipfs.client import DIMIPFSClient
from orchestrator.src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BasePatternEngine(ABC):
    """Abstract base class for all pattern engines"""
    
    def __init__(self, config: Dict):
        """
        Initialize pattern engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize IPFS client
        ipfs_api = config.get('ipfs', {}).get('api_url', '/ip4/127.0.0.1/tcp/5001')
        self.ipfs_client = DIMIPFSClient(ipfs_api)
        
        # gRPC clients to daemons (will be created on demand)
        self.grpc_clients = {}
        
        logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    async def validate_spec(self, spec: Dict) -> Dict:
        """
        Validate pattern-specific job specification
        
        Returns:
            {'valid': bool, 'error': str}
        """
        pass
    
    @abstractmethod
    async def execute_pattern(self, job_id: str, spec: Dict) -> List[Dict]:
        """
        Execute pattern-specific inference logic
        
        Args:
            job_id: Job identifier
            spec: Job specification
            
        Returns:
            List of results from nodes/models
        """
        pass
    
    @abstractmethod
    async def aggregate_results(self, job_id: str, results: List[Dict]) -> Dict:
        """
        Aggregate results from multiple nodes/models
        
        Args:
            job_id: Job identifier
            results: List of results to aggregate
            
        Returns:
            Final aggregated result
        """
        pass
    
    async def execute(self, job_id: str, spec: Dict) -> Dict:
        """
        Main execution method (common flow)
        
        Args:
            job_id: Job identifier
            spec: Job specification
            
        Returns:
            Final result dictionary
        """
        # 1. Validate
        validation = await self.validate_spec(spec)
        if not validation['valid']:
            raise ValueError(validation['error'])
        
        # 2. Execute pattern
        results = await self.execute_pattern(job_id, spec)
        
        # 3. Aggregate
        final_result = await self.aggregate_results(job_id, results)
        
        # 4. Save to IPFS
        await self.save_result(job_id, final_result)
        
        return final_result
    
    async def save_result(self, job_id: str, result: Dict):
        """Save result to IPFS"""
        await self.ipfs_client.save_job_result(job_id, result)
    
    async def load_job_spec(self, job_id: str) -> Optional[Dict]:
        """Load job spec from IPFS"""
        return await self.ipfs_client.load_job_spec(job_id)
    
    async def send_to_daemon(self, node_id: str, job_spec: Dict) -> Dict:
        """
        Send job to daemon via gRPC
        
        Args:
            node_id: Node identifier
            job_spec: Job specification for daemon
            
        Returns:
            Result from daemon
        """
        # For Phase 1, this is a placeholder
        # In Phase 2, we'll implement gRPC client
        logger.warning(f"send_to_daemon not yet implemented for node {node_id}")
        
        # Mock response for Phase 1
        return {
            'status': 'completed',
            'result': {'mock': True, 'node_id': node_id},
            'execution_time': '5s'
        }
    
    async def get_node_endpoint(self, node_id: str) -> str:
        """
        Get gRPC endpoint for node
        
        Args:
            node_id: Node identifier
            
        Returns:
            gRPC endpoint address
        """
        # For Phase 1, return localhost
        # In Phase 2, look up from node registry
        return f"localhost:50052"

