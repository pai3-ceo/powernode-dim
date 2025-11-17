"""
DIM Daemon - Receives jobs, manages agents, executes inference
"""

from typing import Dict, Optional
import asyncio
import time
from datetime import datetime
import sys
from pathlib import Path

from .job_queue import JobQueue
from .resource_manager import ResourceManager
from .model_cache import ModelCache
from .model_prewarmer import ModelPrewarmer
from .agent_manager import AgentManager
from .data_cabinet import DataCabinetManager
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class DIMDaemon:
    """
    DIM Daemon running on each PowerNode
    
    Responsibilities:
    - Receive jobs from orchestrator
    - Manage agent processes
    - Cache models from IPFS
    - Access data cabinets
    - Monitor resources
    """
    
    def __init__(self, config: Dict):
        """
        Initialize DIM daemon
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.node_id = config.get('daemon', {}).get('node_id', config.get('node_id', 'node-001'))
        
        # Components
        self.job_queue = JobQueue(config)
        self.resource_manager = ResourceManager(config)
        self.model_cache = ModelCache(config)
        self.model_prewarmer = ModelPrewarmer(self.model_cache, config)
        self.agent_manager = AgentManager(config)
        self.data_cabinet_manager = DataCabinetManager(config)
        
        # gRPC server (will be initialized in start())
        self.grpc_server = None
        
        # Statistics tracking
        self.stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'execution_times': []
        }
        
        # State
        self.active_jobs: Dict[str, Dict] = {}
        
        logger.info(f"DIM Daemon initialized for node {self.node_id}")
    
    async def start(self):
        """Start daemon services"""
        logger.info(f"Starting DIM Daemon on node {self.node_id}...")
        
        # Start gRPC server (Phase 2)
        from .grpc_server import DaemonGRPCServer
        self.grpc_server = DaemonGRPCServer(self, self.config)
        await self.grpc_server.start()
        
        # Start model pre-warmer (Phase 2)
        await self.model_prewarmer.start()
        
        # Start job processor
        asyncio.create_task(self.process_jobs())
        
        # Start heartbeat
        asyncio.create_task(self.heartbeat_loop())
        
        grpc_address = self.config.get('daemon', {}).get('grpc_address', 'localhost:50052')
        logger.info(f"DIM Daemon started on {grpc_address}")
    
    async def stop(self):
        """Stop daemon services"""
        logger.info(f"Stopping DIM Daemon on node {self.node_id}...")
        
        # Stop model pre-warmer
        await self.model_prewarmer.stop()
        
        # Stop gRPC server
        if self.grpc_server:
            await self.grpc_server.stop()
        
        logger.info("DIM Daemon stopped")
    
    async def submit_job(self, job_spec: Dict) -> Dict:
        """
        Submit job to daemon
        
        Called by gRPC server when orchestrator sends job
        
        Args:
            job_spec: Job specification dictionary
            
        Returns:
            Result dictionary with status
        """
        job_id = job_spec.get('job_id', f"job-{int(time.time())}")
        
        # Check resources
        if not self.resource_manager.can_accept_job(job_spec):
            raise ResourceError("Insufficient resources")
        
        # Add to queue
        await self.job_queue.enqueue(job_id, job_spec)
        
        # Track active job
        self.active_jobs[job_id] = {
            'status': 'queued',
            'job_spec': job_spec,
            'created_at': datetime.now()
        }
        
        self.stats['total_jobs'] += 1
        
        logger.info(f"Job {job_id} queued on node {self.node_id}")
        
        return {
            'job_id': job_id,
            'status': 'queued'
        }
    
    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get job status
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary or None
        """
        return self.active_jobs.get(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel job
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully
        """
        if job_id in self.active_jobs:
            # Remove from queue if queued
            await self.job_queue.remove(job_id)
            
            # Cancel agent if running
            await self.agent_manager.cancel_agent(job_id)
            
            # Update status
            self.active_jobs[job_id]['status'] = 'cancelled'
            
            logger.info(f"Job {job_id} cancelled on node {self.node_id}")
            return True
        
        return False
    
    async def get_health(self) -> Dict:
        """
        Get daemon health status
        
        Returns:
            Health status dictionary
        """
        resource_status = self.resource_manager.get_status()
        cached_models = self.model_cache.get_cached_models()
        
        # Determine overall health
        cpu_ok = resource_status.get('cpu_percent', 100) < 90
        memory_ok = resource_status.get('memory_percent', 100) < 90
        
        if cpu_ok and memory_ok:
            health_status = 'healthy'
        elif resource_status.get('cpu_percent', 100) < 95 and resource_status.get('memory_percent', 100) < 95:
            health_status = 'degraded'
        else:
            health_status = 'unhealthy'
        
        return {
            'status': health_status,
            'resources': {
                'cpu_available': resource_status.get('cpu_available', 0),
                'memory_available_gb': resource_status.get('memory_available_gb', 0),
                'gpu_available': resource_status.get('gpu_available', False),
                'cpu_percent': resource_status.get('cpu_percent', 0.0),
                'memory_percent': resource_status.get('memory_percent', 0.0)
            },
            'cached_models': cached_models,
            'active_jobs': len([j for j in self.active_jobs.values() if j['status'] == 'running']),
            'queued_jobs': self.job_queue.size()
        }
    
    async def get_stats(self) -> Dict:
        """
        Get daemon statistics
        
        Returns:
            Statistics dictionary
        """
        resource_status = self.resource_manager.get_status()
        cached_models = self.model_cache.get_cached_models()
        cache_size = self.model_cache.get_cache_size()
        
        # Calculate average execution time
        avg_execution_time = 0.0
        if self.stats['execution_times']:
            avg_execution_time = sum(self.stats['execution_times']) / len(self.stats['execution_times'])
        
        return {
            'total_jobs': self.stats['total_jobs'],
            'successful_jobs': self.stats['successful_jobs'],
            'failed_jobs': self.stats['failed_jobs'],
            'avg_execution_time': avg_execution_time,
            'cached_models_count': len(cached_models),
            'cache_size_bytes': cache_size,
            'resources': {
                'cpu_available': resource_status.get('cpu_available', 0),
                'memory_available_gb': resource_status.get('memory_available_gb', 0),
                'gpu_available': resource_status.get('gpu_available', False),
                'cpu_percent': resource_status.get('cpu_percent', 0.0),
                'memory_percent': resource_status.get('memory_percent', 0.0)
            }
        }
    
    async def process_jobs(self):
        """Process jobs from queue"""
        while True:
            try:
                # Get next job
                job_id, job_spec = await self.job_queue.dequeue()
                
                if not job_id:
                    await asyncio.sleep(1)
                    continue
                
                # Update status
                if job_id in self.active_jobs:
                    self.active_jobs[job_id]['status'] = 'running'
                    self.active_jobs[job_id]['started_at'] = datetime.now()
                
                # Execute job
                try:
                    result = await self.execute_job(job_id, job_spec)
                    
                    # Update status
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id]['status'] = 'completed'
                        self.active_jobs[job_id]['result'] = result
                        self.active_jobs[job_id]['completed_at'] = datetime.now()
                        
                        # Calculate execution time
                        started = self.active_jobs[job_id].get('started_at')
                        if started:
                            exec_time = (datetime.now() - started).total_seconds()
                            self.active_jobs[job_id]['execution_time'] = f"{exec_time:.1f}s"
                            self.stats['execution_times'].append(exec_time)
                    
                    self.stats['successful_jobs'] += 1
                    
                    # Notify orchestrator
                    await self.notify_completion(job_id, result)
                    
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}", exc_info=True)
                    
                    # Update status
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id]['status'] = 'failed'
                        self.active_jobs[job_id]['error'] = str(e)
                        self.active_jobs[job_id]['completed_at'] = datetime.now()
                    
                    self.stats['failed_jobs'] += 1
                    
                    # Notify orchestrator
                    await self.notify_failure(job_id, str(e))
                
            except Exception as e:
                logger.error(f"Error in process_jobs: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def execute_job(self, job_id: str, job_spec: Dict) -> Dict:
        """
        Execute inference job
        
        Args:
            job_id: Job identifier
            job_spec: Job specification
            
        Returns:
            Inference result
        """
        model_id = job_spec.get('model_id')
        data_source = job_spec.get('data_source')
        input_data = job_spec.get('input_data')
        timeout = job_spec.get('timeout', 120)
        
        # Record model access for pre-warming
        self.model_prewarmer.record_model_access(model_id)
        
        # Get or download model
        model_path = await self.model_cache.get_model(model_id)
        
        # Get data
        if data_source:
            data = await self.data_cabinet_manager.get_data(data_source)
        elif input_data:
            data = input_data
        else:
            raise ValueError("No data source or input data provided")
        
        # Spawn agent to run inference
        result = await self.agent_manager.run_inference(
            job_id=job_id,
            model_path=model_path,
            data=data,
            timeout=timeout
        )
        
        return result
    
    async def notify_completion(self, job_id: str, result: Dict):
        """Notify orchestrator of job completion via IPFS Pubsub"""
        try:
            # Import state manager if available
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'orchestrator' / 'src'))
            
            from orchestrator.src.ipfs.pubsub import IPFSPubsub
            
            # Get IPFS API from config
            ipfs_api = self.config.get('ipfs', {}).get('api_url', '/ip4/127.0.0.1/tcp/5001')
            if ipfs_api.startswith("/ip4/"):
                parts = ipfs_api.split("/")
                host = parts[2]
                port = parts[4]
                api_base = f"http://{host}:{port}/api/v0"
            else:
                api_base = ipfs_api if ipfs_api.endswith('/api/v0') else f"{ipfs_api}/api/v0"
            
            pubsub = IPFSPubsub(api_base)
            
            # Publish completion event
            await pubsub.publish('dim.jobs.updates', {
                'job_id': job_id,
                'event_type': 'completed',
                'node_id': self.node_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Published job completion: {job_id}")
        except Exception as e:
            logger.warning(f"Failed to publish completion via Pubsub: {e}")
    
    async def notify_failure(self, job_id: str, error: str):
        """Notify orchestrator of job failure via IPFS Pubsub"""
        try:
            # Import state manager if available
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'orchestrator' / 'src'))
            
            from orchestrator.src.ipfs.pubsub import IPFSPubsub
            
            # Get IPFS API from config
            ipfs_api = self.config.get('ipfs', {}).get('api_url', '/ip4/127.0.0.1/tcp/5001')
            if ipfs_api.startswith("/ip4/"):
                parts = ipfs_api.split("/")
                host = parts[2]
                port = parts[4]
                api_base = f"http://{host}:{port}/api/v0"
            else:
                api_base = ipfs_api if ipfs_api.endswith('/api/v0') else f"{ipfs_api}/api/v0"
            
            pubsub = IPFSPubsub(api_base)
            
            # Publish failure event
            await pubsub.publish('dim.jobs.updates', {
                'job_id': job_id,
                'event_type': 'failed',
                'node_id': self.node_id,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Published job failure: {job_id}")
        except Exception as e:
            logger.warning(f"Failed to publish failure via Pubsub: {e}")
    
    async def heartbeat_loop(self):
        """Publish heartbeat to IPFS Pubsub"""
        # Initialize pubsub if available
        pubsub = None
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'orchestrator' / 'src'))
            from orchestrator.src.ipfs.pubsub import IPFSPubsub
            
            ipfs_api = self.config.get('ipfs', {}).get('api_url', '/ip4/127.0.0.1/tcp/5001')
            if ipfs_api.startswith("/ip4/"):
                parts = ipfs_api.split("/")
                host = parts[2]
                port = parts[4]
                api_base = f"http://{host}:{port}/api/v0"
            else:
                api_base = ipfs_api if ipfs_api.endswith('/api/v0') else f"{ipfs_api}/api/v0"
            
            pubsub = IPFSPubsub(api_base)
        except Exception as e:
            logger.warning(f"Failed to initialize Pubsub for heartbeat: {e}")
        
        while True:
            try:
                # Publish status
                heartbeat_data = {
                    'node_id': self.node_id,
                    'status': 'active',
                    'active_jobs': len([j for j in self.active_jobs.values() if j['status'] == 'running']),
                    'queued_jobs': self.job_queue.size(),
                    'resources': self.resource_manager.get_status(),
                    'cached_models': self.model_cache.get_cached_models(),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Publish via IPFS Pubsub
                if pubsub:
                    await pubsub.publish('dim.nodes.heartbeat', heartbeat_data)
                else:
                    logger.debug(f"Heartbeat: {heartbeat_data}")
                
                await asyncio.sleep(30)  # Every 30 seconds
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(30)


class ResourceError(Exception):
    """Raised when insufficient resources available"""
    pass
