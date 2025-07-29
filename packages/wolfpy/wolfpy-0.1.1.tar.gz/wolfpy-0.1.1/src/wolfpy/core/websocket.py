"""
WolfPy WebSocket Support - Phase 11 Real-Time Support

This module provides WebSocket connection management and real-time communication
capabilities for WolfPy applications.

Features:
- WebSocket connection lifecycle management
- Message handling (text/binary/JSON)
- Connection pooling and broadcasting
- Room-based communication
- Event-driven architecture
- Connection state management
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Callable, Union, Set
from enum import Enum


class WebSocketState(Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class WebSocketMessage:
    """Represents a WebSocket message."""
    
    def __init__(self, message_type: str, data: Any, timestamp: float = None):
        self.type = message_type
        self.data = data
        self.timestamp = timestamp or time.time()
        self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'data': self.data,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class WebSocket:
    """
    WebSocket connection wrapper for ASGI.
    
    Provides high-level interface for WebSocket communication including:
    - Connection management
    - Message sending/receiving
    - JSON message handling
    - Connection state tracking
    - Event callbacks
    """
    
    def __init__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        self.scope = scope
        self.receive = receive
        self.send = send
        self.state = WebSocketState.CONNECTING
        self.id = str(uuid.uuid4())
        self.path = scope.get('path', '/')
        self.query_string = scope.get('query_string', b'').decode('utf-8')
        self.headers = self._parse_headers(scope.get('headers', []))
        self.client_info = scope.get('client', ['unknown', 0])
        self.connected_at = time.time()
        self.last_ping = time.time()
        
        # Event callbacks
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # User data
        self.user_data: Dict[str, Any] = {}
        
        # Message queue for buffering
        self._message_queue: List[Dict[str, Any]] = []
        self._queue_lock = asyncio.Lock()
    
    def _parse_headers(self, headers: List[List[bytes]]) -> Dict[str, str]:
        """Parse ASGI headers."""
        parsed = {}
        for name, value in headers:
            parsed[name.decode('latin1').lower()] = value.decode('latin1')
        return parsed
    
    @property
    def client_ip(self) -> str:
        """Get client IP address."""
        return self.client_info[0] if self.client_info else 'unknown'
    
    @property
    def client_port(self) -> int:
        """Get client port."""
        return self.client_info[1] if self.client_info else 0
    
    async def accept(self, subprotocol: Optional[str] = None):
        """Accept WebSocket connection."""
        message = {'type': 'websocket.accept'}
        if subprotocol:
            message['subprotocol'] = subprotocol
        
        await self.send(message)
        self.state = WebSocketState.CONNECTED
        
        if self.on_connect:
            await self._safe_callback(self.on_connect, self)
    
    async def close(self, code: int = 1000, reason: str = ""):
        """Close WebSocket connection."""
        if self.state in [WebSocketState.DISCONNECTING, WebSocketState.DISCONNECTED]:
            return
        
        self.state = WebSocketState.DISCONNECTING
        
        await self.send({
            'type': 'websocket.close',
            'code': code,
            'reason': reason
        })
        
        self.state = WebSocketState.DISCONNECTED
        
        if self.on_disconnect:
            await self._safe_callback(self.on_disconnect, self, code, reason)
    
    async def send_text(self, text: str):
        """Send text message."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket not connected")
        
        await self.send({
            'type': 'websocket.send',
            'text': text
        })
    
    async def send_bytes(self, data: bytes):
        """Send binary message."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket not connected")
        
        await self.send({
            'type': 'websocket.send',
            'bytes': data
        })
    
    async def send_json(self, data: Any):
        """Send JSON message."""
        json_str = json.dumps(data, default=str)
        await self.send_text(json_str)
    
    async def send_message(self, message: WebSocketMessage):
        """Send WebSocketMessage object."""
        await self.send_json(message.to_dict())
    
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from WebSocket."""
        try:
            message = await self.receive()
            
            if message['type'] == 'websocket.receive':
                if 'text' in message:
                    return {
                        'type': 'text',
                        'data': message['text']
                    }
                elif 'bytes' in message:
                    return {
                        'type': 'bytes',
                        'data': message['bytes']
                    }
            elif message['type'] == 'websocket.disconnect':
                self.state = WebSocketState.DISCONNECTED
                if self.on_disconnect:
                    code = message.get('code', 1000)
                    reason = message.get('reason', '')
                    await self._safe_callback(self.on_disconnect, self, code, reason)
                return None
            
        except Exception as e:
            if self.on_error:
                await self._safe_callback(self.on_error, self, e)
            return None
        
        return None
    
    async def receive_json(self) -> Optional[Any]:
        """Receive and parse JSON message."""
        message = await self.receive_message()
        if message and message['type'] == 'text':
            try:
                return json.loads(message['data'])
            except json.JSONDecodeError:
                return None
        return None
    
    async def ping(self, data: bytes = b''):
        """Send ping frame."""
        await self.send({
            'type': 'websocket.ping',
            'bytes': data
        })
        self.last_ping = time.time()
    
    async def pong(self, data: bytes = b''):
        """Send pong frame."""
        await self.send({
            'type': 'websocket.pong',
            'bytes': data
        })
    
    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Safely execute callback with error handling."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            print(f"WebSocket callback error: {e}")
    
    def __str__(self) -> str:
        return f"WebSocket(id={self.id}, path={self.path}, state={self.state.value})"
    
    def __repr__(self) -> str:
        return self.__str__()


