"""
Orchestrator Coordinator - Coordinates multiple orchestrators via IPFS Pubsub
"""

import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .ipfs.state_manager import IPFSStateManager
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class OrchestratorCoordinator:
    """Coordinates multiple orchestrators for distributed job execution"""
    
    def __init__(self, orchestrator_id: str, state_manager: IPFSStateManager, config: Dict):
        """
        Initialize orchestrator coordinator
        
        Args:
            orchestrator_id: Unique orchestrator identifier
            state_manager: IPFS state manager
            config: Configuration dictionary
        """
        self.orchestrator_id = orchestrator_id
        self.state_manager = state_manager
        self.config = config
        
        # Coordination topics
        self.coordination_topic = config.get('orchestrator', {}).get('coordination_topic', 'dim.orchestrators.coordination')
        self.heartbeat_topic = config.get('orchestrator', {}).get('heartbeat_topic', 'dim.orchestrators.heartbeat')
        
        # Known orchestrators
        self.known_orchestrators: Dict[str, datetime] = {}  # orchestrator_id -> last_seen
        self.heartbeat_interval = config.get('orchestrator', {}).get('heartbeat_interval_seconds', 30)
        self.heartbeat_timeout = config.get('orchestrator', {}).get('heartbeat_timeout_seconds', 90)
        
        # Job distribution
        self.local_job_count = 0
        self.running = False
        
        logger.info(f"Orchestrator Coordinator initialized: {self.orchestrator_id}")
    
    async def start(self):
        """Start coordinator services"""
        if self.running:
            return
        
        self.running = True
        
        # Subscribe to orchestrator heartbeats
        if self.state_manager.pubsub:
            await self.state_manager.pubsub.subscribe(
                self.heartbeat_topic,
                self._handle_orchestrator_heartbeat
            )
            
            # Subscribe to coordination messages
            await self.state_manager.pubsub.subscribe(
                self.coordination_topic,
                self._handle_coordination_message
            )
        
        # Start heartbeat publishing
        asyncio.create_task(self._heartbeat_loop())
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_stale_orchestrators())
        
        logger.info("Orchestrator Coordinator started")
    
    async def stop(self):
        """Stop coordinator services"""
        self.running = False
        logger.info("Orchestrator Coordinator stopped")
    
    async def _handle_orchestrator_heartbeat(self, message: Dict):
        """Handle orchestrator heartbeat"""
        try:
            orchestrator_id = message.get('orchestrator_id')
            if not orchestrator_id or orchestrator_id == self.orchestrator_id:
                return  # Ignore own heartbeat
            
            # Update known orchestrators
            self.known_orchestrators[orchestrator_id] = datetime.now()
            
            logger.debug(f"Received heartbeat from orchestrator {orchestrator_id}")
            
        except Exception as e:
            logger.error(f"Error handling orchestrator heartbeat: {e}", exc_info=True)
    
    async def _handle_coordination_message(self, message: Dict):
        """Handle coordination message from other orchestrators"""
        try:
            message_type = message.get('type')
            orchestrator_id = message.get('orchestrator_id')
            
            if orchestrator_id == self.orchestrator_id:
                return  # Ignore own messages
            
            if message_type == 'job_distribution_request':
                # Another orchestrator is requesting job distribution info
                await self._respond_to_distribution_request(orchestrator_id)
            
            elif message_type == 'job_assignment':
                # Another orchestrator is assigning a job to us
                job_id = message.get('job_id')
                logger.info(f"Received job assignment from {orchestrator_id}: {job_id}")
                # This would trigger job execution in the orchestrator
            
        except Exception as e:
            logger.error(f"Error handling coordination message: {e}", exc_info=True)
    
    async def _heartbeat_loop(self):
        """Publish orchestrator heartbeat"""
        while self.running:
            try:
                heartbeat = {
                    'orchestrator_id': self.orchestrator_id,
                    'active_jobs': self.local_job_count,
                    'timestamp': datetime.now().isoformat()
                }
                
                if self.state_manager.pubsub:
                    await self.state_manager.pubsub.publish(self.heartbeat_topic, heartbeat)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)
                await asyncio.sleep(self.heartbeat_interval)
    
    async def _cleanup_stale_orchestrators(self):
        """Remove orchestrators that haven't sent heartbeats"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.now()
                timeout = timedelta(seconds=self.heartbeat_timeout)
                
                stale = []
                for orchestrator_id, last_seen in self.known_orchestrators.items():
                    if now - last_seen > timeout:
                        stale.append(orchestrator_id)
                
                for orchestrator_id in stale:
                    del self.known_orchestrators[orchestrator_id]
                    logger.info(f"Orchestrator {orchestrator_id} marked as stale")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)
    
    async def _respond_to_distribution_request(self, requesting_orchestrator_id: str):
        """Respond to job distribution request"""
        try:
            response = {
                'type': 'job_distribution_response',
                'orchestrator_id': self.orchestrator_id,
                'active_jobs': self.local_job_count,
                'capacity': self._estimate_capacity(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Send response via coordination topic
            if self.state_manager.pubsub:
                await self.state_manager.pubsub.publish(self.coordination_topic, response)
            
        except Exception as e:
            logger.error(f"Error responding to distribution request: {e}", exc_info=True)
    
    def _estimate_capacity(self) -> int:
        """
        Estimate how many more jobs this orchestrator can handle
        
        Returns:
            Estimated capacity
        """
        # Simple estimation based on current load
        max_jobs = self.config.get('orchestrator', {}).get('max_concurrent_jobs', 100)
        return max(0, max_jobs - self.local_job_count)
    
    async def get_active_orchestrators(self) -> List[str]:
        """
        Get list of active orchestrator IDs
        
        Returns:
            List of orchestrator IDs
        """
        now = datetime.now()
        timeout = timedelta(seconds=self.heartbeat_timeout)
        
        active = []
        for orchestrator_id, last_seen in self.known_orchestrators.items():
            if now - last_seen < timeout:
                active.append(orchestrator_id)
        
        # Include self
        active.append(self.orchestrator_id)
        
        return active
    
    async def select_orchestrator_for_job(self, job_id: str, job_spec: Dict) -> Optional[str]:
        """
        Select best orchestrator for a job (load balancing)
        
        Args:
            job_id: Job identifier
            job_spec: Job specification
            
        Returns:
            Selected orchestrator ID or None (use local)
        """
        active_orchestrators = await self.get_active_orchestrators()
        
        if len(active_orchestrators) <= 1:
            # Only us, handle locally
            return None
        
        # Request distribution info from other orchestrators
        request = {
            'type': 'job_distribution_request',
            'orchestrator_id': self.orchestrator_id,
            'job_id': job_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.state_manager.pubsub:
            await self.state_manager.pubsub.publish(self.coordination_topic, request)
        
        # Wait for responses (simplified - in production would use proper async response handling)
        await asyncio.sleep(2)  # Give time for responses
        
        # For now, use simple round-robin or load-based selection
        # In production, would collect responses and select best orchestrator
        
        # Simple heuristic: if we're not too loaded, handle locally
        if self.local_job_count < 50:  # Threshold
            return None
        
        # Otherwise, select another orchestrator (round-robin)
        other_orchestrators = [o for o in active_orchestrators if o != self.orchestrator_id]
        if other_orchestrators:
            # Simple round-robin
            selected = other_orchestrators[self.local_job_count % len(other_orchestrators)]
            return selected
        
        return None
    
    async def assign_job_to_orchestrator(self, orchestrator_id: str, job_id: str, job_spec: Dict):
        """
        Assign job to another orchestrator
        
        Args:
            orchestrator_id: Target orchestrator ID
            job_id: Job identifier
            job_spec: Job specification
        """
        if orchestrator_id == self.orchestrator_id:
            return  # Don't assign to self
        
        assignment = {
            'type': 'job_assignment',
            'orchestrator_id': self.orchestrator_id,
            'target_orchestrator_id': orchestrator_id,
            'job_id': job_id,
            'job_spec': job_spec,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.state_manager.pubsub:
            await self.state_manager.pubsub.publish(self.coordination_topic, assignment)
        logger.info(f"Assigned job {job_id} to orchestrator {orchestrator_id}")
    
    def update_job_count(self, count: int):
        """Update local job count"""
        self.local_job_count = count

