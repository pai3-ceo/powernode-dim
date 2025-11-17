"""
Model Pre-warmer - Pre-loads popular models for faster inference
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .model_cache import ModelCache
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class ModelPrewarmer:
    """Pre-warms models based on usage patterns"""
    
    def __init__(self, model_cache: ModelCache, config: Dict):
        """
        Initialize model pre-warmer
        
        Args:
            model_cache: Model cache instance
            config: Configuration dictionary
        """
        self.model_cache = model_cache
        self.config = config
        
        # Pre-warming configuration
        self.enabled = config.get('prewarming', {}).get('enabled', True)
        self.popular_models = config.get('prewarming', {}).get('popular_models', [])
        self.min_access_count = config.get('prewarming', {}).get('min_access_count', 5)
        self.access_window = timedelta(hours=config.get('prewarming', {}).get('access_window_hours', 24))
        
        # Model access tracking
        self.model_access_times: Dict[str, List[datetime]] = {}  # model_id -> [access_times]
        self.running = False
        
        logger.info("Model Pre-warmer initialized")
    
    async def start(self):
        """Start pre-warming service"""
        if not self.enabled:
            logger.info("Model pre-warming disabled")
            return
        
        if self.running:
            return
        
        self.running = True
        
        # Pre-warm popular models
        asyncio.create_task(self._prewarm_popular_models())
        
        # Start periodic pre-warming
        asyncio.create_task(self._periodic_prewarming())
        
        logger.info("Model Pre-warmer started")
    
    async def stop(self):
        """Stop pre-warming service"""
        self.running = False
        logger.info("Model Pre-warmer stopped")
    
    async def _prewarm_popular_models(self):
        """Pre-warm configured popular models"""
        for model_id in self.popular_models:
            try:
                logger.info(f"Pre-warming popular model: {model_id}")
                await self.model_cache.get_model(model_id)
                logger.info(f"Successfully pre-warmed model: {model_id}")
            except Exception as e:
                logger.warning(f"Failed to pre-warm model {model_id}: {e}")
    
    async def _periodic_prewarming(self):
        """Periodically pre-warm frequently accessed models"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                # Find frequently accessed models
                now = datetime.now()
                popular = []
                
                for model_id, access_times in self.model_access_times.items():
                    # Count accesses in window
                    recent_accesses = [
                        at for at in access_times
                        if now - at < self.access_window
                    ]
                    
                    if len(recent_accesses) >= self.min_access_count:
                        popular.append((model_id, len(recent_accesses)))
                
                # Sort by access count
                popular.sort(key=lambda x: x[1], reverse=True)
                
                # Pre-warm top models (limit to 5)
                for model_id, _ in popular[:5]:
                    try:
                        # Check if already cached
                        if model_id not in self.model_cache.get_cached_models():
                            logger.info(f"Pre-warming frequently accessed model: {model_id}")
                            await self.model_cache.get_model(model_id)
                    except Exception as e:
                        logger.warning(f"Failed to pre-warm model {model_id}: {e}")
                
            except Exception as e:
                logger.error(f"Error in periodic pre-warming: {e}", exc_info=True)
    
    def record_model_access(self, model_id: str):
        """Record model access for tracking"""
        if model_id not in self.model_access_times:
            self.model_access_times[model_id] = []
        
        self.model_access_times[model_id].append(datetime.now())
        
        # Clean old access times (keep only last 100)
        if len(self.model_access_times[model_id]) > 100:
            self.model_access_times[model_id] = self.model_access_times[model_id][-100:]
    
    async def prewarm_model(self, model_id: str):
        """
        Manually pre-warm a specific model
        
        Args:
            model_id: Model identifier
        """
        try:
            logger.info(f"Manually pre-warming model: {model_id}")
            await self.model_cache.get_model(model_id)
            logger.info(f"Successfully pre-warmed model: {model_id}")
        except Exception as e:
            logger.error(f"Failed to pre-warm model {model_id}: {e}")
            raise

