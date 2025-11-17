"""
Resource Manager - Manages CPU, Memory, GPU resources
"""

import psutil
from typing import Dict, Optional
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class ResourceManager:
    """Manages system resources"""
    
    def __init__(self, config: Dict):
        """
        Initialize resource manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Resource limits
        self.max_concurrent_jobs = config.get('max_concurrent_jobs', 10)
        self.max_memory_gb = config.get('max_memory_gb', 64)
        self.max_cpu_percent = config.get('max_cpu_percent', 80)
        
        # Current usage
        self.active_jobs = 0
        
        logger.info(f"Resource manager initialized: max_jobs={self.max_concurrent_jobs}, max_memory={self.max_memory_gb}GB")
    
    def can_accept_job(self, job_spec: Dict) -> bool:
        """
        Check if system can accept new job
        
        Args:
            job_spec: Job specification
            
        Returns:
            True if can accept job
        """
        # Check concurrent jobs limit
        if self.active_jobs >= self.max_concurrent_jobs:
            logger.warning(f"Cannot accept job: max concurrent jobs ({self.max_concurrent_jobs}) reached")
            return False
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_gb_used = memory.used / (1024 ** 3)
        memory_gb_available = memory.available / (1024 ** 3)
        
        if memory_gb_used > self.max_memory_gb * 0.9:  # 90% threshold
            logger.warning(f"Cannot accept job: memory usage ({memory_gb_used:.1f}GB) too high")
            return False
        
        # Check CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > self.max_cpu_percent:
            logger.warning(f"Cannot accept job: CPU usage ({cpu_percent}%) too high")
            return False
        
        return True
    
    def reserve_resources(self, job_id: str):
        """Reserve resources for job"""
        self.active_jobs += 1
        logger.debug(f"Resources reserved for job {job_id} (active_jobs={self.active_jobs})")
    
    def release_resources(self, job_id: str):
        """Release resources for job"""
        if self.active_jobs > 0:
            self.active_jobs -= 1
        logger.debug(f"Resources released for job {job_id} (active_jobs={self.active_jobs})")
    
    def get_status(self) -> Dict:
        """Get current resource status"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return {
            'active_jobs': self.active_jobs,
            'max_concurrent_jobs': self.max_concurrent_jobs,
            'memory_used_gb': memory.used / (1024 ** 3),
            'memory_available_gb': memory.available / (1024 ** 3),
            'memory_percent': memory.percent,
            'cpu_percent': cpu_percent,
            'cpu_count': psutil.cpu_count()
        }

