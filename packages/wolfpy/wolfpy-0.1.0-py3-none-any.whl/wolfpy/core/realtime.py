"""
WolfPy Real-Time Features - Phase 11 Real-Time Support

This module provides advanced real-time communication features including:
- Room-based messaging
- Channel subscriptions
- Event broadcasting
- Message queuing
- Presence tracking
- Real-time notifications
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Set, Callable, Union
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from .websocket import WebSocket, WebSocketMessage, WebSocketManager


class EventType(Enum):
    """Real-time event types."""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    MESSAGE = "message"
    BROADCAST = "broadcast"
    NOTIFICATION = "notification"
    PRESENCE_UPDATE = "presence_update"
    ROOM_UPDATE = "room_update"
    CHANNEL_UPDATE = "channel_update"


@dataclass
class User:
    """Represents a connected user."""
    id: str
    name: str
    websocket_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    joined_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'metadata': self.metadata,
            'joined_at': self.joined_at,
            'last_seen': self.last_seen
        }


@dataclass
class Room:
    """
    Represents a chat room or communication channel.
    
    Rooms allow grouping users for targeted messaging and provide:
    - User management
    - Message broadcasting
    - Presence tracking
    - Room-specific events
    """
    id: str
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    max_users: Optional[int] = None
    is_private: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    users: Dict[str, User] = field(default_factory=dict)
    message_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_user(self, user: User) -> bool:
        """Add user to room."""
        if self.max_users and len(self.users) >= self.max_users:
            return False
        
        self.users[user.id] = user
        return True
    
    def remove_user(self, user_id: str) -> Optional[User]:
        """Remove user from room."""
        return self.users.pop(user_id, None)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_user_count(self) -> int:
        """Get number of users in room."""
        return len(self.users)
    
    def add_message(self, message: Dict[str, Any], max_history: int = 100):
        """Add message to room history."""
        self.message_history.append(message)
        if len(self.message_history) > max_history:
            self.message_history = self.message_history[-max_history:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert room to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'max_users': self.max_users,
            'is_private': self.is_private,
            'metadata': self.metadata,
            'user_count': self.get_user_count(),
            'users': [user.to_dict() for user in self.users.values()]
        }


@dataclass
class Channel:
    """
    Represents a pub/sub channel for event broadcasting.
    
    Channels provide:
    - Topic-based messaging
    - Subscription management
    - Event filtering
    - Message persistence
    """
    id: str
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    is_persistent: bool = False
    subscribers: Set[str] = field(default_factory=set)
    message_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def subscribe(self, user_id: str):
        """Subscribe user to channel."""
        self.subscribers.add(user_id)
    
    def unsubscribe(self, user_id: str):
        """Unsubscribe user from channel."""
        self.subscribers.discard(user_id)
    
    def add_message(self, message: Dict[str, Any], max_history: int = 1000):
        """Add message to channel history."""
        if self.is_persistent:
            self.message_history.append(message)
            if len(self.message_history) > max_history:
                self.message_history = self.message_history[-max_history:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert channel to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'is_persistent': self.is_persistent,
            'subscriber_count': len(self.subscribers),
            'metadata': self.metadata
        }


class RealtimeManager:
    """
    Manages real-time communication features.
    
    Provides:
    - Room management
    - Channel subscriptions
    - Event broadcasting
    - User presence tracking
    - Message routing
    """
    
    def __init__(self, websocket_manager: Optional[WebSocketManager] = None):
        self.websocket_manager = websocket_manager or WebSocketManager()
        self.rooms: Dict[str, Room] = {}
        self.channels: Dict[str, Channel] = {}
        self.users: Dict[str, User] = {}
        self.user_websocket_map: Dict[str, str] = {}  # user_id -> websocket_id
        self.websocket_user_map: Dict[str, str] = {}  # websocket_id -> user_id
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        
        # Statistics
        self.stats = {
            'total_rooms': 0,
            'total_channels': 0,
            'total_users': 0,
            'messages_sent': 0,
            'events_fired': 0
        }
        
        self._lock = asyncio.Lock()
    
    # User Management
    async def add_user(self, user: User, websocket: WebSocket) -> bool:
        """Add user to the system."""
        async with self._lock:
            self.users[user.id] = user
            self.user_websocket_map[user.id] = websocket.id
            self.websocket_user_map[websocket.id] = user.id
            self.stats['total_users'] = len(self.users)
            
            await self._fire_event(EventType.USER_JOINED, {
                'user': user.to_dict(),
                'websocket_id': websocket.id
            })
            
            return True
    
    async def remove_user(self, user_id: str) -> Optional[User]:
        """Remove user from the system."""
        async with self._lock:
            user = self.users.pop(user_id, None)
            if user:
                websocket_id = self.user_websocket_map.pop(user_id, None)
                if websocket_id:
                    self.websocket_user_map.pop(websocket_id, None)
                
                # Remove user from all rooms
                for room in self.rooms.values():
                    room.remove_user(user_id)
                
                # Unsubscribe from all channels
                for channel in self.channels.values():
                    channel.unsubscribe(user_id)
                
                self.stats['total_users'] = len(self.users)
                
                await self._fire_event(EventType.USER_LEFT, {
                    'user': user.to_dict(),
                    'websocket_id': websocket_id
                })
            
            return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    async def get_user_by_websocket(self, websocket_id: str) -> Optional[User]:
        """Get user by WebSocket ID."""
        user_id = self.websocket_user_map.get(websocket_id)
        return self.users.get(user_id) if user_id else None
    
    # Room Management
    async def create_room(self, room_id: str, name: str, **kwargs) -> Room:
        """Create a new room."""
        async with self._lock:
            room = Room(id=room_id, name=name, **kwargs)
            self.rooms[room_id] = room
            self.stats['total_rooms'] = len(self.rooms)
            
            await self._fire_event(EventType.ROOM_UPDATE, {
                'action': 'created',
                'room': room.to_dict()
            })
            
            return room
    
    async def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        return self.rooms.get(room_id)
    
    async def delete_room(self, room_id: str) -> bool:
        """Delete a room."""
        async with self._lock:
            room = self.rooms.pop(room_id, None)
            if room:
                # Notify users in the room
                await self.broadcast_to_room(room_id, {
                    'type': 'room_deleted',
                    'room_id': room_id
                })
                
                self.stats['total_rooms'] = len(self.rooms)
                
                await self._fire_event(EventType.ROOM_UPDATE, {
                    'action': 'deleted',
                    'room_id': room_id
                })
                
                return True
            return False
    
    async def join_room(self, room_id: str, user_id: str) -> bool:
        """Add user to room."""
        room = await self.get_room(room_id)
        user = await self.get_user(user_id)
        
        if not room or not user:
            return False
        
        if room.add_user(user):
            await self.broadcast_to_room(room_id, {
                'type': 'user_joined_room',
                'room_id': room_id,
                'user': user.to_dict()
            }, exclude_user=user_id)
            
            return True
        return False
    
    async def leave_room(self, room_id: str, user_id: str) -> bool:
        """Remove user from room."""
        room = await self.get_room(room_id)
        if not room:
            return False
        
        user = room.remove_user(user_id)
        if user:
            await self.broadcast_to_room(room_id, {
                'type': 'user_left_room',
                'room_id': room_id,
                'user': user.to_dict()
            })
            return True
        return False
    
    # Channel Management
    async def create_channel(self, channel_id: str, name: str, **kwargs) -> Channel:
        """Create a new channel."""
        async with self._lock:
            channel = Channel(id=channel_id, name=name, **kwargs)
            self.channels[channel_id] = channel
            self.stats['total_channels'] = len(self.channels)
            
            await self._fire_event(EventType.CHANNEL_UPDATE, {
                'action': 'created',
                'channel': channel.to_dict()
            })
            
            return channel
    
    async def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get channel by ID."""
        return self.channels.get(channel_id)
    
    async def subscribe_to_channel(self, channel_id: str, user_id: str) -> bool:
        """Subscribe user to channel."""
        channel = await self.get_channel(channel_id)
        if channel:
            channel.subscribe(user_id)
            return True
        return False
    
    async def unsubscribe_from_channel(self, channel_id: str, user_id: str) -> bool:
        """Unsubscribe user from channel."""
        channel = await self.get_channel(channel_id)
        if channel:
            channel.unsubscribe(user_id)
            return True
        return False
    
    # Broadcasting
    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude_user: str = None):
        """Broadcast message to all users in a room."""
        room = await self.get_room(room_id)
        if not room:
            return
        
        # Add message to room history
        room.add_message({
            **message,
            'timestamp': time.time(),
            'id': str(uuid.uuid4())
        })
        
        # Send to all users in room
        tasks = []
        for user in room.users.values():
            if exclude_user and user.id == exclude_user:
                continue
            
            websocket_id = self.user_websocket_map.get(user.id)
            if websocket_id:
                websocket = await self.websocket_manager.get_connection(websocket_id)
                if websocket:
                    tasks.append(self._send_message_safe(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            self.stats['messages_sent'] += len(tasks)
    
    async def broadcast_to_channel(self, channel_id: str, message: Dict[str, Any]):
        """Broadcast message to all channel subscribers."""
        channel = await self.get_channel(channel_id)
        if not channel:
            return
        
        # Add message to channel history
        channel.add_message({
            **message,
            'timestamp': time.time(),
            'id': str(uuid.uuid4())
        })
        
        # Send to all subscribers
        tasks = []
        for user_id in channel.subscribers:
            websocket_id = self.user_websocket_map.get(user_id)
            if websocket_id:
                websocket = await self.websocket_manager.get_connection(websocket_id)
                if websocket:
                    tasks.append(self._send_message_safe(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            self.stats['messages_sent'] += len(tasks)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user."""
        websocket_id = self.user_websocket_map.get(user_id)
        if websocket_id:
            websocket = await self.websocket_manager.get_connection(websocket_id)
            if websocket:
                await self._send_message_safe(websocket, message)
                self.stats['messages_sent'] += 1
    
    async def _send_message_safe(self, websocket: WebSocket, message: Dict[str, Any]):
        """Safely send message to WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message to {websocket.id}: {e}")
    
    # Event System
    def on(self, event_type: EventType, handler: Callable):
        """Register event handler."""
        self.event_handlers[event_type].append(handler)
    
    async def _fire_event(self, event_type: EventType, data: Dict[str, Any]):
        """Fire event to all registered handlers."""
        handlers = self.event_handlers.get(event_type, [])
        if handlers:
            tasks = []
            for handler in handlers:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event_type, data))
                else:
                    # Run sync handler in thread pool
                    tasks.append(asyncio.get_event_loop().run_in_executor(None, handler, event_type, data))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                self.stats['events_fired'] += len(tasks)
    
    # Statistics
    def get_stats(self) -> Dict[str, Any]:
        """Get real-time system statistics."""
        return {
            **self.stats,
            'rooms': {room_id: room.to_dict() for room_id, room in self.rooms.items()},
            'channels': {channel_id: channel.to_dict() for channel_id, channel in self.channels.items()},
            'websocket_stats': self.websocket_manager.get_stats()
        }
