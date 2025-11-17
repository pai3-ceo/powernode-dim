"""
IPNS (InterPlanetary Name System) - Mutable pointers to IPFS content
"""

import json
import tempfile
import os
import requests
from typing import Dict, Optional
from datetime import datetime
import logging
import sys

# Simple logger setup (avoid circular import)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class IPNSManager:
    """Manages IPNS records for mutable state"""
    
    def __init__(self, api_base: str, key_name: Optional[str] = None):
        """
        Initialize IPNS manager
        
        Args:
            api_base: IPFS API base URL
            key_name: IPNS key name (creates new key if None)
        """
        self.api_base = api_base
        self.key_name = key_name or 'dim-state-key'
        self.key_id = None
        
        # Ensure key exists
        self._ensure_key()
        
        logger.info(f"IPNS Manager initialized with key: {self.key_name}")
    
    def _ensure_key(self):
        """Ensure IPNS key exists, create if not"""
        try:
            # List existing keys
            response = requests.post(
                f"{self.api_base}/key/list",
                timeout=5
            )
            response.raise_for_status()
            
            keys = response.json().get('Keys', [])
            
            # Check if key exists
            key_exists = any(k.get('Name') == self.key_name for k in keys)
            
            if not key_exists:
                # Create new key
                logger.info(f"Creating IPNS key: {self.key_name}")
                response = requests.post(
                    f"{self.api_base}/key/gen",
                    params={'arg': self.key_name, 'type': 'rsa', 'size': '2048'},
                    timeout=10
                )
                response.raise_for_status()
                key_info = response.json()
                self.key_id = key_info.get('Id')
                logger.info(f"Created IPNS key: {self.key_name} -> {self.key_id}")
            else:
                # Get existing key ID
                for key in keys:
                    if key.get('Name') == self.key_name:
                        self.key_id = key.get('Id')
                        logger.info(f"Using existing IPNS key: {self.key_name} -> {self.key_id}")
                        break
            
        except Exception as e:
            logger.error(f"Failed to ensure IPNS key: {e}")
            raise
    
    def publish(self, cid: str, lifetime: str = "24h") -> str:
        """
        Publish CID to IPNS
        
        Args:
            cid: IPFS CID to publish
            lifetime: How long the record is valid (e.g., "24h", "7d")
            
        Returns:
            IPNS name (key ID)
        """
        try:
            response = requests.post(
                f"{self.api_base}/name/publish",
                params={
                    'arg': cid,
                    'key': self.key_name,
                    'lifetime': lifetime
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            ipns_name = result.get('Name', self.key_id)
            
            logger.info(f"Published CID {cid} to IPNS: {ipns_name}")
            return ipns_name
            
        except Exception as e:
            logger.error(f"Failed to publish to IPNS: {e}")
            raise
    
    def resolve(self, ipns_name: Optional[str] = None) -> Optional[str]:
        """
        Resolve IPNS name to CID
        
        Args:
            ipns_name: IPNS name (uses key_name if None)
            
        Returns:
            Resolved CID or None if not found
        """
        try:
            name = ipns_name or f"/ipns/{self.key_id}"
            
            response = requests.post(
                f"{self.api_base}/name/resolve",
                params={'arg': name},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            path = result.get('Path', '')
            
            # Extract CID from path (format: /ipfs/Qm...)
            if path.startswith('/ipfs/'):
                cid = path[6:]  # Remove '/ipfs/' prefix
                logger.debug(f"Resolved IPNS {name} to CID: {cid}")
                return cid
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to resolve IPNS {ipns_name}: {e}")
            return None
    
    def update_state(self, state_data: Dict, lifetime: str = "24h") -> str:
        """
        Update mutable state via IPNS
        
        Steps:
        1. Save state data to IPFS (get CID)
        2. Publish CID to IPNS
        
        Args:
            state_data: State data dictionary
            lifetime: IPNS record lifetime
            
        Returns:
            IPNS name
        """
        # Save state to IPFS
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(state_data, f, indent=2)
            temp_path = f.name
        
        try:
            # Add to IPFS
            with open(temp_path, 'rb') as f:
                files = {'file': f}
                data = {'pin': 'true'}
                response = requests.post(
                    f"{self.api_base}/add",
                    files=files,
                    data=data,
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                cid = result['Hash']
            
            # Publish to IPNS
            ipns_name = self.publish(cid, lifetime)
            
            logger.info(f"Updated state via IPNS: {ipns_name} -> {cid}")
            return ipns_name
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def get_state(self, ipns_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get mutable state from IPNS
        
        Args:
            ipns_name: IPNS name (uses key_name if None)
            
        Returns:
            State data dictionary or None
        """
        # Resolve IPNS to CID
        cid = self.resolve(ipns_name)
        if not cid:
            return None
        
        # Get file from IPFS
        try:
            response = requests.post(
                f"{self.api_base}/get",
                params={'arg': cid},
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            # Read JSON data
            data = response.json()
            return data
            
        except Exception as e:
            logger.error(f"Failed to get state from IPNS: {e}")
            return None
    
    def get_key_id(self) -> Optional[str]:
        """Get IPNS key ID"""
        return self.key_id

