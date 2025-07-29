#!/usr/bin/env python3
"""
WolfPy Real-Time Chat Application - Phase 11 Demo

This example demonstrates the real-time features of WolfPy including:
- WebSocket connections
- Real-time messaging
- Room-based chat
- User presence tracking
- Event broadcasting

To run this example:
    pip install uvicorn  # ASGI server
    python examples/realtime_chat.py

Then visit:
    http://localhost:8000 - Chat interface
    ws://localhost:8000/ws - WebSocket endpoint

Or run with uvicorn:
    uvicorn examples.realtime_chat:app --host 0.0.0.0 --port 8000
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wolfpy import WolfPy
from wolfpy.core.websocket import WebSocket
from wolfpy.core.realtime import User, Room, EventType
from wolfpy.core.response import Response


# Create WolfPy application with WebSocket and real-time support
app = WolfPy(
    debug=True,
    enable_websockets=True,
    enable_realtime=True
)

# Store connected users
connected_users = {}


@app.route('/')
def home(request):
    """Serve the chat interface."""
    return Response("""
<!DOCTYPE html>
<html>
<head>
    <title>WolfPy Real-Time Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; background: #fafafa; }
        .message { margin: 5px 0; padding: 8px; border-radius: 4px; }
        .message.user { background: #e3f2fd; text-align: right; }
        .message.other { background: #f3e5f5; }
        .message.system { background: #fff3e0; font-style: italic; text-align: center; }
        .input-container { display: flex; gap: 10px; }
        .input-container input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .input-container button { padding: 10px 20px; background: #2196f3; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .input-container button:hover { background: #1976d2; }
        .user-list { background: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .status.connected { background: #c8e6c9; color: #2e7d32; }
        .status.disconnected { background: #ffcdd2; color: #c62828; }
        .room-controls { margin: 10px 0; }
        .room-controls button { margin: 5px; padding: 8px 16px; background: #4caf50; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐺 WolfPy Real-Time Chat</h1>
        
        <div id="status" class="status disconnected">Disconnected</div>
        
        <div class="room-controls">
            <input type="text" id="usernameInput" placeholder="Enter your username" value="User" + Math.floor(Math.random() * 1000)>
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div class="room-controls">
            <input type="text" id="roomInput" placeholder="Room name" value="general">
            <button onclick="joinRoom()">Join Room</button>
            <button onclick="leaveRoom()">Leave Room</button>
        </div>
        
        <div class="user-list">
            <strong>Online Users:</strong>
            <div id="userList">None</div>
        </div>
        
        <div id="chatContainer" class="chat-container"></div>
        
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        let ws = null;
        let username = '';
        let currentRoom = '';
        let isConnected = false;

        function connect() {
            username = document.getElementById('usernameInput').value.trim();
            if (!username) {
                alert('Please enter a username');
                return;
            }

            ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.onopen = function() {
                isConnected = true;
                updateStatus('Connected', true);
                
                // Send join message
                ws.send(JSON.stringify({
                    type: 'user_join',
                    username: username
                }));
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleMessage(message);
            };
            
            ws.onclose = function() {
                isConnected = false;
                updateStatus('Disconnected', false);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateStatus('Connection Error', false);
            };
        }

        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
        }

        function joinRoom() {
            const roomName = document.getElementById('roomInput').value.trim();
            if (!roomName || !isConnected) return;
            
            ws.send(JSON.stringify({
                type: 'join_room',
                room: roomName
            }));
            currentRoom = roomName;
        }

        function leaveRoom() {
            if (!currentRoom || !isConnected) return;
            
            ws.send(JSON.stringify({
                type: 'leave_room',
                room: currentRoom
            }));
            currentRoom = '';
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !isConnected) return;
            
            ws.send(JSON.stringify({
                type: 'message',
                message: message,
                room: currentRoom
            }));
            
            input.value = '';
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function handleMessage(data) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            
            switch(data.type) {
                case 'message':
                    messageDiv.className += data.username === username ? ' user' : ' other';
                    messageDiv.innerHTML = `<strong>${data.username}:</strong> ${data.message}`;
                    break;
                    
                case 'user_joined_room':
                case 'user_left_room':
                case 'system':
                    messageDiv.className += ' system';
                    messageDiv.textContent = data.message;
                    break;
                    
                case 'user_list':
                    updateUserList(data.users);
                    return;
                    
                default:
                    messageDiv.className += ' system';
                    messageDiv.textContent = JSON.stringify(data);
            }
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function updateStatus(message, connected) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + (connected ? 'connected' : 'disconnected');
        }

        function updateUserList(users) {
            const userList = document.getElementById('userList');
            if (users && users.length > 0) {
                userList.textContent = users.join(', ');
            } else {
                userList.textContent = 'None';
            }
        }

        // Auto-connect on page load
        window.onload = function() {
            // Set random username
            document.getElementById('usernameInput').value = 'User' + Math.floor(Math.random() * 1000);
        };
    </script>
</body>
</html>
    """, headers={'Content-Type': 'text/html'})


@app.websocket('/ws')
async def websocket_handler(websocket: WebSocket):
    """Handle WebSocket connections for real-time chat."""
    await websocket.accept()
    
    user_id = None
    current_room = None
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_json()
            
            if message['type'] == 'user_join':
                # User joining the system
                username = message['username']
                user_id = f"user_{username}_{websocket.id}"
                
                # Create user and add to system
                user = User(
                    id=user_id,
                    name=username,
                    websocket_id=websocket.id
                )
                
                await app.realtime_manager.add_user(user, websocket)
                connected_users[websocket.id] = user
                
                # Send welcome message
                await websocket.send_json({
                    'type': 'system',
                    'message': f'Welcome {username}! You are now connected.'
                })
                
            elif message['type'] == 'join_room':
                # User joining a room
                if not user_id:
                    continue
                    
                room_name = message['room']
                room_id = f"room_{room_name}"
                
                # Create room if it doesn't exist
                room = await app.realtime_manager.get_room(room_id)
                if not room:
                    room = await app.realtime_manager.create_room(
                        room_id=room_id,
                        name=room_name,
                        description=f"Chat room: {room_name}"
                    )
                
                # Join the room
                success = await app.realtime_manager.join_room(room_id, user_id)
                if success:
                    current_room = room_id
                    
                    # Send room info
                    await websocket.send_json({
                        'type': 'system',
                        'message': f'Joined room: {room_name}'
                    })
                    
                    # Send user list
                    room = await app.realtime_manager.get_room(room_id)
                    user_names = [user.name for user in room.users.values()]
                    await websocket.send_json({
                        'type': 'user_list',
                        'users': user_names
                    })
                
            elif message['type'] == 'leave_room':
                # User leaving a room
                if not user_id or not current_room:
                    continue
                    
                room_name = message['room']
                room_id = f"room_{room_name}"
                
                success = await app.realtime_manager.leave_room(room_id, user_id)
                if success:
                    current_room = None
                    await websocket.send_json({
                        'type': 'system',
                        'message': f'Left room: {room_name}'
                    })
                
            elif message['type'] == 'message':
                # User sending a message
                if not user_id:
                    continue
                    
                user = await app.realtime_manager.get_user(user_id)
                if not user:
                    continue
                
                room_name = message.get('room', 'general')
                room_id = f"room_{room_name}"
                
                # Broadcast message to room
                chat_message = {
                    'type': 'message',
                    'username': user.name,
                    'message': message['message'],
                    'timestamp': datetime.now().isoformat(),
                    'room': room_name
                }
                
                await app.realtime_manager.broadcast_to_room(room_id, chat_message)
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    finally:
        # Cleanup when connection closes
        if user_id:
            await app.realtime_manager.remove_user(user_id)
        if websocket.id in connected_users:
            del connected_users[websocket.id]


@app.route('/api/stats')
def get_stats(request):
    """Get real-time system statistics."""
    if app.realtime_manager:
        stats = app.realtime_manager.get_stats()
        return Response.json(stats)
    else:
        return Response.json({'error': 'Real-time features not enabled'}, status=400)


@app.route('/api/rooms')
def get_rooms(request):
    """Get list of active rooms."""
    if app.realtime_manager:
        rooms = {
            room_id: room.to_dict() 
            for room_id, room in app.realtime_manager.rooms.items()
        }
        return Response.json({'rooms': rooms})
    else:
        return Response.json({'error': 'Real-time features not enabled'}, status=400)


# Event handlers for real-time events
if app.realtime_manager:
    @app.realtime_manager.on(EventType.USER_JOINED)
    async def on_user_joined(event_type, data):
        """Handle user joined event."""
        print(f"User joined: {data['user']['name']}")
    
    @app.realtime_manager.on(EventType.USER_LEFT)
    async def on_user_left(event_type, data):
        """Handle user left event."""
        print(f"User left: {data['user']['name']}")


if __name__ == '__main__':
    print("🐺 Starting WolfPy Real-Time Chat Demo...")
    print("=" * 50)
    print("Features demonstrated:")
    print("  ✅ WebSocket connections")
    print("  ✅ Real-time messaging")
    print("  ✅ Room-based chat")
    print("  ✅ User presence tracking")
    print("  ✅ Event broadcasting")
    print()
    print("🚀 Server starting...")
    print("   Visit: http://localhost:8000")
    print("   WebSocket: ws://localhost:8000/ws")
    print("   API Stats: http://localhost:8000/api/stats")
    print("   API Rooms: http://localhost:8000/api/rooms")
    print()
    print("💡 To run with ASGI server:")
    print("   pip install uvicorn")
    print("   uvicorn examples.realtime_chat:app --host 0.0.0.0 --port 8000")
    print("=" * 50)
    
    try:
        # Try to run with uvicorn if available
        import uvicorn
        uvicorn.run(app.asgi, host='0.0.0.0', port=8000)
    except ImportError:
        print("❌ uvicorn not found. Please install it to run ASGI server:")
        print("   pip install uvicorn")
        print("   Then run: uvicorn examples.realtime_chat:app --host 0.0.0.0 --port 8000")
