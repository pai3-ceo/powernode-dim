"""
IPFS State Management for DIM
Handles IPNS for mutable state and Pubsub for coordination
"""

import json
import asyncio
from typing import Dict, Optional, Any, Callable
from datetime import datetime
from .client import DIMIPFSClient
from .pubsub import IPFSPubsub
from .ipns import IPNSManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class IPFSStateManager:
    """Manages DIM state via IPFS, IPNS, and Pubsub"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize state manager
        
        Args:
            config: Configuration dictionary with IPFS settings
        """
        ipfs_api = config.get('ipfs', {}).get('api_url', '/ip4/127.0.0.1/tcp/5001')
        
        # Convert multiaddr to HTTP URL if needed
        if ipfs_api.startswith("/ip4/"):
            parts = ipfs_api.split("/")
            host = parts[2]
            port = parts[4]
            api_base = f"http://{host}:{port}/api/v0"
        else:
            api_base = ipfs_api if ipfs_api.endswith('/api/v0') else f"{ipfs_api}/api/v0"
        
        self.client = DIMIPFSClient(ipfs_api)
        self.api_base = api_base
        
        # IPNS configuration
        self.registry_ipns = config.get('ipfs', {}).get('registry_ipns')
        self.ipns_key_name = config.get('ipfs', {}).get('ipns_key_name', 'dim-state-key')
        
        # Initialize IPNS manager
        try:
            self.ipns = IPNSManager(api_base, self.ipns_key_name)
        except Exception as e:
            logger.warning(f"Failed to initialize IPNS manager: {e}. IPNS features disabled.")
            self.ipns = None
        
        # Pubsub configuration
        self.pubsub_topics = config.get('ipfs', {}).get('pubsub', {
            'job_updates': 'dim.jobs.updates',
            'node_heartbeat': 'dim.nodes.heartbeat',
            'results_ready': 'dim.results.ready'
        })
        
        # Initialize Pubsub
        try:
            self.pubsub = IPFSPubsub(api_base)
        except Exception as e:
            logger.warning(f"Failed to initialize IPFS Pubsub: {e}. Pubsub features disabled.")
            self.pubsub = None
        
        # Active jobs state (IPNS)
        self.active_jobs_ipns = None
        
        logger.info("IPFS State Manager initialized")
    
    async def save_job_spec(self, job_id: str, spec: Dict[str, Any]) -> str:
        """Save job specification to IPFS"""
        return await self.client.save_job_spec(job_id, spec)
    
    async def save_job_result(self, job_id: str, result: Dict[str, Any]) -> str:
        """Save job result to IPFS"""
        return await self.client.save_job_result(job_id, result)
    
    async def update_job_status(self, job_id: str, state: str, **kwargs):
        """
        Update job status in IPFS (via IPNS for mutable state)
        
        Args:
            job_id: Job identifier
            state: New state
            **kwargs: Additional status fields
        """
        status_data = {
            'job_id': job_id,
            'state': state,
            'updated_at': datetime.now().isoformat(),
            **kwargs
        }
        
        # Save to IPFS
        cid = await self.client.save_job_result(job_id, status_data)
        
        # Update active jobs state via IPNS (if enabled)
        if self.ipns:
            await self._update_active_jobs_state(job_id, state, status_data)
    
    async def _update_active_jobs_state(self, job_id: str, state: str, status_data: Dict):
        """Update active jobs state via IPNS"""
        try:
            # Load current active jobs state
            active_jobs = await self.get_active_jobs_state()
            
            # Update job entry
            active_jobs['jobs'][job_id] = {
                'state': state,
                'updated_at': datetime.now().isoformat(),
                **status_data
            }
            
            # Update timestamp
            active_jobs['updated_at'] = datetime.now().isoformat()
            
            # Publish to IPNS
            self.ipns.update_state(active_jobs, lifetime="1h")
            
        except Exception as e:
            logger.warning(f"Failed to update active jobs state via IPNS: {e}")
    
    async def load_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Load job status from IPFS/IPNS
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary or None
        """
        # Try to get from active jobs state (IPNS)
        if self.ipns:
            active_jobs = await self.get_active_jobs_state()
            if job_id in active_jobs.get('jobs', {}):
                return active_jobs['jobs'][job_id]
        
        # Fallback: try to load from IPFS directly
        # (This would require tracking CIDs, which we don't do yet)
        return None
    
    async def get_active_jobs_state(self) -> Dict[str, Any]:
        """
        Get active jobs state from IPNS
        
        Returns:
            Active jobs state dictionary
        """
        if not self.ipns:
            return {'jobs': {}, 'updated_at': datetime.now().isoformat()}
        
        try:
            # Resolve active jobs IPNS
            if not self.active_jobs_ipns:
                # Try to resolve from registry IPNS or use default
                ipns_name = self.registry_ipns or f"/ipns/{self.ipns.get_key_id()}"
                state = self.ipns.get_state(ipns_name)
                
                if state:
                    self.active_jobs_ipns = ipns_name
                    return state
            
            # Get state from known IPNS
            state = self.ipns.get_state(self.active_jobs_ipns)
            if state:
                return state
            
            # Return empty state if not found
            return {'jobs': {}, 'updated_at': datetime.now().isoformat()}
            
        except Exception as e:
            logger.warning(f"Failed to get active jobs state: {e}")
            return {'jobs': {}, 'updated_at': datetime.now().isoformat()}
    
    async def publish_job_event(self, job_id: str, event_type: str, data: Dict[str, Any]):
        """
        Publish job event via IPFS Pubsub
        
        Args:
            job_id: Job identifier
            event_type: Event type (e.g., 'completed', 'failed')
            data: Event data
        """
        if not self.pubsub:
            logger.debug("Pubsub not available, skipping event publish")
            return
        
        topic = self.pubsub_topics.get('job_updates', 'dim.jobs.updates')
        
        message = {
            'job_id': job_id,
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Publish via IPFS Pubsub
        await self.pubsub.publish(topic, message)
        logger.debug(f"Published job event: {job_id} -> {event_type}")
    
    async def subscribe_to_job_updates(self, handler: Callable[[Dict], None]):
        """
        Subscribe to job update events
        
        Args:
            handler: Async function to handle job updates
                    Signature: async def handler(message: Dict) -> None
        """
        if not self.pubsub:
            logger.warning("Pubsub not available, cannot subscribe to job updates")
            return
        
        topic = self.pubsub_topics.get('job_updates', 'dim.jobs.updates')
        await self.pubsub.subscribe(topic, handler)
    
    async def publish_node_heartbeat(self, node_id: str, heartbeat_data: Dict):
        """
        Publish node heartbeat via IPFS Pubsub
        
        Args:
            node_id: Node identifier
            heartbeat_data: Heartbeat data dictionary
        """
        if not self.pubsub:
            return
        
        topic = self.pubsub_topics.get('node_heartbeat', 'dim.nodes.heartbeat')
        
        message = {
            'node_id': node_id,
            'timestamp': datetime.now().isoformat(),
            **heartbeat_data
        }
        
        await self.pubsub.publish(topic, message)
    
    async def subscribe_to_node_heartbeats(self, handler: Callable[[Dict], None]):
        """
        Subscribe to node heartbeat events
        
        Args:
            handler: Async function to handle heartbeats
        """
        if not self.pubsub:
            return
        
        topic = self.pubsub_topics.get('node_heartbeat', 'dim.nodes.heartbeat')
        await self.pubsub.subscribe(topic, handler)
    
    async def publish_result_ready(self, job_id: str, result_cid: str):
        """
        Publish result ready event
        
        Args:
            job_id: Job identifier
            result_cid: IPFS CID of result
        """
        if not self.pubsub:
            return
        
        topic = self.pubsub_topics.get('results_ready', 'dim.results.ready')
        
        message = {
            'job_id': job_id,
            'result_cid': result_cid,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.pubsub.publish(topic, message)
    
    async def update_node_registry(self, registry_data: Dict) -> Optional[str]:
        """
        Update node registry via IPNS
        
        Args:
            registry_data: Node registry data dictionary
            
        Returns:
            IPNS name if successful
        """
        if not self.ipns:
            logger.warning("IPNS not available, cannot update node registry")
            return None
        
        try:
            # Add updated timestamp
            registry_data['updated_at'] = datetime.now().isoformat()
            
            # Update via IPNS
            ipns_name = self.ipns.update_state(registry_data, lifetime="7d")
            
            logger.info(f"Updated node registry via IPNS: {ipns_name}")
            return ipns_name
            
        except Exception as e:
            logger.error(f"Failed to update node registry: {e}")
            return None
    
    async def get_node_registry(self) -> Optional[Dict]:
        """
        Get node registry from IPNS
        
        Returns:
            Node registry dictionary or None
        """
        if not self.ipns:
            return None
        
        try:
            # Resolve registry IPNS
            ipns_name = self.registry_ipns or f"/ipns/{self.ipns.get_key_id()}"
            registry = self.ipns.get_state(ipns_name)
            
            return registry
            
        except Exception as e:
            logger.warning(f"Failed to get node registry: {e}")
            return None
    
    async def stop(self):
        """Stop state manager (unsubscribe from pubsub)"""
        if self.pubsub:
            await self.pubsub.stop()
        logger.info("IPFS State Manager stopped")

