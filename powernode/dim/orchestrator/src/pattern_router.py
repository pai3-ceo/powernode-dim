"""
Pattern Router - Routes jobs to appropriate pattern engine
"""

from typing import Dict
import httpx
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class PatternRouter:
    """Routes jobs to appropriate pattern engine"""
    
    def __init__(self, config: Dict):
        """
        Initialize pattern router
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Pattern engine endpoints (Phase 1: localhost)
        engines_config = config.get('orchestrator', {}).get('engines', {})
        self.engines = {
            'collaborative': engines_config.get('collaborative', 'http://localhost:8001'),
            'comparative': engines_config.get('comparative', 'http://localhost:8002'),
            'chained': engines_config.get('chained', 'http://localhost:8003')
        }
        
        logger.info(f"Pattern router initialized with engines: {self.engines}")
    
    def get_engine(self, pattern: str) -> 'PatternEngineClient':
        """
        Get pattern engine client for given pattern type
        
        Args:
            pattern: Pattern type ('collaborative', 'comparative', 'chained')
            
        Returns:
            PatternEngineClient instance
            
        Raises:
            ValueError: If pattern is unknown
        """
        endpoint = self.engines.get(pattern)
        if not endpoint:
            raise ValueError(f"Unknown pattern: {pattern}. Available: {list(self.engines.keys())}")
        
        return PatternEngineClient(endpoint, pattern)


class PatternEngineClient:
    """HTTP client for pattern engine"""
    
    def __init__(self, endpoint: str, pattern: str):
        """
        Initialize pattern engine client
        
        Args:
            endpoint: Pattern engine HTTP endpoint
            pattern: Pattern type
        """
        self.endpoint = endpoint
        self.pattern = pattern
        self.client = httpx.AsyncClient(timeout=300.0)
        logger.info(f"Pattern engine client created for {pattern} at {endpoint}")
    
    async def execute(self, job_id: str, spec: Dict) -> Dict:
        """
        Execute job on pattern engine
        
        Args:
            job_id: Job identifier
            spec: Job specification dictionary
            
        Returns:
            Execution result
        """
        try:
            response = await self.client.post(
                f"{self.endpoint}/execute",
                json={
                    'job_id': job_id,
                    'spec': spec
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to execute job {job_id} on {self.pattern} engine: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing job {job_id}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if pattern engine is healthy
        
        Returns:
            True if healthy
        """
        try:
            response = await self.client.get(f"{self.endpoint}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

