#!/usr/bin/env python3
"""
Load Testing Script for Multi-Agent POC Backend
Tests multiple concurrent WebSocket connections
"""

import asyncio
import websockets
import json
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any
import argparse

class LoadTestClient:
    def __init__(self, client_id: str, server_url: str):
        self.client_id = client_id
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.messages_sent = 0
        self.messages_received = 0
        self.response_times = []
        self.errors = []
        self.start_time = None
        
    async def connect(self) -> bool:
        """Connect to WebSocket server"""
        try:
            ws_url = f"{self.server_url}/ws/{self.client_id}"
            self.websocket = await asyncio.wait_for(
                websockets.connect(ws_url), 
                timeout=10
            )
            self.connected = True
            self.start_time = time.time()
            return True
        except Exception as e:
            self.errors.append(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
    
    async def send_message(self, content: str) -> float:
        """Send message and measure response time"""
        if not self.connected:
            return -1
        
        try:
            message = {
                "type": "message",
                "message": content,
                "timestamp": datetime.now().isoformat()
            }
            
            send_time = time.time()
            await self.websocket.send(json.dumps(message))
            self.messages_sent += 1
            
            # Wait for response
            response = await asyncio.wait_for(
                self.websocket.recv(), 
                timeout=30
            )
            
            receive_time = time.time()
            response_time = receive_time - send_time
            self.response_times.append(response_time)
            self.messages_received += 1
            
            return response_time
            
        except Exception as e:
            self.errors.append(f"Send error: {e}")
            return -1
    
    async def listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            while self.connected:
                message = await self.websocket.recv()
                # Just count received messages
                self.messages_received += 1
        except Exception as e:
            if self.connected:
                self.errors.append(f"Listen error: {e}")

class LoadTester:
    def __init__(self, server_url: str, num_clients: int, test_duration: int):
        self.server_url = server_url
        self.num_clients = num_clients
        self.test_duration = test_duration
        self.clients: List[LoadTestClient] = []
        self.test_messages = [
            "Hello! How are you?",
            "I want to start working out",
            "What should I eat for breakfast?",
            "Plan me a workout routine",
            "Suggest some healthy meals",
            "How often should I exercise?",
            "What are good protein sources?",
            "I need help with my fitness goals",
            "Can you create a meal plan?",
            "What exercises build muscle?"
        ]
        
    async def setup_clients(self):
        """Create and connect all test clients"""
        print(f"🔗 Connecting {self.num_clients} clients...")
        
        for i in range(self.num_clients):
            client = LoadTestClient(f"load-test-{i}", self.server_url)
            self.clients.append(client)
        
        # Connect all clients concurrently
        connection_tasks = [client.connect() for client in self.clients]
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        connected_count = sum(1 for result in results if result is True)
        print(f"✅ {connected_count}/{self.num_clients} clients connected")
        
        return connected_count
    
    async def run_load_test(self):
        """Run the main load test"""
        print(f"🚀 Starting load test for {self.test_duration} seconds...")
        
        # Start message listeners for all clients
        listen_tasks = [
            asyncio.create_task(client.listen_for_messages()) 
            for client in self.clients if client.connected
        ]
        
        # Run test for specified duration
        start_time = time.time()
        message_tasks = []
        
        while time.time() - start_time < self.test_duration:
            # Send messages from random clients
            for client in self.clients:
                if client.connected and len(message_tasks) < 50:  # Limit concurrent messages
                    message = self.test_messages[int(time.time()) % len(self.test_messages)]
                    task = asyncio.create_task(client.send_message(message))
                    message_tasks.append(task)
            
            # Clean up completed tasks
            if len(message_tasks) >= 30:
                done_tasks = [task for task in message_tasks if task.done()]
                for task in done_tasks:
                    message_tasks.remove(task)
            
            await asyncio.sleep(0.1)  # Small delay between batches
        
        # Wait for remaining message tasks
        await asyncio.gather(*message_tasks, return_exceptions=True)
        
        # Stop listeners
        for task in listen_tasks:
            task.cancel()
        
        print("⏹️ Load test completed")
    
    async def cleanup_clients(self):
        """Disconnect all clients"""
        print("🧹 Cleaning up clients...")
        
        disconnect_tasks = [client.disconnect() for client in self.clients]
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test results report"""
        total_sent = sum(client.messages_sent for client in self.clients)
        total_received = sum(client.messages_received for client in self.clients)
        total_errors = sum(len(client.errors) for client in self.clients)
        
        all_response_times = []
        for client in self.clients:
            all_response_times.extend(client.response_times)
        
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            median_response_time = statistics.median(all_response_times)
            min_response_time = min(all_response_times)
            max_response_time = max(all_response_times)
            p95_response_time = sorted(all_response_times)[int(len(all_response_times) * 0.95)]
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = p95_response_time = 0
        
        success_rate = (total_received / total_sent * 100) if total_sent > 0 else 0
        
        return {
            "test_config": {
                "num_clients": self.num_clients,
                "test_duration": self.test_duration,
                "server_url": self.server_url
            },
            "results": {
                "total_messages_sent": total_sent,
                "total_messages_received": total_received,
                "total_errors": total_errors,
                "success_rate": success_rate,
                "messages_per_second": total_sent / self.test_duration,
                "response_times": {
                    "average": avg_response_time,
                    "median": median_response_time,
                    "min": min_response_time,
                    "max": max_response_time,
                    "p95": p95_response_time
                }
            },
            "client_details": [
                {
                    "client_id": client.client_id,
                    "connected": client.connected,
                    "messages_sent": client.messages_sent,
                    "messages_received": client.messages_received,
                    "errors": len(client.errors),
                    "avg_response_time": statistics.mean(client.response_times) if client.response_times else 0
                }
                for client in self.clients
            ]
        }
    
    def print_report(self, report: Dict[str, Any]):
        """Print formatted test report"""
        print("\n" + "="*60)
        print("📊 LOAD TEST RESULTS")
        print("="*60)
        
        config = report["test_config"]
        results = report["results"]
        
        print(f"🎯 Test Configuration:")
        print(f"   Clients: {config['num_clients']}")
        print(f"   Duration: {config['test_duration']}s")
        print(f"   Server: {config['server_url']}")
        
        print(f"\n📈 Results Overview:")
        print(f"   Messages Sent: {results['total_messages_sent']}")
        print(f"   Messages Received: {results['total_messages_received']}")
        print(f"   Success Rate: {results['success_rate']:.2f}%")
        print(f"   Messages/Second: {results['messages_per_second']:.2f}")
        print(f"   Total Errors: {results['total_errors']}")
        
        print(f"\n⏱️ Response Times:")
        rt = results["response_times"]
        print(f"   Average: {rt['average']:.3f}s")
        print(f"   Median: {rt['median']:.3f}s")
        print(f"   Min: {rt['min']:.3f}s")
        print(f"   Max: {rt['max']:.3f}s")
        print(f"   95th Percentile: {rt['p95']:.3f}s")
        
        # Show client performance
        print(f"\n👥 Client Performance:")
        for client_data in report["client_details"][:5]:  # Show first 5 clients
            print(f"   {client_data['client_id']}: "
                  f"{client_data['messages_sent']} sent, "
                  f"{client_data['messages_received']} received, "
                  f"{client_data['avg_response_time']:.3f}s avg")
        
        if len(report["client_details"]) > 5:
            print(f"   ... and {len(report['client_details']) - 5} more clients")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Load test Multi-Agent POC Backend")
    parser.add_argument("--url", default="ws://localhost:8000", help="Server URL")
    parser.add_argument("--clients", type=int, default=10, help="Number of concurrent clients")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    print("🧪 Multi-Agent Backend Load Test")
    print("=" * 40)
    print(f"Server: {args.url}")
    print(f"Clients: {args.clients}")
    print(f"Duration: {args.duration}s")
    print()
    
    # Create and run load tester
    tester = LoadTester(args.url, args.clients, args.duration)
    
    try:
        # Setup
        connected_count = await tester.setup_clients()
        if connected_count == 0:
            print("❌ No clients could connect. Test aborted.")
            return
        
        # Run test
        await tester.run_load_test()
        
        # Generate and display results
        report = tester.generate_report()
        tester.print_report(report)
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Results saved to {args.output}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    finally:
        await tester.cleanup_clients()

if __name__ == "__main__":
    asyncio.run(main())