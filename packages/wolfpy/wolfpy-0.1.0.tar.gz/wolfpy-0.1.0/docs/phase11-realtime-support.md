# Phase 11: Real-Time Support (Async/WebSockets)

Phase 11 adds comprehensive real-time communication capabilities to WolfPy, including ASGI adapter support, WebSocket handling, and advanced real-time features like rooms, channels, and event broadcasting.

## Features

### 🚀 **ASGI Support**
- **ASGI 3.0 Compatibility**: Full ASGI application interface alongside existing WSGI support
- **HTTP/WebSocket Protocol Handling**: Support for both HTTP and WebSocket protocols
- **Async Route Handlers**: Native async/await support for route handlers
- **Seamless Integration**: Works alongside existing WSGI routes and middleware

### 🔌 **WebSocket Support**
- **Connection Management**: Full WebSocket lifecycle management
- **Message Handling**: Support for text, binary, and JSON messages
- **Connection Pooling**: Efficient connection management and cleanup
- **State Tracking**: Real-time connection state monitoring

### 🏠 **Real-Time Features**
- **Room-Based Communication**: Group users into rooms for targeted messaging
- **Channel Subscriptions**: Pub/sub pattern for event broadcasting
- **User Presence Tracking**: Track online users and their status
- **Event System**: Extensible event-driven architecture
- **Message History**: Optional message persistence and history

### ⚡ **Performance & Scalability**
- **Async/Await Throughout**: Non-blocking operations for high concurrency
- **Connection Statistics**: Real-time monitoring and analytics
- **Efficient Broadcasting**: Optimized message delivery to multiple clients
- **Memory Management**: Automatic cleanup of disconnected connections

## Quick Start

### 1. Enable Real-Time Support

```python
from wolfpy import WolfPy

# Create app with WebSocket and real-time support
app = WolfPy(
    debug=True,
    enable_websockets=True,
    enable_realtime=True
)
```

### 2. Create WebSocket Routes

```python
@app.websocket('/ws')
async def websocket_handler(websocket):
    """Handle WebSocket connections."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_json()
            
            # Echo message back
            await websocket.send_json({
                'type': 'echo',
                'data': message
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

### 3. Create Async HTTP Routes

```python
@app.async_route('/api/data')
async def get_data(request):
    """Async HTTP route handler."""
    # Simulate async operation
    await asyncio.sleep(0.1)
    
    return {
        'message': 'Data from async route',
        'timestamp': time.time()
    }
```

### 4. Run with ASGI Server

```bash
# Install uvicorn
pip install uvicorn

# Run the application
uvicorn myapp:app --host 0.0.0.0 --port 8000
```

## Real-Time Communication

### Room-Based Messaging

```python
@app.websocket('/chat')
async def chat_handler(websocket):
    await websocket.accept()
    
    # Create user
    user = User(
        id=f"user_{websocket.id}",
        name="Anonymous",
        websocket_id=websocket.id
    )
    
    # Add user to system
    await app.realtime_manager.add_user(user, websocket)
    
    try:
        while True:
            message = await websocket.receive_json()
            
            if message['type'] == 'join_room':
                room_id = message['room_id']
                
                # Create room if it doesn't exist
                room = await app.realtime_manager.get_room(room_id)
                if not room:
                    room = await app.realtime_manager.create_room(
                        room_id=room_id,
                        name=message.get('room_name', room_id)
                    )
                
                # Join room
                await app.realtime_manager.join_room(room_id, user.id)
                
            elif message['type'] == 'chat_message':
                room_id = message['room_id']
                
                # Broadcast to room
                await app.realtime_manager.broadcast_to_room(room_id, {
                    'type': 'message',
                    'user': user.name,
                    'message': message['content'],
                    'timestamp': time.time()
                })
    
    finally:
        await app.realtime_manager.remove_user(user.id)
```

### Channel Subscriptions

```python
# Create channels for different topics
await app.realtime_manager.create_channel(
    channel_id='notifications',
    name='System Notifications',
    is_persistent=True
)

await app.realtime_manager.create_channel(
    channel_id='updates',
    name='Live Updates'
)

# Subscribe users to channels
await app.realtime_manager.subscribe_to_channel('notifications', user_id)

# Broadcast to channel subscribers
await app.realtime_manager.broadcast_to_channel('notifications', {
    'type': 'notification',
    'title': 'System Update',
    'message': 'The system will be updated in 5 minutes'
})
```

### Event Handling

```python
from wolfpy.core.realtime import EventType

# Register event handlers
@app.realtime_manager.on(EventType.USER_JOINED)
async def on_user_joined(event_type, data):
    """Handle user joined event."""
    user = data['user']
    print(f"User {user['name']} joined the system")
    
    # Send welcome message
    await app.realtime_manager.send_to_user(user['id'], {
        'type': 'welcome',
        'message': f"Welcome {user['name']}!"
    })

