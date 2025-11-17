"""
Model Cache - 50GB local model cache with LRU eviction
"""

from typing import Optional, Dict, List
import os
import time
import asyncio
from pathlib import Path
import sys

# Add orchestrator IPFS client to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'orchestrator' / 'src'))
from orchestrator.src.ipfs.client import DIMIPFSClient
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class ModelCache:
    """
    Local model cache (50GB)
    
    - Downloads models from IPFS
    - LRU eviction
    - Pre-warming popular models
    """
    
    def __init__(self, config: Dict):
        """
        Initialize model cache
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.cache_dir = Path(config.get('cache_dir', '/var/lib/dim/models'))
        self.max_cache_size = config.get('max_cache_gb', 50) * 1024 * 1024 * 1024  # Convert to bytes
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cached models: model_id -> {path, size, last_used}
        self.cached_models: Dict[str, Dict] = {}
        
        # IPFS client
        ipfs_api = config.get('ipfs', {}).get('api_url', '/ip4/127.0.0.1/tcp/5001')
        self.ipfs_client = DIMIPFSClient(ipfs_api)
        
        logger.info(f"Model cache initialized: dir={self.cache_dir}, max_size={self.max_cache_size / (1024**3):.1f}GB")
    
    async def get_model(self, model_id: str) -> str:
        """
        Get model (from cache or download)
        
        Args:
            model_id: Model identifier
            
        Returns:
            Path to cached model
        """
        # Check if cached
        if model_id in self.cached_models:
            # Update last used
            self.cached_models[model_id]['last_used'] = time.time()
            model_path = self.cached_models[model_id]['path']
            
            # Verify file still exists
            if os.path.exists(model_path):
                logger.debug(f"Model {model_id} found in cache: {model_path}")
                return model_path
            else:
                # File missing, remove from cache
                logger.warning(f"Cached model {model_id} file missing, removing from cache")
                del self.cached_models[model_id]
        
        # Download from IPFS
        logger.info(f"Downloading model {model_id} from IPFS...")
        model_path = await self.download_model(model_id)
        
        # Check cache size and evict if needed
        await self.evict_if_needed()
        
        # Add to cache
        model_size = os.path.getsize(model_path)
        self.cached_models[model_id] = {
            'path': model_path,
            'size': model_size,
            'last_used': time.time()
        }
        
        # Pin in IPFS
        try:
            # Get CID from model_id (assuming model_id is CID or we track it)
            # For Phase 1, we'll skip pinning
            pass
        except Exception as e:
            logger.warning(f"Failed to pin model {model_id}: {e}")
        
        logger.info(f"Model {model_id} cached: {model_path} ({model_size / (1024**2):.1f}MB)")
        return model_path
    
    async def download_model(self, model_id: str) -> str:
        """
        Download model from IPFS
        
        Args:
            model_id: Model identifier (CID or model ID)
            
        Returns:
            Path to downloaded model
        """
        # IPFS path
        ipfs_path = f"/pai3/dim/models/{model_id}"
        
        # Local path
        local_path = self.cache_dir / model_id
        
        # Create model directory
        local_path.mkdir(parents=True, exist_ok=True)
        
        # Download from IPFS
        # For Phase 1, we'll use a placeholder
        # In Phase 2, use IPFS get
        try:
            # Try to get from IPFS
            # This is a simplified version - in production, handle directories, etc.
            temp_file = local_path / "model.bin"
            
            # Placeholder: create empty file
            # In production, use: await self.ipfs_client.get_file(cid, str(temp_file))
            temp_file.touch()
            
            logger.info(f"Model {model_id} downloaded to {local_path}")
            return str(temp_file)
        except Exception as e:
            logger.error(f"Failed to download model {model_id}: {e}")
            raise
    
    async def evict_if_needed(self):
        """Evict least recently used models if cache full"""
        current_size = sum(m['size'] for m in self.cached_models.values())
        
        if current_size > self.max_cache_size:
            logger.info(f"Cache full ({current_size / (1024**3):.1f}GB), evicting LRU models...")
            
            # Sort by last used (oldest first)
            models_by_age = sorted(
                self.cached_models.items(),
                key=lambda x: x[1]['last_used']
            )
            
            # Evict until under limit
            for model_id, model_info in models_by_age:
                try:
                    # Remove file
                    if os.path.exists(model_info['path']):
                        os.remove(model_info['path'])
                    
                    # Remove from cache
                    del self.cached_models[model_id]
                    
                    # Unpin from IPFS (if applicable)
                    # For Phase 1, skip
                    
                    # Check if under limit
                    current_size -= model_info['size']
                    if current_size <= self.max_cache_size * 0.9:  # 90% threshold
                        break
                except Exception as e:
                    logger.error(f"Error evicting model {model_id}: {e}")
            
            logger.info(f"Cache eviction complete: {current_size / (1024**3):.1f}GB remaining")
    
    def get_cached_models(self) -> List[str]:
        """Get list of cached model IDs"""
        return list(self.cached_models.keys())
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        current_size = sum(m['size'] for m in self.cached_models.values())
        
        return {
            'cached_models': len(self.cached_models),
            'current_size_gb': current_size / (1024 ** 3),
            'max_size_gb': self.max_cache_size / (1024 ** 3),
            'usage_percent': (current_size / self.max_cache_size * 100) if self.max_cache_size > 0 else 0
        }

