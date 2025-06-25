import asyncio
import websockets
import json
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ExternalWebSocketBridge:
    """Bridge to connect to external WebSocket servers and process messages with local agents"""
    
    def __init__(self, external_url: str, user_id: str = "poc-backend"):
        self.external_url = external_url
        self.user_id = user_id
        self.external_ws = None
        self.is_connected = False
        self.message_handlers = []
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def add_message_handler(self, handler: Callable):
        """Add a handler function for incoming messages"""
        self.message_handlers.append(handler)
        
    async def connect_to_external(self) -> bool:
        """Connect to the external WebSocket server"""
        try:
            # Build connection URL
            if "{user_id}" in self.external_url:
                url = self.external_url.replace("{user_id}", self.user_id)
            elif not self.external_url.endswith('/ws'):
                url = f"{self.external_url.rstrip('/')}/ws/{self.user_id}"
            else:
                url = f"{self.external_url}/{self.user_id}"
            
            logger.info(f"Connecting to external WebSocket: {url}")
            
            # Connect with timeout
            self.external_ws = await asyncio.wait_for(
                websockets.connect(url, ping_interval=30, ping_timeout=10),
                timeout=10
            )
            
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("Successfully connected to external WebSocket")
            
            # Start listening for messages from external socket
            asyncio.create_task(self._listen_to_external())
            
            # Send initial connection message
            await self.send_to_external("Hello! POC backend connected and ready.", "System")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to external WebSocket: {e}")
            self.is_connected = False
            return False
    
    async def send_to_external(self, message: str, agent_name: str = "Assistant") -> bool:
        """Send message to external WebSocket"""
        if not self.is_connected or not self.external_ws:
            logger.warning("Cannot send to external WebSocket: not connected")
            return False
        
        try:
            # Format message for external socket
            message_data = {
                "message": message,
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "from": "poc-backend",
                "type": "agent_response"
            }
            
            await self.external_ws.send(json.dumps(message_data))
            logger.info(f"Sent to external WebSocket [{agent_name}]: {message[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send to external WebSocket: {e}")
            self.is_connected = False
            await self._attempt_reconnect()
            return False
    
    async def _listen_to_external(self):
        """Listen for messages from external WebSocket and forward to handlers"""
        try:
            async for raw_message in self.external_ws:
                try:
                    await self._process_external_message(raw_message)
                except Exception as e:
                    logger.error(f"Error processing external message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("External WebSocket connection closed")
            self.is_connected = False
            await self._attempt_reconnect()
        except Exception as e:
            logger.error(f"Error in external WebSocket listener: {e}")
            self.is_connected = False
            await self._attempt_reconnect()
    
    async def _process_external_message(self, raw_message: str):
        """Process incoming message from external WebSocket"""
        try:
            # Try to parse as JSON
            try:
                data = json.loads(raw_message)
                message_content = data.get("message", data.get("content", str(data)))
                sender = data.get("sender", data.get("from", data.get("user", "External User")))
                message_type = data.get("type", "message")
            except json.JSONDecodeError:
                # Handle plain text messages
                message_content = raw_message.strip()
                sender = "External User"
                message_type = "text"
            
            # Skip empty messages
            if not message_content or message_content.strip() == "":
                return
            
            # Skip our own messages
            if sender == "poc-backend" or "poc-backend" in str(data.get("from", "")):
                return
            
            logger.info(f"Processing external message from {sender}: {message_content}")
            
            # Forward to all registered handlers
            for handler in self.message_handlers:
                try:
                    await handler(message_content, sender, message_type)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing external message: {e}")
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect to external WebSocket"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached for external WebSocket")
            return
        
        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 30)  # Exponential backoff, max 30s
        
        logger.info(f"Attempting external WebSocket reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts} in {wait_time}s")
        await asyncio.sleep(wait_time)
        
        await self.connect_to_external()
    
    async def disconnect(self):
        """Disconnect from external WebSocket"""
        if self.external_ws:
            try:
                await self.external_ws.close()
            except:
                pass
        self.is_connected = False
        logger.info("Disconnected from external WebSocket")
    
    def get_status(self) -> Dict[str, Any]:
        """Get connection status information"""
        return {
            "connected": self.is_connected,
            "url": self.external_url,
            "user_id": self.user_id,
            "reconnect_attempts": self.reconnect_attempts,
            "handlers_count": len(self.message_handlers)
        }