@app.realtime_manager.on(EventType.USER_LEFT)
async def on_user_left(event_type, data):
    """Handle user left event."""
    user = data['user']
    print(f"User {user['name']} left the system")
```

## WebSocket API

### Connection Management

```python
# WebSocket properties
websocket.id              # Unique connection ID
websocket.path            # WebSocket path
websocket.client_ip       # Client IP address
websocket.state           # Connection state
websocket.headers         # Request headers

# Connection lifecycle
await websocket.accept()                    # Accept connection
await websocket.close(code=1000)           # Close connection
await websocket.ping()                     # Send ping frame
```

### Message Handling

```python
# Sending messages
await websocket.send_text("Hello, World!")
await websocket.send_bytes(b"Binary data")
await websocket.send_json({'key': 'value'})

# Receiving messages
message = await websocket.receive_message()
json_data = await websocket.receive_json()

# Message types
if message['type'] == 'text':
    text_data = message['data']
elif message['type'] == 'bytes':
    binary_data = message['data']
```

### Broadcasting

```python
# Broadcast to all connections
await app.websocket_manager.broadcast_to_all({
    'type': 'announcement',
    'message': 'Server maintenance in 10 minutes'
})

# Broadcast to specific path
await app.websocket_manager.broadcast_to_path('/chat', {
    'type': 'system',
    'message': 'New user joined the chat'
})
```

## Real-Time Models

### User Model

```python
from wolfpy.core.realtime import User

user = User(
    id='user123',
    name='John Doe',
    websocket_id='ws_abc123',
    metadata={'role': 'admin', 'avatar': 'avatar.jpg'}
)

# User methods
user.to_dict()  # Convert to dictionary
```

### Room Model

```python
from wolfpy.core.realtime import Room

room = Room(
    id='room_general',
    name='General Chat',
    description='Main chat room',
    max_users=100,
    is_private=False
)

# Room management
room.add_user(user)           # Add user to room
room.remove_user(user_id)     # Remove user from room
room.get_user_count()         # Get number of users
room.add_message(message)     # Add message to history
```

### Channel Model

```python
from wolfpy.core.realtime import Channel

channel = Channel(
    id='notifications',
    name='System Notifications',
    is_persistent=True
)

# Channel management
channel.subscribe(user_id)      # Subscribe user
channel.unsubscribe(user_id)    # Unsubscribe user
channel.add_message(message)    # Add message to history
```

## ASGI Integration

### Running with ASGI Servers

```python
# app.py
from wolfpy import WolfPy

app = WolfPy(enable_websockets=True)

@app.route('/')
def home(request):
    return "Hello from WSGI route"

@app.async_route('/async')
async def async_home(request):
    return {'message': 'Hello from async route'}

@app.websocket('/ws')
async def websocket_handler(websocket):
    await websocket.accept()
    await websocket.send_json({'message': 'Connected'})

# For ASGI
asgi_app = app.asgi

# For WSGI (still works)
wsgi_app = app
```

```bash
# Run with uvicorn (ASGI)
uvicorn app:asgi_app --host 0.0.0.0 --port 8000

# Run with gunicorn (WSGI)
gunicorn app:wsgi_app --bind 0.0.0.0:8000
```

### Deployment Options

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    command: uvicorn app:asgi_app --host 0.0.0.0 --port 8000
    environment:
      - WOLFPY_ENV=production
```

## Monitoring & Statistics

```python
# Get WebSocket statistics
ws_stats = app.websocket_manager.get_stats()
print(f"Active connections: {ws_stats['active_connections']}")

# Get real-time system statistics
rt_stats = app.realtime_manager.get_stats()
print(f"Total rooms: {rt_stats['total_rooms']}")
print(f"Total users: {rt_stats['total_users']}")

# Room and channel information
for room_id, room_info in rt_stats['rooms'].items():
    print(f"Room {room_id}: {room_info['user_count']} users")
```

## Error Handling

```python
@app.websocket('/ws')
async def websocket_handler(websocket):
    try:
        await websocket.accept()
        
        while True:
            message = await websocket.receive_json()
            # Handle message
            
    except ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")
    finally:
        # Cleanup
        await cleanup_user_data(websocket.id)
```

## Best Practices

1. **Connection Cleanup**: Always clean up resources when connections close
2. **Error Handling**: Implement proper error handling for WebSocket operations
3. **Rate Limiting**: Consider implementing rate limiting for message sending
4. **Authentication**: Implement proper authentication for WebSocket connections
5. **Monitoring**: Monitor connection counts and message rates
6. **Graceful Shutdown**: Handle server shutdown gracefully

## Example Applications

See `examples/realtime_chat.py` for a complete real-time chat application demonstrating:
- WebSocket connections
- Room-based messaging
- User presence tracking
- Real-time notifications
- Event broadcasting

This completes Phase 11 of the WolfPy framework, providing comprehensive real-time communication capabilities.
