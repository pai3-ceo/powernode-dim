"""
IPFS Pubsub - Real-time coordination via IPFS Pubsub
"""

import json
import asyncio
import requests
from typing import Dict, Optional, Callable, List
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


class IPFSPubsub:
    """IPFS Pubsub client for real-time coordination"""
    
    def __init__(self, api_base: str):
        """
        Initialize IPFS Pubsub client
        
        Args:
            api_base: IPFS API base URL (e.g., "http://localhost:5001/api/v0")
        """
        self.api_base = api_base
        self.subscriptions: Dict[str, asyncio.Task] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        
        logger.info(f"IPFS Pubsub initialized: {api_base}")
    
    async def publish(self, topic: str, message: Dict) -> bool:
        """
        Publish message to IPFS Pubsub topic
        
        Args:
            topic: Pubsub topic name
            message: Message dictionary (will be JSON encoded)
            
        Returns:
            True if successful
        """
        try:
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            
            response = requests.post(
                f"{self.api_base}/pubsub/pub",
                params={'arg': topic},
                data=message_bytes,
                timeout=5,
                headers={'Content-Type': 'application/octet-stream'}
            )
            response.raise_for_status()
            
            logger.debug(f"Published message to topic {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish to topic {topic}: {e}")
            return False
    
    async def subscribe(self, topic: str, handler: Callable[[Dict], None]):
        """
        Subscribe to IPFS Pubsub topic
        
        Args:
            topic: Pubsub topic name
            handler: Async function to handle incoming messages
                     Signature: async def handler(message: Dict) -> None
        """
        if topic not in self.message_handlers:
            self.message_handlers[topic] = []
        
        self.message_handlers[topic].append(handler)
        
        # Start subscription if not already running
        if topic not in self.subscriptions:
            task = asyncio.create_task(self._subscribe_loop(topic))
            self.subscriptions[topic] = task
            logger.info(f"Subscribed to topic: {topic}")
    
    async def unsubscribe(self, topic: str):
        """Unsubscribe from topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].cancel()
            del self.subscriptions[topic]
        
        if topic in self.message_handlers:
            del self.message_handlers[topic]
        
        logger.info(f"Unsubscribed from topic: {topic}")
    
    async def _subscribe_loop(self, topic: str):
        """Internal subscription loop"""
        logger.info(f"Starting subscription loop for topic: {topic}")
        
        while True:
            try:
                # Use IPFS Pubsub sub API (streaming)
                response = requests.post(
                    f"{self.api_base}/pubsub/sub",
                    params={'arg': topic},
                    stream=True,
                    timeout=None
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to subscribe to {topic}: {response.status_code}")
                    await asyncio.sleep(5)
                    continue
                
                # Stream messages
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    try:
                        # IPFS Pubsub returns messages in a specific format
                        # Format: {"from": "...", "data": "...", "seqno": "...", "topicIDs": [...]}
                        message_data = json.loads(line)
                        
                        # Decode data (base64 encoded)
                        import base64
                        data_bytes = base64.b64decode(message_data.get('data', ''))
                        message = json.loads(data_bytes.decode('utf-8'))
                        
                        # Call handlers
                        if topic in self.message_handlers:
                            for handler in self.message_handlers[topic]:
                                try:
                                    await handler(message)
                                except Exception as e:
                                    logger.error(f"Error in pubsub handler for {topic}: {e}")
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode pubsub message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing pubsub message: {e}")
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Pubsub connection error for {topic}: {e}")
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info(f"Subscription loop cancelled for {topic}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in subscription loop for {topic}: {e}")
                await asyncio.sleep(5)
    
    async def list_peers(self, topic: Optional[str] = None) -> List[str]:
        """
        List peers subscribed to topic
        
        Args:
            topic: Topic name (optional, lists all peers if None)
            
        Returns:
            List of peer IDs
        """
        try:
            params = {}
            if topic:
                params['arg'] = topic
            
            response = requests.post(
                f"{self.api_base}/pubsub/peers",
                params=params,
                timeout=5
            )
            response.raise_for_status()
            
            peers = response.json()
            return peers if isinstance(peers, list) else []
            
        except Exception as e:
            logger.error(f"Failed to list peers: {e}")
            return []
    
    async def list_topics(self) -> List[str]:
        """
        List subscribed topics
        
        Returns:
            List of topic names
        """
        try:
            response = requests.post(
                f"{self.api_base}/pubsub/ls",
                timeout=5
            )
            response.raise_for_status()
            
            topics = response.json()
            return topics if isinstance(topics, list) else []
            
        except Exception as e:
            logger.error(f"Failed to list topics: {e}")
            return []
    
    async def stop(self):
        """Stop all subscriptions"""
        logger.info("Stopping IPFS Pubsub subscriptions...")
        
        for topic in list(self.subscriptions.keys()):
            await self.unsubscribe(topic)
        
        self.running = False
        logger.info("IPFS Pubsub stopped")

