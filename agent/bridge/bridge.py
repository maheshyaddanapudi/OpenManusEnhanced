"""
Bridge Module for OpenManusEnhanced

This module provides the communication bridge between the Python agent
and the Node.js backend for real-time visualization and control.

Features:
- WebSocket-based communication
- Event forwarding
- Session management
- Human control coordination
"""

import asyncio
import json
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Callable

from agent.core.base import event_emitter

class BridgeConnection:
    """
    Manages the connection between the Python agent and Node.js backend.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.connected = False
        self.socket = None
        self.event_subscriptions = []
        self.message_queue = asyncio.Queue()
        self.running = False
        self.lock = threading.Lock()
    
    async def connect(self, url: str = "ws://localhost:3001/agent") -> bool:
        """
        Connect to the Node.js backend via WebSocket.
        
        Args:
            url: WebSocket URL to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        # This is a placeholder - in a real implementation, this would
        # establish a WebSocket connection to the Node.js backend
        
        # For now, we'll simulate a successful connection
        self.connected = True
        
        # Start message processing loop
        if not self.running:
            self.running = True
            asyncio.create_task(self._process_messages())
        
        # Subscribe to events
        self._subscribe_to_events()
        
        return True
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the Node.js backend.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        # Unsubscribe from events
        self._unsubscribe_from_events()
        
        # Stop message processing loop
        self.running = False
        
        # This is a placeholder - in a real implementation, this would
        # close the WebSocket connection
        
        # For now, we'll simulate a successful disconnection
        self.connected = False
        
        return True
    
    async def send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """
        Send a message to the Node.js backend.
        
        Args:
            message_type: Type of message to send
            data: Message data
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.connected:
            return False
        
        # Create message
        message = {
            "type": message_type,
            "data": data,
            "session_id": self.session_id,
            "timestamp": time.time()
        }
        
        # Add message to queue
        await self.message_queue.put(message)
        
        return True
    
    async def _process_messages(self) -> None:
        """
        Process messages in the queue and send them to the Node.js backend.
        """
        while self.running:
            try:
                # Get message from queue
                message = await self.message_queue.get()
                
                # This is a placeholder - in a real implementation, this would
                # send the message over the WebSocket connection
                
                # For now, we'll just print the message
                print(f"Sending message: {json.dumps(message)}")
                
                # Mark message as processed
                self.message_queue.task_done()
            except Exception as e:
                print(f"Error processing message: {e}")
            
            # Prevent tight loop
            await asyncio.sleep(0.01)
    
    def _subscribe_to_events(self) -> None:
        """
        Subscribe to events from the event emitter.
        """
        # Subscribe to agent events
        self.event_subscriptions.append(
            event_emitter.subscribe("agent:state_change", self._on_agent_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("agent:run_start", self._on_agent_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("agent:run_end", self._on_agent_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("agent:step_start", self._on_agent_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("agent:step_end", self._on_agent_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("agent:error", self._on_agent_event)
        )
        
        # Subscribe to tool events
        self.event_subscriptions.append(
            event_emitter.subscribe("tool:start", self._on_tool_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("tool:completed", self._on_tool_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("tool:error", self._on_tool_event)
        )
        
        # Subscribe to memory events
        self.event_subscriptions.append(
            event_emitter.subscribe("memory:message_added", self._on_memory_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("memory:cleared", self._on_memory_event)
        )
        
        # Subscribe to visualization events
        self.event_subscriptions.append(
            event_emitter.subscribe("visualization:browser_update", self._on_visualization_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("visualization:browser_action", self._on_visualization_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("visualization:browser_close", self._on_visualization_event)
        )
        self.event_subscriptions.append(
            event_emitter.subscribe("visualization:agent_thinking", self._on_visualization_event)
        )
    
    def _unsubscribe_from_events(self) -> None:
        """
        Unsubscribe from events from the event emitter.
        """
        for event_type, subscription_id in self.event_subscriptions:
            event_emitter.unsubscribe(event_type, subscription_id)
        
        self.event_subscriptions = []
    
    def _on_agent_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle agent events.
        
        Args:
            event_data: Event data
        """
        # Forward event to Node.js backend
        asyncio.create_task(self.send_message("agent_event", event_data))
    
    def _on_tool_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle tool events.
        
        Args:
            event_data: Event data
        """
        # Forward event to Node.js backend
        asyncio.create_task(self.send_message("tool_event", event_data))
    
    def _on_memory_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle memory events.
        
        Args:
            event_data: Event data
        """
        # Forward event to Node.js backend
        asyncio.create_task(self.send_message("memory_event", event_data))
    
    def _on_visualization_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle visualization events.
        
        Args:
            event_data: Event data
        """
        # Forward event to Node.js backend
        asyncio.create_task(self.send_message("visualization_event", event_data))

class BridgeManager:
    """
    Manages bridge connections for multiple agent sessions.
    """
    def __init__(self):
        self.connections = {}
        self.lock = threading.Lock()
    
    async def create_connection(self, session_id: str, url: str = "ws://localhost:3001/agent") -> BridgeConnection:
        """
        Create a new bridge connection for a session.
        
        Args:
            session_id: Session ID
            url: WebSocket URL to connect to
            
        Returns:
            Bridge connection
        """
        with self.lock:
            # Check if connection already exists
            if session_id in self.connections:
                return self.connections[session_id]
            
            # Create new connection
            connection = BridgeConnection(session_id)
            self.connections[session_id] = connection
        
        # Connect
        await connection.connect(url)
        
        return connection
    
    async def get_connection(self, session_id: str) -> Optional[BridgeConnection]:
        """
        Get an existing bridge connection for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Bridge connection if exists, None otherwise
        """
        with self.lock:
            return self.connections.get(session_id)
    
    async def close_connection(self, session_id: str) -> bool:
        """
        Close a bridge connection for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if connection closed successfully, False otherwise
        """
        connection = None
        
        with self.lock:
            # Check if connection exists
            if session_id not in self.connections:
                return False
            
            # Get connection
            connection = self.connections[session_id]
            
            # Remove from connections
            del self.connections[session_id]
        
        # Disconnect
        if connection:
            await connection.disconnect()
        
        return True
    
    async def close_all_connections(self) -> None:
        """
        Close all bridge connections.
        """
        # Get all session IDs
        session_ids = []
        
        with self.lock:
            session_ids = list(self.connections.keys())
        
        # Close each connection
        for session_id in session_ids:
            await self.close_connection(session_id)

# Global bridge manager instance
bridge_manager = BridgeManager()

async def initialize_bridge(session_id: str, url: str = "ws://localhost:3001/agent") -> BridgeConnection:
    """
    Initialize the bridge for a session.
    
    Args:
        session_id: Session ID
        url: WebSocket URL to connect to
        
    Returns:
        Bridge connection
    """
    return await bridge_manager.create_connection(session_id, url)

async def close_bridge(session_id: str) -> bool:
    """
    Close the bridge for a session.
    
    Args:
        session_id: Session ID
        
    Returns:
        True if bridge closed successfully, False otherwise
    """
    return await bridge_manager.close_connection(session_id)

async def get_bridge(session_id: str) -> Optional[BridgeConnection]:
    """
    Get the bridge for a session.
    
    Args:
        session_id: Session ID
        
    Returns:
        Bridge connection if exists, None otherwise
    """
    return await bridge_manager.get_connection(session_id)

async def send_event(session_id: str, event_type: str, data: Dict[str, Any]) -> bool:
    """
    Send an event to the Node.js backend.
    
    Args:
        session_id: Session ID
        event_type: Type of event to send
        data: Event data
        
    Returns:
        True if event sent successfully, False otherwise
    """
    bridge = await get_bridge(session_id)
    if not bridge:
        return False
    
    return await bridge.send_message(event_type, data)

async def cleanup() -> None:
    """
    Clean up all bridge connections.
    """
    await bridge_manager.close_all_connections()
