"""
Tests for WolfPy Real-Time Support - Phase 11

This test suite covers the WebSocket and real-time communication features:
- ASGI application functionality
- WebSocket connection management
- Real-time messaging and broadcasting
- Room and channel management
- Event system
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wolfpy import WolfPy
from wolfpy.core.asgi import ASGIApplication, ASGIRequest, ASGIResponse
from wolfpy.core.websocket import WebSocket, WebSocketManager, WebSocketState, WebSocketMessage
from wolfpy.core.realtime import RealtimeManager, User, Room, Channel, EventType


class TestASGIApplication:
    """Test ASGI application functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.app = WolfPy(enable_websockets=True, enable_realtime=True)
        self.asgi_app = self.app.asgi_app
    
    @pytest.mark.asyncio
    async def test_asgi_http_request(self):
        """Test ASGI HTTP request handling."""
        # Mock ASGI scope for HTTP request
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'query_string': b'',
            'headers': []
        }
        
        # Mock receive and send
        receive = AsyncMock()
        receive.return_value = {'type': 'http.request', 'body': b'', 'more_body': False}
        
        send = AsyncMock()
        
        # Add async route
        @self.asgi_app.async_route('/test')
        async def test_handler(request):
            return {'message': 'Hello from async route'}
        
        # Call ASGI app
        await self.asgi_app(scope, receive, send)
        
        # Verify response was sent
        assert send.call_count >= 2  # start + body
        
        # Check response start
        start_call = send.call_args_list[0][0][0]
        assert start_call['type'] == 'http.response.start'
        assert start_call['status'] == 200
    
    @pytest.mark.asyncio
    async def test_asgi_websocket_connection(self):
        """Test ASGI WebSocket connection handling."""
        # Mock ASGI scope for WebSocket
        scope = {
            'type': 'websocket',
            'path': '/ws',
            'query_string': b'',
            'headers': []
        }
        
        # Mock receive and send
        receive = AsyncMock()
        send = AsyncMock()
        
        # Add WebSocket route
        @self.asgi_app.websocket('/ws')
        async def ws_handler(websocket):
            await websocket.accept()
            await websocket.send_json({'message': 'Connected'})
        
        # Call ASGI app
        await self.asgi_app(scope, receive, send)
        
        # Verify WebSocket accept was called
        accept_call = send.call_args_list[0][0][0]
        assert accept_call['type'] == 'websocket.accept'


