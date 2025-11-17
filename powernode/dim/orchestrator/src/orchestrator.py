"""
DIM Orchestrator - Main coordinator for job lifecycle and pattern routing
"""

from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import uuid

from .pattern_router import PatternRouter
from .node_selector import NodeSelector
from .node_registry import NodeRegistryManager
from .node_discovery import NodeDiscovery
from .orchestrator_coordinator import OrchestratorCoordinator
from .connection_pool import ConnectionPool
from .monitoring import Monitoring
from .ipfs.state_manager import IPFSStateManager
from .models.job_spec import JobSpec
from .models.job_status import JobStatus, JobState
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class DIMOrchestrator:
    """Main orchestrator for DIM inference jobs"""
    
    def __init__(self, config: Dict):
        """
        Initialize DIM orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.pattern_router = PatternRouter(config)
        self.state_manager = IPFSStateManager(config)
        
        # Node registry and discovery (Phase 2)
        self.registry_manager = NodeRegistryManager(self.state_manager, config)
        self.node_discovery = NodeDiscovery(self.registry_manager, self.state_manager, config)
        self.node_selector = NodeSelector(config)
        self.node_selector.set_state_manager(self.state_manager)
        self.node_selector.set_registry_manager(self.registry_manager)
        
        # Orchestrator coordination (Phase 2)
        orchestrator_id = config.get('orchestrator', {}).get('orchestrator_id', 'orchestrator-001')
        self.coordinator = OrchestratorCoordinator(orchestrator_id, self.state_manager, config)
        
        # Connection pool (Phase 2)
        self.connection_pool = ConnectionPool(config)
        asyncio.create_task(self.connection_pool.cleanup_idle_connections())
        
        # Monitoring (Phase 2)
        self.monitoring = Monitoring(config) if config.get('monitoring', {}).get('enabled', False) else None
        
        # Local cache for active jobs
        self.active_jobs: Dict[str, JobStatus] = {}
        
        # gRPC server (will be initialized in start())
        self.grpc_server = None
        
        logger.info("DIM Orchestrator initialized")
    
    async def start(self):
        """Start orchestrator services"""
        logger.info("Starting DIM Orchestrator...")
        
        # Start gRPC server (Phase 2)
        from .grpc_server import OrchestratorGRPCServer
        self.grpc_server = OrchestratorGRPCServer(self, self.config)
        await self.grpc_server.start()
        
        # Start node discovery (Phase 2)
        await self.node_discovery.start()
        
        # Start orchestrator coordination (Phase 2)
        await self.coordinator.start()
        
        # Subscribe to IPFS Pubsub for coordination
        await self.subscribe_to_updates()
        
        # Start heartbeat
        asyncio.create_task(self.heartbeat_loop())
        
        # Update monitoring with initial state
        if self.monitoring:
            self.monitoring.update_active_jobs(len(self.active_jobs))
            # Get node count from registry
            registry = await self.registry_manager.get_registry()
            self.monitoring.update_node_count(len(registry.nodes))
        
        logger.info("DIM Orchestrator started")
    
    async def stop(self):
        """Stop orchestrator services"""
        logger.info("Stopping DIM Orchestrator...")
        
        # Stop gRPC server
        if self.grpc_server:
            await self.grpc_server.stop()
        
        # Stop orchestrator coordination
        await self.coordinator.stop()
        
        # Stop node discovery
        await self.node_discovery.stop()
        
        # Close connection pool
        await self.connection_pool.close_all()
        
        # Stop state manager (unsubscribe from pubsub)
        await self.state_manager.stop()
        
        logger.info("DIM Orchestrator stopped")
    
    async def submit_job(self, spec: JobSpec, user_id: str) -> str:
        """
        Submit new inference job
        
        Args:
            spec: Job specification
            user_id: User submitting the job
            
        Returns:
            job_id: Unique job identifier
        """
        # Generate job ID
        job_id = self.generate_job_id()
        
        # Validate spec
        validation = self.validate_spec(spec)
        if not validation['valid']:
            raise ValueError(f"Invalid job spec: {validation['error']}")
        
        # Create job status
        status = JobStatus(
            job_id=job_id,
            pattern=spec.pattern.value,
            state=JobState.PENDING,
            user_id=user_id,
            spec=spec.dict()
        )
        
        # Save to IPFS
        spec_dict = spec.dict()
        await self.state_manager.save_job_spec(job_id, spec_dict)
        
        # Add to active jobs
        self.active_jobs[job_id] = status
        
        # Update coordinator job count
        self.coordinator.update_job_count(len(self.active_jobs))
        
        # Update monitoring
        if self.monitoring:
            self.monitoring.update_active_jobs(len(self.active_jobs))
            self.monitoring.record_job_submission(spec.pattern.value, user_id)
        
        # Check if job should be distributed to another orchestrator (Phase 2)
        selected_orchestrator = await self.coordinator.select_orchestrator_for_job(job_id, spec_dict)
        
        if selected_orchestrator:
            # Assign to another orchestrator
            await self.coordinator.assign_job_to_orchestrator(selected_orchestrator, job_id, spec_dict)
            logger.info(f"Job {job_id} assigned to orchestrator {selected_orchestrator}")
        else:
            # Execute locally
            logger.info(f"Job {job_id} submitted: pattern={spec.pattern.value}, user={user_id}")
            # Route to appropriate pattern engine (async)
            asyncio.create_task(self.execute_job(job_id, spec))
        
        return job_id
    
    async def execute_job(self, job_id: str, spec: JobSpec):
        """
        Execute job via pattern engine
        
        Args:
            job_id: Job identifier
            spec: Job specification
        """
        start_time = datetime.now()
        try:
            # Update status
            await self.update_job_state(job_id, JobState.RUNNING)
            
            # Get pattern engine
            pattern_engine = self.pattern_router.get_engine(spec.pattern.value)
            
            # Execute pattern
            result = await pattern_engine.execute(job_id, spec.dict())
            
            # Save result to IPFS
            await self.state_manager.save_job_result(job_id, result)
            
            # Update status
            await self.update_job_state(job_id, JobState.COMPLETED, result=result)
            
            # Publish completion event
            await self.state_manager.publish_job_event(job_id, 'completed', result)
            
            # Record metrics
            if self.monitoring:
                duration = (datetime.now() - start_time).total_seconds()
                self.monitoring.record_job_completion(spec.pattern.value, duration, True)
                self.monitoring.update_active_jobs(len(self.active_jobs))
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job {job_id} failed: {error_msg}")
            await self.update_job_state(job_id, JobState.FAILED, error=error_msg)
            await self.state_manager.publish_job_event(job_id, 'failed', {'error': error_msg})
            
            # Record metrics
            if self.monitoring:
                duration = (datetime.now() - start_time).total_seconds()
                self.monitoring.record_job_completion(spec.pattern.value, duration, False)
                self.monitoring.update_active_jobs(len(self.active_jobs))
    
    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get current job status
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobStatus or None if not found
        """
        # Check local cache
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Load from IPFS (Phase 2)
        status_dict = await self.state_manager.load_job_status(job_id)
        if status_dict:
            # Convert dict to JobStatus
            return JobStatus(**status_dict)
        
        return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel running job
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully
        """
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found in active jobs")
            return False
        
        # Update state
        await self.update_job_state(job_id, JobState.CANCELLED)
        
        # TODO: Notify pattern engine to cancel
        # For Phase 1, we'll just mark as cancelled
        
        logger.info(f"Job {job_id} cancelled")
        return True
    
    def generate_job_id(self) -> str:
        """
        Generate unique job ID
        
        Returns:
            Job ID string
        """
        return f"job-{uuid.uuid4().hex[:12]}"
    
    def validate_spec(self, spec: JobSpec) -> Dict[str, any]:
        """
        Validate job specification
        
        Args:
            spec: Job specification
            
        Returns:
            {'valid': bool, 'error': str}
        """
        try:
            # Basic validation (Pydantic handles most of this)
            if spec.pattern.value not in ['collaborative', 'comparative', 'chained']:
                return {'valid': False, 'error': f"Unknown pattern: {spec.pattern.value}"}
            
            # Pattern-specific validation
            if spec.pattern.value == 'collaborative':
                if len(spec.config.nodes) < 2:
                    return {'valid': False, 'error': "Collaborative requires at least 2 nodes"}
            
            elif spec.pattern.value == 'comparative':
                if len(spec.config.model_ids) < 2:
                    return {'valid': False, 'error': "Comparative requires at least 2 models"}
            
            elif spec.pattern.value == 'chained':
                if len(spec.config.pipeline) < 2:
                    return {'valid': False, 'error': "Chained requires at least 2 pipeline steps"}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    async def update_job_state(self, job_id: str, state: JobState, **kwargs):
        """
        Update job state
        
        Args:
            job_id: Job identifier
            state: New state
            **kwargs: Additional status fields
        """
        if job_id in self.active_jobs:
            self.active_jobs[job_id].state = state
            
            # Update timestamps
            if state == JobState.RUNNING and not self.active_jobs[job_id].started_at:
                self.active_jobs[job_id].started_at = datetime.now()
            elif state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
                self.active_jobs[job_id].completed_at = datetime.now()
            
            # Update additional fields
            for key, value in kwargs.items():
                setattr(self.active_jobs[job_id], key, value)
        
        # Persist to IPFS
        await self.state_manager.update_job_status(job_id, state.value, **kwargs)
    
    async def subscribe_to_updates(self):
        """Subscribe to IPFS Pubsub for coordination"""
        if not self.state_manager.pubsub:
            logger.warning("Pubsub not available, skipping subscriptions")
            return
        
        # Subscribe to job updates
        await self.state_manager.subscribe_to_job_updates(self._handle_job_update)
        
        # Subscribe to node heartbeats
        await self.state_manager.subscribe_to_node_heartbeats(self._handle_node_heartbeat)
        
        logger.info("Subscribed to IPFS Pubsub updates")
    
    async def _handle_job_update(self, message: Dict):
        """Handle job update from Pubsub"""
        try:
            job_id = message.get('job_id')
            event_type = message.get('event_type')
            data = message.get('data', {})
            
            logger.info(f"Received job update: {job_id} -> {event_type}")
            
            # Update local job status if we have it
            if job_id in self.active_jobs:
                if event_type == 'completed':
                    self.active_jobs[job_id].state = JobState.COMPLETED
                    self.active_jobs[job_id].result = data.get('result')
                elif event_type == 'failed':
                    self.active_jobs[job_id].state = JobState.FAILED
                    self.active_jobs[job_id].error = data.get('error')
            
        except Exception as e:
            logger.error(f"Error handling job update: {e}")
    
    async def _handle_node_heartbeat(self, message: Dict):
        """Handle node heartbeat from Pubsub"""
        try:
            node_id = message.get('node_id')
            # Update node registry with heartbeat info
            # This will be used by NodeSelector
            logger.debug(f"Received heartbeat from node: {node_id}")
        except Exception as e:
            logger.error(f"Error handling node heartbeat: {e}")
    
    async def heartbeat_loop(self):
        """Periodic heartbeat loop"""
        while True:
            try:
                # Update coordinator job count
                self.coordinator.update_job_count(len(self.active_jobs))
                
                # Update node registry via IPNS (if needed)
                # The coordinator handles orchestrator heartbeats via Pubsub
                
                await asyncio.sleep(30)  # Every 30 seconds
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(30)

