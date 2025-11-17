"""
Agent Manager - Spawns and manages agent processes
"""

from multiprocessing import Process, Queue, Event
import signal
import time
import asyncio
from typing import Optional, Dict
import sys
from pathlib import Path
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class AgentManager:
    """
    Manages agent processes
    
    - Spawns separate Python processes for inference
    - Enforces 120s timeout
    - Cleans up after completion
    """
    
    def __init__(self, config: Dict):
        """
        Initialize agent manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.active_agents: Dict[str, Process] = {}
        
        # Agent script path
        agent_script = config.get('agent_script')
        if agent_script:
            self.agent_script = Path(agent_script)
        else:
            # Default to agents/run_agent.py
            self.agent_script = Path(__file__).parent.parent.parent.parent / 'agents' / 'run_agent.py'
        
        logger.info(f"Agent manager initialized: script={self.agent_script}")
    
    async def run_inference(
        self,
        job_id: str,
        model_path: str,
        data_cabinet,
        input_data: Optional[Dict],
        timeout: int = 120
    ) -> Dict:
        """
        Run inference in separate process with timeout
        
        Args:
            job_id: Unique job ID
            model_path: Path to cached model
            data_cabinet: Data cabinet instance
            input_data: Input data for inference
            timeout: Timeout in seconds (default 120)
            
        Returns:
            Inference result
        """
        # Create result queue (for IPC)
        result_queue = Queue()
        
        # Create stop event (for graceful shutdown)
        stop_event = Event()
        
        # Spawn agent process
        agent_process = Process(
            target=self._agent_worker,
            args=(
                job_id,
                model_path,
                data_cabinet,
                input_data,
                result_queue,
                stop_event
            )
        )
        
        # Start process
        agent_process.start()
        self.active_agents[job_id] = agent_process
        
        logger.info(f"Agent process started for job {job_id} (PID: {agent_process.pid})")
        
        # Wait for result with timeout
        start_time = time.time()
        result = None
        
        try:
            # Wait for result (polling with timeout)
            elapsed = 0
            while elapsed < timeout:
                if not result_queue.empty():
                    result = result_queue.get()
                    break
                
                # Check if process is still alive
                if not agent_process.is_alive():
                    # Process finished, check for result
                    if not result_queue.empty():
                        result = result_queue.get()
                    else:
                        # Process died without result
                        raise RuntimeError("Agent process terminated without result")
                    break
                
                await asyncio.sleep(0.1)  # Small delay
                elapsed = time.time() - start_time
            
            # Check if we got a result
            if result is None:
                # Timeout - kill process
                logger.warning(f"Agent timeout for job {job_id}, killing process")
                agent_process.terminate()
                agent_process.join(timeout=5)
                
                if agent_process.is_alive():
                    # Force kill
                    agent_process.kill()
                    agent_process.join(timeout=2)
                
                raise TimeoutError(f"Agent timeout after {timeout}s")
            
            # Check for errors in result
            if isinstance(result, dict) and 'error' in result:
                raise RuntimeError(result['error'])
            
            return result
        
        finally:
            # Cleanup
            if job_id in self.active_agents:
                del self.active_agents[job_id]
            
            # Ensure process is terminated
            if agent_process.is_alive():
                agent_process.terminate()
                agent_process.join(timeout=2)
    
    @staticmethod
    def _agent_worker(
        job_id: str,
        model_path: str,
        data_cabinet,
        input_data: Optional[Dict],
        result_queue: Queue,
        stop_event: Event
    ):
        """
        Worker function running in separate process
        
        This is the actual agent code
        """
        try:
            # Import here (in subprocess)
            import sys
            from pathlib import Path
            
            # Add agents src to path
            agents_src = Path(__file__).parent.parent.parent.parent / 'agents' / 'src'
            sys.path.insert(0, str(agents_src))
            
            from inference_engine import InferenceEngine
            
            # Initialize inference engine
            engine = InferenceEngine(model_path)
            
            # Load data
            if input_data:
                data = input_data
            elif data_cabinet:
                # Read from cabinet
                data = data_cabinet.read() if hasattr(data_cabinet, 'read') else {}
            else:
                data = {}
            
            # Run inference
            result = engine.infer(data)
            
            # Put result in queue
            result_queue.put(result)
            
        except Exception as e:
            # Put error in queue
            error_msg = str(e)
            result_queue.put({'error': error_msg})
            import traceback
            traceback.print_exc()