class TestWebSocket:
    """Test WebSocket functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.scope = {
            'type': 'websocket',
            'path': '/ws',
            'query_string': b'test=1',
            'headers': [[b'host', b'localhost']],
            'client': ['127.0.0.1', 12345]
        }
        self.receive = AsyncMock()
        self.send = AsyncMock()
        self.websocket = WebSocket(self.scope, self.receive, self.send)
    
    def test_websocket_properties(self):
        """Test WebSocket properties."""
        assert self.websocket.path == '/ws'
        assert self.websocket.query_string == 'test=1'
        assert self.websocket.client_ip == '127.0.0.1'
        assert self.websocket.client_port == 12345
        assert self.websocket.state == WebSocketState.CONNECTING
        assert 'host' in self.websocket.headers
    
    @pytest.mark.asyncio
    async def test_websocket_accept(self):
        """Test WebSocket connection acceptance."""
        await self.websocket.accept()
        
        # Verify accept message was sent
        self.send.assert_called_once_with({'type': 'websocket.accept'})
        assert self.websocket.state == WebSocketState.CONNECTED
    
    @pytest.mark.asyncio
    async def test_websocket_send_text(self):
        """Test sending text messages."""
        self.websocket.state = WebSocketState.CONNECTED
        
        await self.websocket.send_text("Hello, World!")
        
        self.send.assert_called_once_with({
            'type': 'websocket.send',
            'text': "Hello, World!"
        })
    
    @pytest.mark.asyncio
    async def test_websocket_send_json(self):
        """Test sending JSON messages."""
        self.websocket.state = WebSocketState.CONNECTED
        
        data = {'message': 'Hello', 'timestamp': 123456}
        await self.websocket.send_json(data)
        
        expected_call = {
            'type': 'websocket.send',
            'text': json.dumps(data, default=str)
        }
        self.send.assert_called_once_with(expected_call)
    
    @pytest.mark.asyncio
    async def test_websocket_receive_message(self):
        """Test receiving messages."""
        self.receive.return_value = {
            'type': 'websocket.receive',
            'text': 'Hello from client'
        }
        
        message = await self.websocket.receive_message()
        
        assert message['type'] == 'text'
        assert message['data'] == 'Hello from client'
    
    @pytest.mark.asyncio
    async def test_websocket_close(self):
        """Test WebSocket connection closing."""
        self.websocket.state = WebSocketState.CONNECTED
        
        await self.websocket.close(code=1000, reason="Normal closure")
        
        self.send.assert_called_once_with({
            'type': 'websocket.close',
            'code': 1000,
            'reason': "Normal closure"
        })
        assert self.websocket.state == WebSocketState.DISCONNECTED


class TestWebSocketManager:
    """Test WebSocket manager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.manager = WebSocketManager()
        
        # Create mock WebSockets
        self.ws1 = MagicMock()
        self.ws1.id = 'ws1'
        self.ws1.path = '/chat'
        self.ws1.state = WebSocketState.CONNECTED
        
        self.ws2 = MagicMock()
        self.ws2.id = 'ws2'
        self.ws2.path = '/chat'
        self.ws2.state = WebSocketState.CONNECTED
    
    @pytest.mark.asyncio
    async def test_add_connection(self):
        """Test adding WebSocket connections."""
        await self.manager.add_connection(self.ws1)
        
        assert self.ws1.id in self.manager.connections
        assert self.ws1.id in self.manager.connections_by_path['/chat']
        assert self.manager.connection_stats['active_connections'] == 1
    
    @pytest.mark.asyncio
    async def test_remove_connection(self):
        """Test removing WebSocket connections."""
        await self.manager.add_connection(self.ws1)
        await self.manager.remove_connection(self.ws1)
        
        assert self.ws1.id not in self.manager.connections
        assert self.manager.connection_stats['active_connections'] == 0
    
    @pytest.mark.asyncio
    async def test_get_connections_by_path(self):
        """Test getting connections by path."""
        await self.manager.add_connection(self.ws1)
        await self.manager.add_connection(self.ws2)
        
        connections = await self.manager.get_connections_by_path('/chat')
        assert len(connections) == 2
        assert self.ws1 in connections
        assert self.ws2 in connections
    
    @pytest.mark.asyncio
    async def test_broadcast_to_all(self):
        """Test broadcasting to all connections."""
        # Mock send methods
        self.ws1.send_json = AsyncMock()
        self.ws2.send_json = AsyncMock()
        
        await self.manager.add_connection(self.ws1)
        await self.manager.add_connection(self.ws2)
        
        message = {'type': 'broadcast', 'data': 'Hello everyone'}
        await self.manager.broadcast_to_all(message)
        
        self.ws1.send_json.assert_called_once_with(message)
        self.ws2.send_json.assert_called_once_with(message)


