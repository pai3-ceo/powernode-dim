"""
DIM Daemon Entry Point
"""

import asyncio
import sys
import os
from pathlib import Path

# Add daemon src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.daemon import DIMDaemon
from src.utils.config import load_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    """Main entry point for DIM Daemon"""
    # Load configuration
    config = load_config()
    
    # Get node ID from environment or config
    config['node_id'] = os.getenv('NODE_ID', config.get('node_id', 'node-001'))
    
    # Daemon-specific config
    daemon_config = config.get('daemon', {})
    config.update(daemon_config)
    
    # Create daemon
    daemon = DIMDaemon(config)
    
    # Start daemon
    await daemon.start()
    
    logger.info(f"DIM Daemon started for node {config['node_id']}")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down DIM Daemon...")
        # TODO: Graceful shutdown
        sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())