class WebSocketManager:
    """
    Manages multiple WebSocket connections.
    
    Provides:
    - Connection pooling
    - Broadcasting capabilities
    - Connection lifecycle management
    - Statistics and monitoring
    """
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.connections_by_path: Dict[str, Set[str]] = {}
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_received': 0
        }
        self._lock = asyncio.Lock()
    
    async def add_connection(self, websocket: WebSocket):
        """Add WebSocket connection to manager."""
        async with self._lock:
            self.connections[websocket.id] = websocket
            
            # Group by path
            if websocket.path not in self.connections_by_path:
                self.connections_by_path[websocket.path] = set()
            self.connections_by_path[websocket.path].add(websocket.id)
            
            # Update stats
            self.connection_stats['total_connections'] += 1
            self.connection_stats['active_connections'] = len(self.connections)
    
    async def remove_connection(self, websocket: WebSocket):
        """Remove WebSocket connection from manager."""
        async with self._lock:
            if websocket.id in self.connections:
                del self.connections[websocket.id]
                
                # Remove from path grouping
                if websocket.path in self.connections_by_path:
                    self.connections_by_path[websocket.path].discard(websocket.id)
                    if not self.connections_by_path[websocket.path]:
                        del self.connections_by_path[websocket.path]
                
                # Update stats
                self.connection_stats['active_connections'] = len(self.connections)
    
    async def get_connection(self, connection_id: str) -> Optional[WebSocket]:
        """Get connection by ID."""
        return self.connections.get(connection_id)
    
    async def get_connections_by_path(self, path: str) -> List[WebSocket]:
        """Get all connections for a specific path."""
        connection_ids = self.connections_by_path.get(path, set())
        return [self.connections[conn_id] for conn_id in connection_ids 
                if conn_id in self.connections]
    
    async def broadcast_to_all(self, message: Union[str, Dict[str, Any], WebSocketMessage]):
        """Broadcast message to all connections."""
        if not self.connections:
            return
        
        tasks = []
        for websocket in self.connections.values():
            if websocket.state == WebSocketState.CONNECTED:
                tasks.append(self._send_message_safe(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            self.connection_stats['messages_sent'] += len(tasks)
    
    async def broadcast_to_path(self, path: str, message: Union[str, Dict[str, Any], WebSocketMessage]):
        """Broadcast message to all connections on a specific path."""
        connections = await self.get_connections_by_path(path)
        if not connections:
            return
        
        tasks = []
        for websocket in connections:
            if websocket.state == WebSocketState.CONNECTED:
                tasks.append(self._send_message_safe(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            self.connection_stats['messages_sent'] += len(tasks)
    
    async def _send_message_safe(self, websocket: WebSocket, message: Union[str, Dict[str, Any], WebSocketMessage]):
        """Safely send message to WebSocket."""
        try:
            if isinstance(message, str):
                await websocket.send_text(message)
            elif isinstance(message, WebSocketMessage):
                await websocket.send_message(message)
            else:
                await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message to {websocket.id}: {e}")
            # Remove failed connection
            await self.remove_connection(websocket)
    
    async def cleanup_disconnected(self):
        """Remove disconnected connections."""
        disconnected = []
        for websocket in self.connections.values():
            if websocket.state == WebSocketState.DISCONNECTED:
                disconnected.append(websocket)
        
        for websocket in disconnected:
            await self.remove_connection(websocket)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            **self.connection_stats,
            'connections_by_path': {
                path: len(conn_ids) 
                for path, conn_ids in self.connections_by_path.items()
            }
        }
