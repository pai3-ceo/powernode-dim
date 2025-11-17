"""
Job Queue - Manages job scheduling and queuing
"""

import asyncio
from typing import Dict, Optional, Tuple
from collections import deque
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class JobQueue:
    """Job queue with priority support"""
    
    def __init__(self, config: Dict):
        """
        Initialize job queue
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.max_size = config.get('max_queue_size', 1000)
        
        # Priority queues: high, normal, low
        self.queues = {
            'high': deque(),
            'normal': deque(),
            'low': deque()
        }
        
        # Queue lock
        self.lock = asyncio.Lock()
        
        # Condition for waiting on jobs
        self.condition = asyncio.Condition(self.lock)
        
        logger.info(f"Job queue initialized (max_size={self.max_size})")
    
    async def enqueue(self, job_id: str, job_spec: Dict):
        """
        Add job to queue
        
        Args:
            job_id: Job identifier
            job_spec: Job specification
        """
        priority = job_spec.get('priority', 'normal')
        if priority not in self.queues:
            priority = 'normal'
        
        async with self.lock:
            if self.size() >= self.max_size:
                raise QueueFullError(f"Queue is full (max_size={self.max_size})")
            
            self.queues[priority].append((job_id, job_spec))
            logger.debug(f"Job {job_id} enqueued with priority {priority}")
            
            # Notify waiting dequeue
            self.condition.notify()
    
    async def dequeue(self) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Get next job from queue (priority order: high, normal, low)
        
        Returns:
            (job_id, job_spec) or (None, None) if empty
        """
        async with self.lock:
            # Wait for job if queue is empty
            while self.size() == 0:
                await self.condition.wait()
            
            # Get job from highest priority queue
            for priority in ['high', 'normal', 'low']:
                if self.queues[priority]:
                    job_id, job_spec = self.queues[priority].popleft()
                    logger.debug(f"Job {job_id} dequeued from {priority} queue")
                    return job_id, job_spec
            
            return None, None
    
    def size(self) -> int:
        """Get total queue size"""
        return sum(len(q) for q in self.queues.values())
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            'total': self.size(),
            'high': len(self.queues['high']),
            'normal': len(self.queues['normal']),
            'low': len(self.queues['low']),
            'max_size': self.max_size
        }


class QueueFullError(Exception):
    """Raised when queue is full"""
    pass

