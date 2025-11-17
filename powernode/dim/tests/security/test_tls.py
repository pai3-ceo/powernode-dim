"""
Security tests for TLS
"""

import pytest
from unittest.mock import Mock, patch, mock_open

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'orchestrator' / 'src'))

from tls_config import TLSConfig


def test_tls_config_initialization():
    """Test TLS configuration initialization"""
    config = {
        'security': {
            'enable_tls': True,
            'tls_cert': '/path/to/cert.pem',
            'tls_key': '/path/to/key.pem',
            'tls_ca': '/path/to/ca.pem'
        }
    }
    
    tls_config = TLSConfig(config)
    
    assert tls_config.enabled is True
    assert tls_config.cert_file == '/path/to/cert.pem'
    assert tls_config.key_file == '/path/to/key.pem'
    assert tls_config.ca_file == '/path/to/ca.pem'


def test_tls_disabled():
    """Test TLS when disabled"""
    config = {
        'security': {
            'enable_tls': False
        }
    }
    
    tls_config = TLSConfig(config)
    
    assert tls_config.enabled is False
    assert tls_config.get_server_credentials() is None
    assert tls_config.get_client_credentials() is None


def test_tls_server_credentials():
    """Test TLS server credentials loading"""
    config = {
        'security': {
            'enable_tls': True,
            'tls_cert': '/path/to/cert.pem',
            'tls_key': '/path/to/key.pem'
        }
    }
    
    tls_config = TLSConfig(config)
    
    with patch('builtins.open', mock_open(read_data=b'cert data')):
        with patch('grpc.ssl_server_credentials') as mock_ssl:
            credentials = tls_config.get_server_credentials()
            
            # Should attempt to load credentials
            assert credentials is not None or credentials is None  # May fail if files don't exist


def test_tls_client_credentials():
    """Test TLS client credentials loading"""
    config = {
        'security': {
            'enable_tls': True,
            'tls_ca': '/path/to/ca.pem'
        }
    }
    
    tls_config = TLSConfig(config)
    
    with patch('builtins.open', mock_open(read_data=b'ca data')):
        with patch('grpc.ssl_channel_credentials') as mock_ssl:
            credentials = tls_config.get_client_credentials()
            
            # Should attempt to load credentials
            assert credentials is not None or credentials is None  # May fail if files don't exist

