"""
Data Cabinet Manager - Abstracts data access (local and IPFS cabinets)
"""

from typing import Optional, Dict
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class DataCabinetManager:
    """
    Manages data cabinet access
    
    Supports:
    - Local cabinets (disk)
    - IPFS cabinets (remote)
    """
    
    def __init__(self, config: Dict):
        """
        Initialize data cabinet manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.cabinet_manager = None  # Will be initialized if powernode.cabinet available
        
        # Try to import cabinet manager
        try:
            from powernode.cabinet.cabinet_manager import CabinetManager
            # Initialize if needed
            # self.cabinet_manager = CabinetManager(...)
        except ImportError:
            logger.warning("powernode.cabinet not available, using mock cabinet manager")
        
        logger.info("Data cabinet manager initialized")
    
    async def get_cabinet(self, cabinet_id: Optional[str]):
        """
        Get cabinet instance
        
        Args:
            cabinet_id: Cabinet identifier (optional)
            
        Returns:
            Cabinet instance or None
        """
        if not cabinet_id:
            return None
        
        # For Phase 1, return mock cabinet
        # In Phase 2, use actual CabinetManager
        return MockCabinet(cabinet_id)


class MockCabinet:
    """Mock cabinet for Phase 1"""
    
    def __init__(self, cabinet_id: str):
        self.cabinet_id = cabinet_id
    
    def read(self) -> Dict:
        """Read data from cabinet"""
        return {'cabinet_id': self.cabinet_id, 'data': 'mock_data'}

