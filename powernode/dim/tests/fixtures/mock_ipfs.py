"""
Mock IPFS client for testing
"""

from typing import Dict, Optional
from unittest.mock import AsyncMock, Mock


class MockIPFSClient:
    """Mock IPFS client for testing"""
    
    def __init__(self, api_url: str = "/ip4/127.0.0.1/tcp/5001"):
        self.api_url = api_url
        self.added_files: Dict[str, bytes] = {}
        self.pinned_cids: set = set()
        self.api_base = "http://localhost:5001/api/v0"
    
    async def add_file(self, file_path: str, pin: bool = True) -> str:
        """Mock add file"""
        cid = f"QmMock{hash(file_path)}"
        if pin:
            self.pinned_cids.add(cid)
        return cid
    
    async def get_file(self, cid: str, output_path: str) -> bool:
        """Mock get file"""
        if cid in self.added_files:
            return True
        return False
    
    async def pin(self, cid: str) -> bool:
        """Mock pin"""
        self.pinned_cids.add(cid)
        return True
    
    async def unpin(self, cid: str) -> bool:
        """Mock unpin"""
        self.pinned_cids.discard(cid)
        return True
    
    async def save_job_spec(self, job_id: str, spec: Dict) -> str:
        """Mock save job spec"""
        return await self.add_file(f"job-{job_id}-spec.json")
    
    async def save_job_result(self, job_id: str, result: Dict) -> str:
        """Mock save job result"""
        return await self.add_file(f"job-{job_id}-result.json")

