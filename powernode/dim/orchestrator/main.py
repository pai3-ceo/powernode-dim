"""
DIM Orchestrator Entry Point
"""

import asyncio
import sys
from pathlib import Path

# Add orchestrator src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.orchestrator import DIMOrchestrator
from src.utils.config import load_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    """Main entry point for DIM Orchestrator"""
    # Load configuration
    config = load_config()
    
    # Create orchestrator
    orchestrator = DIMOrchestrator(config)
    
    # Start orchestrator
    await orchestrator.start()
    
    grpc_address = config.get('orchestrator', {}).get('grpc_address', 'localhost:50051')
    logger.info(f"DIM Orchestrator started on {grpc_address}")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down DIM Orchestrator...")
        # TODO: Graceful shutdown
        sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())

