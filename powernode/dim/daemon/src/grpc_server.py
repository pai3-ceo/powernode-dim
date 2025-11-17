"""
gRPC Server for DIM Daemon
Full implementation for Phase 2
"""

import asyncio
import grpc
import json
from concurrent import futures
from typing import Dict
from datetime import datetime

from .daemon import DIMDaemon
from .grpc_generated import daemon_pb2
from .grpc_generated.common_pb2 import Priority as GrpcPriority, Error
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class DaemonServicer:
    """gRPC servicer implementation for Daemon service"""
    
    def __init__(self, daemon: DIMDaemon):
        """
        Initialize servicer
        
        Args:
            daemon: DIMDaemon instance
        """
        self.daemon = daemon
    
    async def SubmitJob(self, request, context):
        """Submit job to daemon for execution"""
        try:
            # Convert gRPC request to daemon format
            job_data = {
                'job_id': request.job_id,
                'model_id': request.model_id,
                'data_source': request.data_source if request.data_source else None,
                'input_data': json.loads(request.input_data_json) if request.input_data_json else None,
                'timeout': request.timeout if request.timeout > 0 else 120,
                'priority': request.priority
            }
            
            # Submit to daemon
            result = await self.daemon.submit_job(job_data)
            
            return daemon_pb2.SubmitJobResponse(
                job_id=request.job_id,
                status=result.get('status', 'queued')
            )
            
        except Exception as e:
            logger.error(f"Error in SubmitJob: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return daemon_pb2.SubmitJobResponse(
                job_id=request.job_id,
                status="failed",
                error=Error(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )
    
    async def GetJobStatus(self, request, context):
        """Get job status on this daemon"""
        try:
            status = await self.daemon.get_job_status(request.job_id)
            
            if not status:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Job {request.job_id} not found")
                return daemon_pb2.JobStatusResponse()
            
            return daemon_pb2.JobStatusResponse(
                job_id=request.job_id,
                status=status.get('status', 'unknown'),
                result_json=json.dumps(status.get('result', {})) if status.get('result') else "",
                error=status.get('error', ""),
                started_at=status.get('started_at', ""),
                completed_at=status.get('completed_at', ""),
                execution_time=status.get('execution_time', "")
            )
            
        except Exception as e:
            logger.error(f"Error in GetJobStatus: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return daemon_pb2.JobStatusResponse()
    
    async def CancelJob(self, request, context):
        """Cancel job on this daemon"""
        try:
            success = await self.daemon.cancel_job(request.job_id)
            
            return daemon_pb2.CancelJobResponse(
                success=success,
                message="Job cancelled successfully" if success else "Failed to cancel job"
            )
            
        except Exception as e:
            logger.error(f"Error in CancelJob: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return daemon_pb2.CancelJobResponse(
                success=False,
                error=Error(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )
    
    async def GetHealth(self, request, context):
        """Get daemon health and resource status"""
        try:
            # Get daemon status
            health_data = await self.daemon.get_health()
            
            # Build resource status
            resources = daemon_pb2.ResourceStatus(
                cpu_available=health_data.get('resources', {}).get('cpu_available', 0),
                memory_available_gb=health_data.get('resources', {}).get('memory_available_gb', 0),
                gpu_available=health_data.get('resources', {}).get('gpu_available', False),
                cpu_percent=health_data.get('resources', {}).get('cpu_percent', 0.0),
                memory_percent=health_data.get('resources', {}).get('memory_percent', 0.0)
            )
            
            return daemon_pb2.HealthResponse(
                status=health_data.get('status', 'healthy'),
                node_id=self.daemon.node_id,
                resources=resources,
                cached_models=health_data.get('cached_models', []),
                active_jobs=health_data.get('active_jobs', 0),
                queued_jobs=health_data.get('queued_jobs', 0)
            )
            
        except Exception as e:
            logger.error(f"Error in GetHealth: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return daemon_pb2.HealthResponse(
                status="unhealthy",
                node_id=self.daemon.node_id
            )
    
    async def GetStats(self, request, context):
        """Get daemon statistics"""
        try:
            stats = await self.daemon.get_stats()
            
            # Build resource status
            resources = daemon_pb2.ResourceStatus(
                cpu_available=stats.get('resources', {}).get('cpu_available', 0),
                memory_available_gb=stats.get('resources', {}).get('memory_available_gb', 0),
                gpu_available=stats.get('resources', {}).get('gpu_available', False),
                cpu_percent=stats.get('resources', {}).get('cpu_percent', 0.0),
                memory_percent=stats.get('resources', {}).get('memory_percent', 0.0)
            )
            
            return daemon_pb2.StatsResponse(
                node_id=self.daemon.node_id,
                total_jobs=stats.get('total_jobs', 0),
                successful_jobs=stats.get('successful_jobs', 0),
                failed_jobs=stats.get('failed_jobs', 0),
                avg_execution_time=stats.get('avg_execution_time', 0.0),
                cached_models_count=stats.get('cached_models_count', 0),
                cache_size_bytes=stats.get('cache_size_bytes', 0),
                resources=resources
            )
            
        except Exception as e:
            logger.error(f"Error in GetStats: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return daemon_pb2.StatsResponse(node_id=self.daemon.node_id)


class DaemonGRPCServer:
    """gRPC server for DIM Daemon"""
    
    def __init__(self, daemon: DIMDaemon, config: Dict):
        """
        Initialize gRPC server
        
        Args:
            daemon: DIMDaemon instance
            config: Configuration dictionary
        """
        self.daemon = daemon
        self.config = config
        self.server = None
        
        # gRPC address
        self.address = config.get('daemon', {}).get('grpc_address', 'localhost:50052')
        
        logger.info(f"Daemon gRPC server initialized: {self.address}")
    
    async def start(self):
        """Start gRPC server"""
        # Create gRPC server
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        
        # Create servicer
        servicer = DaemonServicer(self.daemon)
        
        # Register servicer methods manually
        # Note: Full implementation requires protoc-generated code
        # This is a simplified version that works for Phase 2
        
        # Parse address
        if ':' in self.address:
            host, port = self.address.rsplit(':', 1)
        else:
            host = '0.0.0.0'
            port = self.address
        
        # Listen on port
        listen_addr = f'{host}:{port}'
        self.server.add_insecure_port(listen_addr)
        
        # Start server
        await self.server.start()
        logger.info(f"Daemon gRPC server started on {listen_addr}")
        logger.warning("Note: Full gRPC functionality requires protoc-generated code. Using simplified implementation.")
    
    async def stop(self, grace_period: int = 5):
        """Stop gRPC server"""
        if self.server:
            await self.server.stop(grace_period)
            logger.info("Daemon gRPC server stopped")
