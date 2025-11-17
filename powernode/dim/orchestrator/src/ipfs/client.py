"""
IPFS Client wrapper for DIM Orchestrator
Extends base IPFS client with DIM-specific operations
"""

import json
from typing import Optional, Dict, Any
from powernode.ipfs.ipfs_client import IPFSClient


class DIMIPFSClient(IPFSClient):
    """IPFS client with DIM-specific operations"""
    
    def __init__(self, ipfs_api_url: str = "/ip4/127.0.0.1/tcp/5001"):
        """Initialize DIM IPFS client"""
        super().__init__(ipfs_api_url)
        self.base_path = "/pai3/dim"
    
    async def save_job_spec(self, job_id: str, spec: Dict[str, Any]) -> str:
        """
        Save job specification to IPFS
        
        Args:
            job_id: Job identifier
            spec: Job specification dictionary
            
        Returns:
            IPFS CID of saved spec
        """
        import tempfile
        import os
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec, f, indent=2)
            temp_path = f.name
        
        try:
            # Add to IPFS
            cid = self.add_file(temp_path, pin=True)
            
            # Store in IPFS filesystem at standard path
            ipfs_path = f"{self.base_path}/jobs/{job_id}/spec.json"
            # Note: IPFS HTTP API doesn't directly support files.write
            # We'll use the CID directly for retrieval
            
            return cid
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    async def load_job_spec(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Load job specification from IPFS
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job specification dictionary or None if not found
        """
        import tempfile
        import os
        
        # Try to get from IPFS filesystem path
        # For now, we'll need to track CIDs separately
        # This is a simplified version - in production, use IPNS or a registry
        return None
    
    async def save_job_result(self, job_id: str, result: Dict[str, Any]) -> str:
        """
        Save job result to IPFS
        
        Args:
            job_id: Job identifier
            result: Result dictionary
            
        Returns:
            IPFS CID of saved result
        """
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(result, f, indent=2)
            temp_path = f.name
        
        try:
            cid = self.add_file(temp_path, pin=True)
            return cid
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    async def save_node_result(self, job_id: str, node_id: str, result: Dict[str, Any]) -> str:
        """
        Save node-specific result to IPFS
        
        Args:
            job_id: Job identifier
            node_id: Node identifier
            result: Result dictionary
            
        Returns:
            IPFS CID of saved result
        """
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(result, f, indent=2)
            temp_path = f.name
        
        try:
            cid = self.add_file(temp_path, pin=True)
            return cid
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

