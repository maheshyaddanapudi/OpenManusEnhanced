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
import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, Tuple

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from agent.core.base import event_emitter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0  # Initial delay in seconds
        self.receive_task = None
    
    async def connect(self, url: str = "ws://localhost:3001/agent") -> bool:
        """
        Connect to the Node.js backend via WebSocket.
        
        Args:
            url: WebSocket URL to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Establish WebSocket connection
            self.socket = await websockets.connect(
                f"{url}?session_id={self.session_id}",
                ping_interval=20,
                ping_timeout=30,
                close_timeout=10
            )
            
            logger.info(f"Connected to WebSocket server: {url}")
            self.connected = True
            self.reconnect_attempts = 0
            
            # Start message processing loop
            if not self.running:
                self.running = True
                asyncio.create_task(self._process_messages())
            
            # Start receive loop
            self.receive_task = asyncio.create_task(self._receive_messages())
            
            # Subscribe to events
            self._subscribe_to_events()
            
            # Send connection event
            await self.send_message("connection", {
                "status": "connected",
                "client_info": {
                    "type": "python_agent",
                    "version": "1.0.0"
                }
            })
            
            return True
            
        except (WebSocketException, ConnectionError, OSError) as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            self.connected = False
            return False
    
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
        
        # Cancel receive task if running
        if self.receive_task and not self.receive_task.done():
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket connection
        if self.socket:
            try:
                await self.socket.close()
                logger.info(f"Disconnected from WebSocket server for session {self.session_id}")
            except WebSocketException as e:
                logger.error(f"Error closing WebSocket connection: {e}")
        
        self.connected = False
        self.socket = None
        
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
                
                if self.socket and self.connected:
                    # Serialize message to JSON
                    message_json = json.dumps(message)
                    
                    # Send message over WebSocket
                    try:
                        await self.socket.send(message_json)
                        logger.debug(f"Sent message: {message['type']}")
                    except (WebSocketException, ConnectionError) as e:
                        logger.error(f"Error sending message: {e}")
                        # Try to reconnect
                        await self._attempt_reconnect()
                        # Put message back in queue
                        await self.message_queue.put(message)
                
                # Mark message as processed
                self.message_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing message: {e}")
            
            # Prevent tight loop
            await asyncio.sleep(0.01)
    
    async def _receive_messages(self) -> None:
        """
        Receive messages from the Node.js backend.
        """
        while self.running and self.socket:
            try:
                # Receive message
                message_json = await self.socket.recv()
                
                # Parse message
                try:
                    message = json.loads(message_json)
                    logger.debug(f"Received message: {message.get('type', 'unknown')}")
                    
                    # Handle message
                    await self._handle_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing message: {e}")
                
            except ConnectionClosed:
                logger.warning(f"WebSocket connection closed for session {self.session_id}")
                # Try to reconnect
                await self._attempt_reconnect()
            except WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                # Try to reconnect
                await self._attempt_reconnect()
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                # Brief pause before continuing
                await asyncio.sleep(0.1)
    
    async def _attempt_reconnect(self) -> bool:
        """
        Attempt to reconnect to the WebSocket server.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Maximum reconnection attempts reached for session {self.session_id}")
            self.connected = False
            return False
        
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))  # Exponential backoff
        
        logger.info(f"Attempting to reconnect in {delay:.1f} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        
        # Wait before reconnecting
        await asyncio.sleep(delay)
        
        # Close existing socket if any
        if self.socket:
            try:
                await self.socket.close()
            except:
                pass
            self.socket = None
        
        # Reconnect
        self.connected = False
        return await self.connect()
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a message from the Node.js backend.
        
        Args:
            message: Message to handle
        """
        message_type = message.get("type")
        data = message.get("data", {})
        
        if message_type == "ping":
            # Respond to ping
            await self.send_message("pong", {"received_at": time.time()})
        
        elif message_type == "human_control":
            # Handle human control message
            control_type = data.get("control_type")
            
            if control_type == "takeover":
                # Emit human takeover event
                event_emitter.emit("human:interaction", {
                    "type": "takeover",
                    "user_id": data.get("user_id"),
                    "timestamp": data.get("timestamp")
                })
            
            elif control_type == "release":
                # Emit human release event
                event_emitter.emit("human:interaction", {
                    "type": "release",
                    "user_id": data.get("user_id"),
                    "timestamp": data.get("timestamp")
                })
            
            elif control_type == "message":
                # Emit human message event
                event_emitter.emit("human:interaction", {
                    "type": "message",
                    "user_id": data.get("user_id"),
                    "message": data.get("message"),
                    "timestamp": data.get("timestamp")
                })
        
        elif message_type == "tool_response":
            # Handle tool response
            tool_name = data.get("tool_name")
            result = data.get("result")
            
            # Emit tool response event
            event_emitter.emit(f"tool:{tool_name}:response", {
                "tool_name": tool_name,
                "result": result,
                "timestamp": data.get("timestamp")
            })
        
        elif message_type == "session_control":
            # Handle session control message
            control_type = data.get("control_type")
            
            if control_type == "terminate":
                # Emit session terminate event
                event_emitter.emit("session:terminate", {
                    "reason": data.get("reason"),
                    "timestamp": data.get("timestamp")
                })
            
            elif control_type == "pause":
                # Emit session pause event
                event_emitter.emit("session:pause", {
                    "reason": data.get("reason"),
                    "timestamp": data.get("timestamp")
                })
            
            elif control_type == "resume":
                # Emit session resume event
                event_emitter.emit("session:resume", {
                    "timestamp": data.get("timestamp")
                })
    
    def _subscribe_to_events(self) -> None:
        """
        Subscribe to events from the event emitter.
        """
        # Subscribe to agent events
        self.event_subscriptions.append(
            (event_emitter.subscribe("agent:state_change", self._on_agent_event), "agent:state_change")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("agent:run_start", self._on_agent_event), "agent:run_start")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("agent:run_end", self._on_agent_event), "agent:run_end")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("agent:step_start", self._on_agent_event), "agent:step_start")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("agent:step_end", self._on_agent_event), "agent:step_end")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("agent:error", self._on_agent_event), "agent:error")
        )
        
        # Subscribe to tool events
        self.event_subscriptions.append(
            (event_emitter.subscribe("tool:start", self._on_tool_event), "tool:start")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("tool:completed", self._on_tool_event), "tool:completed")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("tool:error", self._on_tool_event), "tool:error")
        )
        
        # Subscribe to memory events
        self.event_subscriptions.append(
            (event_emitter.subscribe("memory:message_added", self._on_memory_event), "memory:message_added")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("memory:cleared", self._on_memory_event), "memory:cleared")
        )
        
        # Subscribe to visualization events
        self.event_subscriptions.append(
            (event_emitter.subscribe("visualization:browser_update", self._on_visualization_event), "visualization:browser_update")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("visualization:browser_action", self._on_visualization_event), "visualization:browser_action")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("visualization:browser_close", self._on_visualization_event), "visualization:browser_close")
        )
        self.event_subscriptions.append(
            (event_emitter.subscribe("visualization:agent_thinking", self._on_visualization_event), "visualization:agent_thinking")
        )
    
    def _unsubscribe_from_events(self) -> None:
        """
        Unsubscribe from events from the event emitter.
        """
        for subscription_id, event_type in self.event_subscriptions:
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
        success = await connection.connect(url)
        
        if not success:
            logger.error(f"Failed to connect bridge for session {session_id}")
            with self.lock:
                if session_id in self.connections:
                    del self.connections[session_id]
            return None
        
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

async def initialize_bridge(session_id: str, url: str = "ws://localhost:3001/agent") -> Optional[BridgeConnection]:
    """
    Initialize the bridge for a session.
    
    Args:
        session_id: Session ID
        url: WebSocket URL to connect to
        
    Returns:
        Bridge connection if successful, None otherwise
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
