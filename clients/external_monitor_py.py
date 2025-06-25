#!/usr/bin/env python3
"""
External WebSocket Monitor Client
Monitors external WebSocket connections and logs interactions
"""

import asyncio
import websockets
import json
import sys
import os
from datetime import datetime
from typing import Optional

class ExternalMonitor:
    def __init__(self, url: str, user_id: str = "monitor-client"):
        self.url = url
        self.user_id = user_id
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.message_count = 0
        self.start_time = None
        
    async def connect_and_monitor(self):
        """Connect to external WebSocket and start monitoring"""
        try:
            # Build connection URL
            if "{user_id}" in self.url:
                connect_url = self.url.replace("{user_id}", self.user_id)
            elif not self.url.endswith('/ws'):
                connect_url = f"{self.url.rstrip('/')}/ws/{self.user_id}"
            else:
                connect_url = f"{self.url}/{self.user_id}"
            
            print(f"🔗 Connecting to: {connect_url}")
            
            # Connect with timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(connect_url, ping_interval=30),
                timeout=10
            )
            
            self.is_connected = True
            self.start_time = datetime.now()
            print(f"✅ Connected successfully at {self.start_time.strftime('%H:%M:%S')}")
            
            # Send initial message
            await self.send_message("Hello! Monitor client connected and ready to observe interactions.")
            
            # Start monitoring
            await self.monitor_messages()
            
        except asyncio.TimeoutError:
            print("❌ Connection timeout")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    async def send_message(self, content: str, message_type: str = "message"):
        """Send message to external WebSocket"""
        if not self.is_connected or not self.websocket:
            return False
        
        try:
            message_data = {
                "type": message_type,
                "message": content,
                "from": "monitor-client",
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(message_data))
            print(f"📤 Sent: {content}")
            return True
            
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    async def monitor_messages(self):
        """Monitor incoming messages"""
        print("\n📡 Starting message monitoring...")
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            async for raw_message in self.websocket:
                try:
                    await self.process_message(raw_message)
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n🔴 Connection closed by server")
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
        finally:
            self.is_connected = False
            if self.websocket:
                await self.websocket.close()
    
    async def process_message(self, raw_message: str):
        """Process and display incoming message"""
        self.message_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            # Try to parse as JSON
            data = json.loads(raw_message)
            
            message_type = data.get("type", "unknown")
            sender = data.get("agent", data.get("sender", data.get("from", "Unknown")))
            content = data.get("message", data.get("content", str(data)))
            
            # Format output based on message type
            if message_type == "message" or message_type == "agent_response":
                print(f"📨 [{timestamp}] {sender}: {content}")
                
                # Detect if this looks like an agent response
                if any(emoji in sender for emoji in ["💪", "🥗", "🤖"]):
                    print(f"   🤖 Agent detected: {sender}")
                    
            elif message_type == "system":
                print(f"🔧 [{timestamp}] System: {content}")
                
            elif message_type == "typing":
                print(f"✏️  [{timestamp}] {sender} is typing...")
                
            else:
                print(f"📋 [{timestamp}] {message_type}: {content}")
            
            # Log to file
            log_entry = {
                "timestamp": timestamp,
                "type": message_type,
                "sender": sender,
                "content": content,
                "message_count": self.message_count
            }
            
            await self.log_to_file(log_entry)
            
        except json.JSONDecodeError:
            # Handle plain text messages
            print(f"📄 [{timestamp}] Plain text: {raw_message}")
    
    async def log_to_file(self, log_entry: dict):
        """Log message to file"""
        try:
            log_filename = f"monitor_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            with open(log_filename, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            print(f"⚠️  Logging error: {e}")
    
    def print_stats(self):
        """Print connection statistics"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            print(f"\n📊 Statistics:")
            print(f"   Connected for: {duration}")
            print(f"   Messages received: {self.message_count}")
            print(f"   Average rate: {self.message_count / duration.total_seconds():.2f} msg/sec")

async def interactive_session(monitor: ExternalMonitor):
    """Run interactive session with the monitor"""
    print("\n🎮 Interactive mode started")
    print("Commands:")
    print("  /stats - Show statistics")
    print("  /ping - Send ping")
    print("  /test - Send test message")
    print("  /quit - Disconnect and exit")
    print("  Or type any message to send\n")
    
    while monitor.is_connected:
        try:
            # Get user input with timeout
            user_input = await asyncio.wait_for(
                asyncio.to_thread(input, "💬 Command: "),
                timeout=1.0
            )
            
            if user_input.strip():
                await handle_command(monitor, user_input.strip())
                
        except asyncio.TimeoutError:
            # Continue monitoring
            await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Exiting interactive mode")
            break
        except EOFError:
            break

async def handle_command(monitor: ExternalMonitor, command: str):
    """Handle user commands"""
    if command.startswith("/"):
        cmd = command[1:].lower()
        
        if cmd == "stats":
            monitor.print_stats()
        elif cmd == "ping":
            await monitor.send_message("ping", "ping")
        elif cmd == "test":
            await monitor.send_message("This is a test message from monitor client")
        elif cmd == "quit":
            print("👋 Disconnecting...")
            monitor.is_connected = False
        else:
            print(f"❓ Unknown command: {cmd}")
    else:
        # Send regular message
        await monitor.send_message(command)

async def main():
    """Main function"""
    print("🔍 External WebSocket Monitor")
    print("=" * 40)
    
    # Get configuration
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = os.getenv("EXTERNAL_WS_URL", "wss://example.onrender.com/ws")
    
    if len(sys.argv) > 2:
        user_id = sys.argv[2]
    else:
        user_id = os.getenv("EXTERNAL_WS_USER_ID", "monitor-client")
    
    print(f"📍 Target URL: {url}")
    print(f"👤 User ID: {user_id}")
    print()
    
    # Create and run monitor
    monitor = ExternalMonitor(url, user_id)
    
    # Run monitoring and interactive session concurrently
    try:
        monitoring_task = asyncio.create_task(monitor.connect_and_monitor())
        
        # Wait a bit for connection
        await asyncio.sleep(2)
        
        if monitor.is_connected:
            interactive_task = asyncio.create_task(interactive_session(monitor))
            await asyncio.gather(monitoring_task, interactive_task, return_exceptions=True)
        else:
            await monitoring_task
            
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")
    finally:
        monitor.print_stats()

if __name__ == "__main__":
    asyncio.run(main())