#!/usr/bin/env python3
"""
WebSocket Client Test for WolfPy Real-Time Features

This script demonstrates how to connect to a WolfPy WebSocket server
and test real-time communication features.

Requirements:
    pip install websockets

Usage:
    1. Start the realtime_chat.py server
    2. Run this client test script
"""

import asyncio
import json
import sys
import time
from typing import Optional

try:
    import websockets
except ImportError:
    print("❌ websockets library not found. Please install it:")
    print("   pip install websockets")
    sys.exit(1)


class WebSocketClient:
    """Simple WebSocket client for testing WolfPy real-time features."""
    
    def __init__(self, uri: str, username: str = "TestClient"):
        self.uri = uri
        self.username = username
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.message_count = 0
    
    async def connect(self):
        """Connect to WebSocket server."""
        try:
            print(f"🔌 Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print(f"✅ Connected as {self.username}")
            
            # Send join message
            await self.send_message({
                'type': 'user_join',
                'username': self.username
            })
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket and self.connected:
            await self.websocket.close()
            self.connected = False
            print(f"🔌 Disconnected")
    
    async def send_message(self, message: dict):
        """Send message to server."""
        if not self.connected or not self.websocket:
            print("❌ Not connected to server")
            return
        
        try:
            await self.websocket.send(json.dumps(message))
            self.message_count += 1
            print(f"📤 Sent: {message}")
        except Exception as e:
            print(f"❌ Send error: {e}")
    
    async def receive_messages(self):
        """Listen for messages from server."""
        if not self.connected or not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    print(f"📥 Received: {data}")
                    
                    # Handle different message types
                    if data.get('type') == 'system':
                        print(f"🔔 System: {data.get('message', '')}")
                    elif data.get('type') == 'message':
                        print(f"💬 {data.get('username', 'Unknown')}: {data.get('message', '')}")
                    elif data.get('type') == 'user_list':
                        users = data.get('users', [])
                        print(f"👥 Online users: {', '.join(users)}")
                    
                except json.JSONDecodeError:
                    print(f"📥 Raw message: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server")
            self.connected = False
        except Exception as e:
            print(f"❌ Receive error: {e}")
    
    async def join_room(self, room_name: str):
        """Join a chat room."""
        await self.send_message({
            'type': 'join_room',
            'room': room_name
        })
    
    async def send_chat_message(self, room_name: str, message: str):
        """Send chat message to room."""
        await self.send_message({
            'type': 'message',
            'room': room_name,
            'message': message
        })
    
    async def run_test_sequence(self):
        """Run a sequence of tests."""
        if not self.connected:
            print("❌ Not connected, cannot run tests")
            return
        
        print("\n🧪 Starting test sequence...")
        
        # Test 1: Join room
        print("\n📋 Test 1: Joining room 'test'")
        await self.join_room('test')
        await asyncio.sleep(1)
        
        # Test 2: Send messages
        print("\n📋 Test 2: Sending test messages")
        test_messages = [
            "Hello from WebSocket client!",
            "Testing real-time messaging",
            "This is message #3",
            "Final test message"
        ]
        
        for i, msg in enumerate(test_messages, 1):
            await self.send_chat_message('test', f"{msg} ({i}/4)")
            await asyncio.sleep(0.5)
        
        # Test 3: Leave room
        print("\n📋 Test 3: Leaving room")
        await self.send_message({
            'type': 'leave_room',
            'room': 'test'
        })
        await asyncio.sleep(1)
        
        print(f"\n✅ Test sequence completed! Sent {self.message_count} messages")


async def test_websocket_connection():
    """Test WebSocket connection to WolfPy server."""
    uri = "ws://localhost:8000/ws"
    username = f"TestClient_{int(time.time())}"
    
    client = WebSocketClient(uri, username)
    
    try:
        # Connect to server
        await client.connect()
        
        if not client.connected:
            print("❌ Failed to connect to server")
            print("💡 Make sure the realtime_chat.py server is running:")
            print("   python examples/realtime_chat.py")
            return False
        
        # Start receiving messages in background
        receive_task = asyncio.create_task(client.receive_messages())
        
        # Wait a moment for connection to stabilize
        await asyncio.sleep(1)
        
        # Run test sequence
        await client.run_test_sequence()
        
        # Wait for any remaining messages
        await asyncio.sleep(2)
        
        # Cancel receive task
        receive_task.cancel()
        
        # Disconnect
        await client.disconnect()
        
        print("\n🎉 WebSocket client test completed successfully!")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        await client.disconnect()
        return False
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        await client.disconnect()
        return False


async def interactive_client():
    """Interactive WebSocket client."""
    uri = "ws://localhost:8000/ws"
    username = input("Enter your username: ").strip() or f"User_{int(time.time())}"
    
    client = WebSocketClient(uri, username)
    
    try:
        await client.connect()
        
        if not client.connected:
            print("❌ Failed to connect to server")
            return
        
        # Start receiving messages
        receive_task = asyncio.create_task(client.receive_messages())
        
        print("\n💬 Interactive WebSocket Client")
        print("Commands:")
        print("  /join <room>     - Join a room")
        print("  /leave <room>    - Leave a room")
        print("  /quit            - Quit client")
        print("  <message>        - Send message to current room")
        print()
        
        current_room = None
        
        while client.connected:
            try:
                # Get user input (non-blocking)
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, f"[{current_room or 'no room'}] > "
                )
                
                if user_input.startswith('/'):
                    # Handle commands
                    parts = user_input[1:].split(' ', 1)
                    command = parts[0].lower()
                    
                    if command == 'quit':
                        break
                    elif command == 'join' and len(parts) > 1:
                        room_name = parts[1]
                        await client.join_room(room_name)
                        current_room = room_name
                    elif command == 'leave' and len(parts) > 1:
                        room_name = parts[1]
                        await client.send_message({
                            'type': 'leave_room',
                            'room': room_name
                        })
                        if current_room == room_name:
                            current_room = None
                    else:
                        print(f"❌ Unknown command: {command}")
                else:
                    # Send chat message
                    if current_room:
                        await client.send_chat_message(current_room, user_input)
                    else:
                        print("❌ Join a room first with /join <room>")
                        
            except EOFError:
                break
            except KeyboardInterrupt:
                break
        
        receive_task.cancel()
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Client error: {e}")


async def main():
    """Main function."""
    print("🐺 WolfPy WebSocket Client Test")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        await interactive_client()
    else:
        success = await test_websocket_connection()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