class TestRealtimeManager:
    """Test real-time manager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.websocket_manager = WebSocketManager()
        self.realtime_manager = RealtimeManager(self.websocket_manager)
        
        # Create mock user and WebSocket
        self.user = User(
            id='user1',
            name='TestUser',
            websocket_id='ws1'
        )
        
        self.websocket = MagicMock()
        self.websocket.id = 'ws1'
        self.websocket.state = WebSocketState.CONNECTED
    
    @pytest.mark.asyncio
    async def test_add_user(self):
        """Test adding users to the system."""
        success = await self.realtime_manager.add_user(self.user, self.websocket)
        
        assert success is True
        assert self.user.id in self.realtime_manager.users
        assert self.realtime_manager.user_websocket_map[self.user.id] == self.websocket.id
        assert self.realtime_manager.stats['total_users'] == 1
    
    @pytest.mark.asyncio
    async def test_remove_user(self):
        """Test removing users from the system."""
        await self.realtime_manager.add_user(self.user, self.websocket)
        removed_user = await self.realtime_manager.remove_user(self.user.id)
        
        assert removed_user == self.user
        assert self.user.id not in self.realtime_manager.users
        assert self.realtime_manager.stats['total_users'] == 0
    
    @pytest.mark.asyncio
    async def test_create_room(self):
        """Test creating rooms."""
        room = await self.realtime_manager.create_room(
            room_id='room1',
            name='Test Room',
            description='A test room'
        )
        
        assert room.id == 'room1'
        assert room.name == 'Test Room'
        assert 'room1' in self.realtime_manager.rooms
        assert self.realtime_manager.stats['total_rooms'] == 1
    
    @pytest.mark.asyncio
    async def test_join_room(self):
        """Test joining rooms."""
        # Create room and add user
        await self.realtime_manager.create_room('room1', 'Test Room')
        await self.realtime_manager.add_user(self.user, self.websocket)
        
        success = await self.realtime_manager.join_room('room1', self.user.id)
        
        assert success is True
        room = await self.realtime_manager.get_room('room1')
        assert self.user.id in room.users
    
    @pytest.mark.asyncio
    async def test_leave_room(self):
        """Test leaving rooms."""
        # Setup room and user
        await self.realtime_manager.create_room('room1', 'Test Room')
        await self.realtime_manager.add_user(self.user, self.websocket)
        await self.realtime_manager.join_room('room1', self.user.id)
        
        success = await self.realtime_manager.leave_room('room1', self.user.id)
        
        assert success is True
        room = await self.realtime_manager.get_room('room1')
        assert self.user.id not in room.users
    
    @pytest.mark.asyncio
    async def test_create_channel(self):
        """Test creating channels."""
        channel = await self.realtime_manager.create_channel(
            channel_id='channel1',
            name='Test Channel',
            is_persistent=True
        )
        
        assert channel.id == 'channel1'
        assert channel.name == 'Test Channel'
        assert channel.is_persistent is True
        assert 'channel1' in self.realtime_manager.channels
    
    @pytest.mark.asyncio
    async def test_subscribe_to_channel(self):
        """Test subscribing to channels."""
        await self.realtime_manager.create_channel('channel1', 'Test Channel')
        
        success = await self.realtime_manager.subscribe_to_channel('channel1', self.user.id)
        
        assert success is True
        channel = await self.realtime_manager.get_channel('channel1')
        assert self.user.id in channel.subscribers


class TestWebSocketMessage:
    """Test WebSocket message functionality."""
    
    def test_message_creation(self):
        """Test creating WebSocket messages."""
        message = WebSocketMessage('test', {'data': 'value'})
        
        assert message.type == 'test'
        assert message.data == {'data': 'value'}
        assert message.id is not None
        assert message.timestamp is not None
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        message = WebSocketMessage('test', {'data': 'value'})
        message_dict = message.to_dict()
        
        assert 'id' in message_dict
        assert 'type' in message_dict
        assert 'data' in message_dict
        assert 'timestamp' in message_dict
        assert message_dict['type'] == 'test'
        assert message_dict['data'] == {'data': 'value'}
    
    def test_message_to_json(self):
        """Test converting message to JSON."""
        message = WebSocketMessage('test', {'data': 'value'})
        json_str = message.to_json()
        
        parsed = json.loads(json_str)
        assert parsed['type'] == 'test'
        assert parsed['data'] == {'data': 'value'}


class TestUser:
    """Test User model."""
    
    def test_user_creation(self):
        """Test creating users."""
        user = User(
            id='user1',
            name='TestUser',
            websocket_id='ws1',
            metadata={'role': 'admin'}
        )
        
        assert user.id == 'user1'
        assert user.name == 'TestUser'
        assert user.websocket_id == 'ws1'
        assert user.metadata['role'] == 'admin'
        assert user.joined_at is not None
    
    def test_user_to_dict(self):
        """Test converting user to dictionary."""
        user = User(id='user1', name='TestUser', websocket_id='ws1')
        user_dict = user.to_dict()
        
        assert user_dict['id'] == 'user1'
        assert user_dict['name'] == 'TestUser'
        assert 'joined_at' in user_dict
        assert 'last_seen' in user_dict


class TestRoom:
    """Test Room model."""
    
    def test_room_creation(self):
        """Test creating rooms."""
        room = Room(
            id='room1',
            name='Test Room',
            description='A test room',
            max_users=10
        )
        
        assert room.id == 'room1'
        assert room.name == 'Test Room'
        assert room.max_users == 10
        assert room.get_user_count() == 0
    
    def test_room_user_management(self):
        """Test adding and removing users from rooms."""
        room = Room(id='room1', name='Test Room', max_users=2)
        user1 = User(id='user1', name='User1', websocket_id='ws1')
        user2 = User(id='user2', name='User2', websocket_id='ws2')
        user3 = User(id='user3', name='User3', websocket_id='ws3')
        
        # Add users
        assert room.add_user(user1) is True
        assert room.add_user(user2) is True
        assert room.get_user_count() == 2
        
        # Try to add user when room is full
        assert room.add_user(user3) is False
        
        # Remove user
        removed = room.remove_user('user1')
        assert removed == user1
        assert room.get_user_count() == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
