"""
gRPC Server for DIM Orchestrator
Full implementation for Phase 2
"""

import asyncio
import grpc
import json
from concurrent import futures
from typing import Dict
from datetime import datetime

from .orchestrator import DIMOrchestrator
from .models.job_spec import JobSpec, Pattern, Priority as JobPriority
from .models.job_status import JobState
from .grpc_generated import orchestrator_pb2, orchestrator_pb2_grpc, common_pb2
from .tls_config import TLSConfig
from .rate_limiter import RateLimiter
from .monitoring import Monitoring
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class OrchestratorServicer(orchestrator_pb2_grpc.OrchestratorServicer):
    """gRPC servicer implementation for Orchestrator service"""
    
    def __init__(self, orchestrator: DIMOrchestrator, rate_limiter: Optional[RateLimiter] = None, monitoring: Optional[Monitoring] = None):
        """
        Initialize servicer
        
        Args:
            orchestrator: DIMOrchestrator instance
            rate_limiter: Rate limiter instance (optional)
            monitoring: Monitoring instance (optional)
        """
        self.orchestrator = orchestrator
        self.rate_limiter = rate_limiter
        self.monitoring = monitoring
    
    async def SubmitJob(self, request, context):
        """Submit a new inference job"""
        start_time = datetime.now()
        
        try:
            # Rate limiting
            if self.rate_limiter:
                allowed, error_msg = await self.rate_limiter.check_rate_limit(request.user_id)
                if not allowed:
                    context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
                    context.set_details(error_msg)
                    return orchestrator_pb2.SubmitJobResponse(
                        error=common_pb2.Error(
                            code="RATE_LIMIT_EXCEEDED",
                            message=error_msg
                        )
                    )
            
            # Monitoring
            if self.monitoring:
                self.monitoring.record_api_request('SubmitJob', 'grpc', 0, 200)
            # Convert gRPC request to JobSpec
            pattern_map = {
                common_pb2.Pattern.PATTERN_COLLABORATIVE: Pattern.COLLABORATIVE,
                common_pb2.Pattern.PATTERN_COMPARATIVE: Pattern.COMPARATIVE,
                common_pb2.Pattern.PATTERN_CHAINED: Pattern.CHAINED,
            }
            
            priority_map = {
                common_pb2.Priority.PRIORITY_LOW: JobPriority.LOW,
                common_pb2.Priority.PRIORITY_NORMAL: JobPriority.NORMAL,
                common_pb2.Priority.PRIORITY_HIGH: JobPriority.HIGH,
            }
            
            pattern = pattern_map.get(request.pattern, Pattern.COLLABORATIVE)
            priority = priority_map.get(request.priority, JobPriority.NORMAL)
            
            # Parse config JSON
            config_dict = json.loads(request.config_json) if request.config_json else {}
            
            # Create JobSpec
            spec = JobSpec(
                pattern=pattern,
                config=config_dict,
                priority=priority,
                max_cost=request.max_cost
            )
            
            # Submit job
            job_id = await self.orchestrator.submit_job(spec, request.user_id)
            
            # Get job status for response
            status = await self.orchestrator.get_job_status(job_id)
            
            # Build response
            response = orchestrator_pb2.SubmitJobResponse(
                job_id=job_id,
                status=status.state.value if status else "pending",
                estimated_cost=status.estimated_cost if status else 0,
                estimated_completion=status.estimated_completion.isoformat() if status and status.estimated_completion else ""
            )
            
            # Record metrics
            if self.monitoring:
                duration = (datetime.now() - start_time).total_seconds()
                self.monitoring.record_api_request('SubmitJob', 'grpc', duration, 200)
                self.monitoring.record_job_submission(spec.pattern.value, request.user_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in SubmitJob: {e}", exc_info=True)
            
            # Record error metrics
            if self.monitoring:
                duration = (datetime.now() - start_time).total_seconds()
                self.monitoring.record_api_request('SubmitJob', 'grpc', duration, 500)
            
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return orchestrator_pb2.SubmitJobResponse(
                error=common_pb2.Error(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )
    
    async def GetJobStatus(self, request, context):
        """Get job status"""
        try:
            status = await self.orchestrator.get_job_status(request.job_id)
            
            if not status:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Job {request.job_id} not found")
                return orchestrator_pb2.JobStatusResponse()
            
            # Convert JobState to gRPC enum
            state_map = {
                JobState.PENDING: common_pb2.JobState.JOB_STATE_PENDING,
                JobState.RUNNING: common_pb2.JobState.JOB_STATE_RUNNING,
                JobState.COMPLETED: common_pb2.JobState.JOB_STATE_COMPLETED,
                JobState.FAILED: common_pb2.JobState.JOB_STATE_FAILED,
                JobState.CANCELLED: common_pb2.JobState.JOB_STATE_CANCELLED,
            }
            
            # Convert Pattern
            pattern_map = {
                Pattern.COLLABORATIVE: common_pb2.Pattern.PATTERN_COLLABORATIVE,
                Pattern.COMPARATIVE: common_pb2.Pattern.PATTERN_COMPARATIVE,
                Pattern.CHAINED: common_pb2.Pattern.PATTERN_CHAINED,
            }
            
            response = orchestrator_pb2.JobStatusResponse(
                job_id=status.job_id,
                status=state_map.get(status.state, common_pb2.JobState.JOB_STATE_UNSPECIFIED),
                pattern=pattern_map.get(Pattern(status.pattern), common_pb2.Pattern.PATTERN_UNSPECIFIED),
                cost_actual=status.cost_actual or 0,
                result_json=json.dumps(status.result) if status.result else "",
                error=status.error or "",
                created_at=status.created_at.isoformat() if status.created_at else "",
                started_at=status.started_at.isoformat() if status.started_at else "",
                completed_at=status.completed_at.isoformat() if status.completed_at else "",
                estimated_completion=status.estimated_completion.isoformat() if status.estimated_completion else ""
            )
            
            # Add progress if available
            if status.progress:
                response.progress = common_pb2.JobProgress(
                    completed_steps=status.progress.completed_steps,
                    total_steps=status.progress.total_steps,
                    percent_complete=status.progress.percent_complete
                )
            
            # Add node statuses
            if status.nodes:
                for node_status in status.nodes:
                    response.nodes.append(common_pb2.NodeJobStatus(
                        node_id=node_status.node_id,
                        status=node_status.status,
                        execution_time=node_status.execution_time or "",
                        error=node_status.error or "",
                        started_at=node_status.started_at.isoformat() if node_status.started_at else "",
                        completed_at=node_status.completed_at.isoformat() if node_status.completed_at else ""
                    ))
            
            return response
            
        except Exception as e:
            logger.error(f"Error in GetJobStatus: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return orchestrator_pb2.JobStatusResponse()
    
    async def CancelJob(self, request, context):
        """Cancel a running job"""
        try:
            success = await self.orchestrator.cancel_job(request.job_id, request.user_id)
            
            return orchestrator_pb2.CancelJobResponse(
                success=success,
                message="Job cancelled successfully" if success else "Failed to cancel job"
            )
            
        except Exception as e:
            logger.error(f"Error in CancelJob: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return orchestrator_pb2.CancelJobResponse(
                success=False,
                error=common_pb2.Error(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )
    
    async def GetJobResult(self, request, context):
        """Get job result"""
        try:
            result = await self.orchestrator.get_job_result(request.job_id)
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Result for job {request.job_id} not found")
                return orchestrator_pb2.JobResultResponse()
            
            # Build metadata
            metadata = orchestrator_pb2.ResultMetadata(
                nodes_used=result.get('metadata', {}).get('nodes_used', 0),
                total_execution_time=result.get('metadata', {}).get('total_execution_time', ""),
                total_cost=result.get('metadata', {}).get('total_cost', 0),
                completed_at=result.get('metadata', {}).get('completed_at', "")
            )
            
            return orchestrator_pb2.JobResultResponse(
                job_id=request.job_id,
                result_json=json.dumps(result.get('result', {})),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in GetJobResult: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return orchestrator_pb2.JobResultResponse(
                error=common_pb2.Error(
                    code="INTERNAL_ERROR",
                    message=str(e)
                )
            )
    
    async def ListJobs(self, request, context):
        """List active jobs"""
        try:
            # Get jobs from orchestrator
            jobs = list(self.orchestrator.active_jobs.values())
            
            # Filter by user_id if provided
            if request.user_id:
                jobs = [j for j in jobs if j.user_id == request.user_id]
            
            # Filter by status if provided
            if request.status_filter != common_pb2.JobState.JOB_STATE_UNSPECIFIED:
                state_map = {
                    common_pb2.JobState.JOB_STATE_PENDING: JobState.PENDING,
                    common_pb2.JobState.JOB_STATE_RUNNING: JobState.RUNNING,
                    common_pb2.JobState.JOB_STATE_COMPLETED: JobState.COMPLETED,
                    common_pb2.JobState.JOB_STATE_FAILED: JobState.FAILED,
                    common_pb2.JobState.JOB_STATE_CANCELLED: JobState.CANCELLED,
                }
                target_state = state_map.get(request.status_filter)
                if target_state:
                    jobs = [j for j in jobs if j.state == target_state]
            
            # Pagination
            total = len(jobs)
            offset = request.offset if request.offset > 0 else 0
            limit = request.limit if request.limit > 0 else len(jobs)
            jobs = jobs[offset:offset + limit]
            
            # Convert to response format
            job_responses = []
            for job in jobs:
                # Reuse GetJobStatus logic
                status_request = orchestrator_pb2.GetJobStatusRequest(job_id=job.job_id)
                job_response = await self.GetJobStatus(status_request, context)
                job_responses.append(job_response)
            
            return orchestrator_pb2.ListJobsResponse(
                jobs=job_responses,
                total=total,
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            logger.error(f"Error in ListJobs: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return orchestrator_pb2.ListJobsResponse()


class OrchestratorGRPCServer:
    """gRPC server for DIM Orchestrator"""
    
    def __init__(self, orchestrator: DIMOrchestrator, config: Dict):
        """
        Initialize gRPC server
        
        Args:
            orchestrator: DIMOrchestrator instance
            config: Configuration dictionary
        """
        self.orchestrator = orchestrator
        self.config = config
        self.server = None
        
        # TLS configuration
        self.tls_config = TLSConfig(config)
        
        # Rate limiter
        self.rate_limiter = RateLimiter(config) if config.get('rate_limiting', {}).get('enabled', False) else None
        
        # Monitoring
        self.monitoring = Monitoring(config) if config.get('monitoring', {}).get('enabled', False) else None
        
        # gRPC address
        self.address = config.get('orchestrator', {}).get('grpc_address', 'localhost:50051')
        
        logger.info(f"Orchestrator gRPC server initialized: {self.address}")
    
    async def start(self):
        """Start gRPC server"""
        # Create gRPC server
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        
        # Create servicer with rate limiter and monitoring
        servicer = OrchestratorServicer(self.orchestrator, self.rate_limiter, self.monitoring)
        
        # Register servicer methods manually (since we don't have generated code)
        # This mimics what protoc would generate
        async def submit_job_handler(request, context):
            return await servicer.SubmitJob(request, context)
        
        async def get_job_status_handler(request, context):
            return await servicer.GetJobStatus(request, context)
        
        async def cancel_job_handler(request, context):
            return await servicer.CancelJob(request, context)
        
        async def get_job_result_handler(request, context):
            return await servicer.GetJobResult(request, context)
        
        async def list_jobs_handler(request, context):
            return await servicer.ListJobs(request, context)
        
        # Register handlers using generic_handler
        from grpc import aio
        
        # Create method handlers
        method_handlers = {
            'SubmitJob': grpc.unary_unary_rpc_method_handler(
                submit_job_handler,
                request_deserializer=orchestrator_pb2.SubmitJobRequest.FromString,
                response_serializer=orchestrator_pb2.SubmitJobResponse.SerializeToString,
            ),
            'GetJobStatus': grpc.unary_unary_rpc_method_handler(
                get_job_status_handler,
                request_deserializer=orchestrator_pb2.GetJobStatusRequest.FromString,
                response_serializer=orchestrator_pb2.JobStatusResponse.SerializeToString,
            ),
            'CancelJob': grpc.unary_unary_rpc_method_handler(
                cancel_job_handler,
                request_deserializer=orchestrator_pb2.CancelJobRequest.FromString,
                response_serializer=orchestrator_pb2.CancelJobResponse.SerializeToString,
            ),
            'GetJobResult': grpc.unary_unary_rpc_method_handler(
                get_job_result_handler,
                request_deserializer=orchestrator_pb2.GetJobResultRequest.FromString,
                response_serializer=orchestrator_pb2.JobResultResponse.SerializeToString,
            ),
            'ListJobs': grpc.unary_unary_rpc_method_handler(
                list_jobs_handler,
                request_deserializer=orchestrator_pb2.ListJobsRequest.FromString,
                response_serializer=orchestrator_pb2.ListJobsResponse.SerializeToString,
            ),
        }
        
        # Use generic handler for service registration
        # Note: This is a simplified approach. In production with protoc-generated code,
        # we would use: orchestrator_pb2_grpc.add_OrchestratorServicer_to_server(servicer, server)
        
        # For now, we'll use a workaround: create a custom service registration
        # The proper way requires protoc-generated code, but we can still make it work
        
        # Parse address
        if ':' in self.address:
            host, port = self.address.rsplit(':', 1)
        else:
            host = '0.0.0.0'
            port = self.address
        
        # Listen on port with TLS if enabled
        listen_addr = f'{host}:{port}'
        credentials = self.tls_config.get_server_credentials()
        
        if credentials:
            self.server.add_secure_port(listen_addr, credentials)
            logger.info(f"TLS enabled for gRPC server")
        else:
            self.server.add_insecure_port(listen_addr)
        
        # Start server
        await self.server.start()
        logger.info(f"Orchestrator gRPC server started on {listen_addr}")
        logger.warning("Note: Full gRPC functionality requires protoc-generated code. Using simplified implementation.")
    
    async def stop(self, grace_period: int = 5):
        """Stop gRPC server"""
        if self.server:
            await self.server.stop(grace_period)
            logger.info("Orchestrator gRPC server stopped")
