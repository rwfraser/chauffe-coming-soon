"""
CloudManager API Client Service
Handles communication with CloudManager.py for blockchain data
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings


logger = logging.getLogger(__name__)


class CloudManagerClient:
    """Client for interacting with CloudManager.py API"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'CLOUDMANAGER_API_URL', 'http://localhost:5000')
        self.timeout = getattr(settings, 'CLOUDMANAGER_TIMEOUT', 10)
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MyChauffe-WebApp/1.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to CloudManager API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            logger.info(f"CloudManager API {method} {endpoint} - Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"CloudManager API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'API returned status {response.status_code}',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to CloudManager at {self.base_url}")
            return {
                'success': False,
                'error': 'CloudManager API unavailable - service may be down',
                'connection_error': True
            }
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to CloudManager at {self.base_url}")
            return {
                'success': False,
                'error': f'CloudManager API timeout after {self.timeout}s',
                'timeout_error': True
            }
        except Exception as e:
            logger.error(f"Unexpected error calling CloudManager API: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def get_health(self) -> Dict[str, Any]:
        """Get CloudManager health and version info"""
        return self._make_request('GET', '/api/health')
    
    def get_version(self) -> Dict[str, Any]:
        """Get CloudManager version information"""
        return self._make_request('GET', '/api/version')
    
    def list_blockchains(self) -> Dict[str, Any]:
        """Get list of all managed blockchains"""
        return self._make_request('GET', '/api/blockchains')
    
    def get_blockchain(self, blockchain_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific blockchain"""
        return self._make_request('GET', f'/api/blockchains/{blockchain_id}')
    
    def get_user_blockchains(self, user_uuid: str) -> Dict[str, Any]:
        """Get all blockchains associated with a user UUID"""
        result = self.list_blockchains()
        
        if not result.get('success'):
            return result
        
        user_blockchains = []
        blockchains = result.get('blockchains', {})
        
        for blockchain_id, metadata in blockchains.items():
            if metadata.get('user_uuid') == user_uuid:
                # Get detailed blockchain info
                blockchain_detail = self.get_blockchain(blockchain_id)
                if blockchain_detail.get('success'):
                    user_blockchains.append({
                        'blockchain_id': blockchain_id,
                        'metadata': metadata,
                        'details': blockchain_detail
                    })
        
        return {
            'success': True,
            'user_uuid': user_uuid,
            'blockchains': user_blockchains,
            'count': len(user_blockchains)
        }
    
    def get_user_blockchain_summary(self, user_uuid: str) -> Dict[str, Any]:
        """Get summarized blockchain data for a user"""
        user_blockchains_result = self.get_user_blockchains(user_uuid)
        
        if not user_blockchains_result.get('success'):
            return user_blockchains_result
        
        blockchains = user_blockchains_result.get('blockchains', [])
        
        # Calculate summary statistics
        total_blockchains = len(blockchains)
        total_blocks = 0
        total_transactions = 0
        controller_names = []
        dloid_parameters = []
        
        for blockchain in blockchains:
            metadata = blockchain.get('metadata', {})
            details = blockchain.get('details', {})
            
            # Extract chain info
            chain_info = details.get('chain_info', {})
            total_blocks += chain_info.get('length', 0)
            total_transactions += chain_info.get('pending_transactions', 0)
            
            # Extract blockchain metadata
            if metadata.get('controller_name'):
                controller_names.append({
                    'blockchain_id': blockchain['blockchain_id'],
                    'controller_name': metadata['controller_name'],
                    'controller_role': metadata.get('controller_role', 'Unknown'),
                    'created_at': metadata.get('created_at'),
                    'blockchain_name': metadata.get('name', 'Unknown')
                })
            
            # Extract DLOID info
            dloid_info = metadata.get('dloid_info', {})
            if dloid_info:
                dloid_parameters.append({
                    'blockchain_id': blockchain['blockchain_id'],
                    'dloid_hex': metadata.get('genesis_dloid', ''),
                    'dloid_params': metadata.get('dloid_params', ''),
                    'dloid_info': dloid_info,
                    'created_at': metadata.get('created_at')
                })
        
        return {
            'success': True,
            'user_uuid': user_uuid,
            'summary': {
                'total_blockchains': total_blockchains,
                'total_blocks': total_blocks,
                'total_transactions': total_transactions,
                'controller_names': controller_names,
                'dloid_parameters': dloid_parameters
            },
            'blockchains': blockchains  # Full data for detailed view
        }
    
    def create_blockchain(self, user_uuid: str, first_name: str, last_name: str, 
                         existing_licenses: int = 0, dloid_params: Dict = None, 
                         name: str = None, difficulty: int = 4, 
                         controller_role: str = 'manager') -> Dict[str, Any]:
        """Create a new blockchain for a user"""
        
        payload = {
            'user_uuid': user_uuid,
            'first_name': first_name,
            'last_name': last_name,
            'existing_licenses': existing_licenses,
            'controller_role': controller_role,
            'difficulty': difficulty
        }
        
        if name:
            payload['name'] = name
            
        if dloid_params:
            payload['dloid_params'] = dloid_params
        
        return self._make_request('POST', '/api/blockchains', json=payload)


# Global client instance
_cloudmanager_client = None

def get_cloudmanager_client() -> CloudManagerClient:
    """Get global CloudManager client instance"""
    global _cloudmanager_client
    if _cloudmanager_client is None:
        _cloudmanager_client = CloudManagerClient()
    return _cloudmanager_client