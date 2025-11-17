"""
TLS Configuration - Manages TLS/SSL certificates for secure connections
"""

import ssl
import grpc
from typing import Optional, Dict
from pathlib import Path
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class TLSConfig:
    """Manages TLS configuration"""
    
    def __init__(self, config: Dict):
        """
        Initialize TLS configuration
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.enabled = config.get('security', {}).get('enable_tls', False)
        self.cert_file = config.get('security', {}).get('tls_cert')
        self.key_file = config.get('security', {}).get('tls_key')
        self.ca_file = config.get('security', {}).get('tls_ca')
        
        logger.info(f"TLS Config initialized (enabled: {self.enabled})")
    
    def get_server_credentials(self) -> Optional[grpc.ServerCredentials]:
        """
        Get server credentials for gRPC
        
        Returns:
            Server credentials or None if TLS disabled
        """
        if not self.enabled:
            return None
        
        if not self.cert_file or not self.key_file:
            logger.warning("TLS enabled but certificate files not configured")
            return None
        
        try:
            # Read certificate and key
            with open(self.cert_file, 'rb') as f:
                cert_chain = f.read()
            
            with open(self.key_file, 'rb') as f:
                private_key = f.read()
            
            # Create server credentials
            credentials = grpc.ssl_server_credentials(
                [(private_key, cert_chain)]
            )
            
            logger.info("TLS server credentials loaded")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to load TLS credentials: {e}", exc_info=True)
            return None
    
    def get_client_credentials(self) -> Optional[grpc.ChannelCredentials]:
        """
        Get client credentials for gRPC
        
        Returns:
            Channel credentials or None if TLS disabled
        """
        if not self.enabled:
            return None
        
        try:
            if self.ca_file:
                # Use CA file for verification
                with open(self.ca_file, 'rb') as f:
                    root_certificates = f.read()
                
                credentials = grpc.ssl_channel_credentials(root_certificates)
            else:
                # Use default system CA
                credentials = grpc.ssl_channel_credentials()
            
            logger.info("TLS client credentials loaded")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to load TLS client credentials: {e}", exc_info=True)
            return None
    
    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
        Create SSL context for HTTP connections
        
        Returns:
            SSL context or None if TLS disabled
        """
        if not self.enabled:
            return None
        
        if not self.cert_file or not self.key_file:
            return None
        
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(self.cert_file, self.key_file)
            
            if self.ca_file:
                context.load_verify_locations(self.ca_file)
            
            logger.info("SSL context created")
            return context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}", exc_info=True)
            return None

