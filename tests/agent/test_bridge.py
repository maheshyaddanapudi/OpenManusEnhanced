"""
Unit Tests for Bridge Module

This module contains unit tests for the bridge module.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import json
import websockets
from websockets.exceptions import ConnectionClosed

from agent.bridge.bridge import (
    BridgeConnection,
    BridgeManager,
    bridge_manager,
    initialize_bridge,
    close_bridge,
    get_bridge,
    send_event
)
from agent.core.base import event_emitter

class TestBridgeConnection(unittest.TestCase):
    """Test cases for the BridgeConnection class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.session_id = "test_session"
        self.connection = BridgeConnection(self.session_id)
        # Clear event emitter subscriptions
        event_emitter._subscribers = {}
    
    def tearDown(self):
        """Clean up after tests."""
        # Ensure any running tasks are cancelled
        if hasattr(self, 'loop'):
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
    
    def test_init(self):
        """Test initialization of BridgeConnection."""
        self.assertEqual(self.connection.session_id, self.session_id)
        self.assertFalse(self.connection.connected)
        self.assertIsNone(self.connection.socket)
        self.assertEqual(self.connection.event_subscriptions, [])
        self.assertFalse(self.connection.running)
        self.assertEqual(self.connection.reconnect_attempts, 0)
        self.assertEqual(self.connection.max_reconnect_attempts, 5)
        self.assertEqual(self.connection.reconnect_delay, 1.0)
    
    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_connect_success(self, mock_connect):
        """Test successful connection."""
        # Mock websocket connection
        mock_socket = AsyncMock()
        mock_socket.send = AsyncMock()
        mock_socket.recv = AsyncMock()
        mock_connect.return_value = mock_socket
        
        # Call connect method
        result = await self.connection.connect()
        
        # Check connection is established
        self.assertTrue(self.connection.connected)
        self.assertTrue(self.connection.running)
        self.assertIsNotNone(self.connection.socket)
        self.assertEqual(self.connection.reconnect_attempts, 0)
        
        # Check websockets.connect was called with correct URL
        mock_connect.assert_called_once()
        call_args = mock_connect.call_args[0][0]
        self.assertTrue(call_args.startswith("ws://localhost:3001/agent?session_id="))
        
        # Check result is True
        self.assertTrue(result)
        
        # Clean up
        await self.connection.disconnect()
    
    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_connect_failure(self, mock_connect):
        """Test connection failure."""
        # Mock websocket connection to fail
        mock_connect.side_effect = websockets.exceptions.WebSocketException("Connection failed")
        
        # Call connect method
        result = await self.connection.connect()
        
        # Check connection failed
        self.assertFalse(self.connection.connected)
        self.assertIsNone(self.connection.socket)
        
        # Check result is False
        self.assertFalse(result)
    
    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_disconnect(self, mock_connect):
        """Test disconnect method."""
        # Mock websocket connection
        mock_socket = AsyncMock()
        mock_socket.close = AsyncMock()
        mock_connect.return_value = mock_socket
        
        # First connect
        await self.connection.connect()
        
        # Then disconnect
        result = await self.connection.disconnect()
        
        # Check socket was closed
        mock_socket.close.assert_called_once()
        
        # Check connection is closed
        self.assertFalse(self.connection.connected)
        self.assertFalse(self.connection.running)
        self.assertIsNone(self.connection.socket)
        
        # Check result is True
        self.assertTrue(result)
    
    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_send_message(self, mock_connect):
        """Test send_message method."""
        # Mock websocket connection
        mock_socket = AsyncMock()
        mock_socket.send = AsyncMock()
        mock_connect.return_value = mock_socket
        
        # First connect
        await self.connection.connect()
        
        # Send message
        result = await self.connection.send_message("test_type", {"key": "value"})
        
        # Wait for message to be processed
        await asyncio.sleep(0.1)
        
        # Check message was sent
        mock_socket.send.assert_called_once()
        sent_message = json.loads(mock_socket.send.call_args[0][0])
        self.assertEqual(sent_message["type"], "test_type")
        self.assertEqual(sent_message["data"], {"key": "value"})
        self.assertEqual(sent_message["session_id"], self.session_id)
        
        # Check result is True
        self.assertTrue(result)
        
        # Disconnect
        await self.connection.disconnect()
    
    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_send_message_not_connected(self, mock_connect):
        """Test send_message when not connected."""
        # Don't connect
        
        # Send message
        result = await self.connection.send_message("test_type", {"key": "value"})
        
        # Check result is False
        self.assertFalse(result)
    
    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_receive_messages(self, mock_connect):
        """Test receiving messages."""
        # Mock websocket connection
        mock_socket = AsyncMock()
        mock_socket.recv = AsyncMock(side_effect=[
            json.dumps({
                "type": "ping",
                "data": {}
            }),
            json.dumps({
                "type": "human_control",
                "data": {
                    "control_type": "takeover",
                    "user_id": "user123",
                    "timestamp": 1621234567.89
                }
            }),
            ConnectionClosed(1000, "Normal closure")
        ])
        mock_socket.send = AsyncMock()
        mock_connect.return_value = mock_socket
        
        # Mock event emitter
        with patch('agent.core.base.event_emitter.emit') as mock_emit:
            # Connect
            await self.connection.connect()
            
            # Wait for messages to be processed
            await asyncio.sleep(0.2)
            
            # Check event emitter was called for human control message
            mock_emit.assert_called_with("human:interaction", {
                "type": "takeover",
                "user_id": "user123",
                "timestamp": 1621234567.89
            })
            
            # Disconnect
            await self.connection.disconnect()
    
    @patch('websockets.connect', new_callable=AsyncMock)
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_attempt_reconnect(self, mock_sleep, mock_connect):
        """Test reconnection attempts."""
        # Mock first connection to succeed
        mock_socket1 = AsyncMock()
        # Mock second connection to fail
        mock_connect.side_effect = [
            mock_socket1,
            websockets.exceptions.WebSocketException("Connection failed"),
            AsyncMock()  # Third attempt succeeds
        ]
        
        # Connect
        await self.connection.connect()
        self.assertTrue(self.connection.connected)
        
        # Simulate connection closed
        self.connection.socket = None
        self.connection.connected = False
        
        # Attempt reconnect
        result = await self.connection._attempt_reconnect()
        
        # Check reconnect was attempted with backoff
        self.assertEqual(self.connection.reconnect_attempts, 1)
        mock_sleep.assert_called_once_with(1.0)  # Initial delay
        
        # Check result is False (second attempt failed)
        self.assertFalse(result)
        
        # Try again
        mock_sleep.reset_mock()
        result = await self.connection._attempt_reconnect()
        
        # Check reconnect was attempted with exponential backoff
        self.assertEqual(self.connection.reconnect_attempts, 2)
        mock_sleep.assert_called_once_with(2.0)  # Double the delay
        
        # Check result is True (third attempt succeeded)
        self.assertTrue(result)
        self.assertTrue(self.connection.connected)
        
        # Disconnect
        await self.connection.disconnect()
    
    @patch('websockets.connect', new_callable=AsyncMock)
    async def test_event_subscription(self, mock_connect):
        """Test event subscription and forwarding."""
        # Mock websocket connection
        mock_socket = AsyncMock()
        mock_socket.send = AsyncMock()
        mock_connect.return_value = mock_socket
        
        # Connect
        await self.connection.connect()
        
        # Check event subscriptions were created
        self.assertGreater(len(self.connection.event_subscriptions), 0)
        
        # Emit an event
        with patch('asyncio.create_task') as mock_create_task:
            event_emitter.emit("agent:state_change", {"old_state": "IDLE", "new_state": "THINKING"})
            
            # Check send_message was called
            mock_create_task.assert_called()
        
        # Disconnect
        await self.connection.disconnect()
        
        # Check event subscriptions were cleared
        self.assertEqual(len(self.connection.event_subscriptions), 0)

class TestBridgeManager(unittest.TestCase):
    """Test cases for the BridgeManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = BridgeManager()
        self.session_id = "test_session"
    
    def test_init(self):
        """Test initialization of BridgeManager."""
        self.assertEqual(self.manager.connections, {})
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    async def test_create_connection_success(self, mock_connect):
        """Test successful connection creation."""
        # Mock connection to succeed
        mock_connect.return_value = True
        
        # Create connection
        connection = await self.manager.create_connection(self.session_id)
        
        # Check connection is created and stored
        self.assertIsInstance(connection, BridgeConnection)
        self.assertEqual(connection.session_id, self.session_id)
        self.assertIn(self.session_id, self.manager.connections)
        self.assertEqual(self.manager.connections[self.session_id], connection)
        
        # Check connect was called
        mock_connect.assert_called_once()
        
        # Close connection
        await self.manager.close_connection(self.session_id)
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    async def test_create_connection_failure(self, mock_connect):
        """Test connection creation failure."""
        # Mock connection to fail
        mock_connect.return_value = False
        
        # Create connection
        connection = await self.manager.create_connection(self.session_id)
        
        # Check connection is not created or stored
        self.assertIsNone(connection)
        self.assertNotIn(self.session_id, self.manager.connections)
        
        # Check connect was called
        mock_connect.assert_called_once()
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    async def test_get_connection(self, mock_connect):
        """Test get_connection method."""
        # Mock connection to succeed
        mock_connect.return_value = True
        
        # Create connection
        await self.manager.create_connection(self.session_id)
        
        # Get connection
        connection = await self.manager.get_connection(self.session_id)
        
        # Check connection is retrieved
        self.assertIsInstance(connection, BridgeConnection)
        self.assertEqual(connection.session_id, self.session_id)
        
        # Close connection
        await self.manager.close_connection(self.session_id)
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    @patch('agent.bridge.bridge.BridgeConnection.disconnect', new_callable=AsyncMock)
    async def test_close_connection(self, mock_disconnect, mock_connect):
        """Test close_connection method."""
        # Mock connection to succeed
        mock_connect.return_value = True
        mock_disconnect.return_value = True
        
        # Create connection
        await self.manager.create_connection(self.session_id)
        
        # Close connection
        result = await self.manager.close_connection(self.session_id)
        
        # Check disconnect was called
        mock_disconnect.assert_called_once()
        
        # Check connection is closed and removed
        self.assertTrue(result)
        self.assertNotIn(self.session_id, self.manager.connections)
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    @patch('agent.bridge.bridge.BridgeConnection.disconnect', new_callable=AsyncMock)
    async def test_close_all_connections(self, mock_disconnect, mock_connect):
        """Test close_all_connections method."""
        # Mock connection to succeed
        mock_connect.return_value = True
        mock_disconnect.return_value = True
        
        # Create multiple connections
        await self.manager.create_connection("session1")
        await self.manager.create_connection("session2")
        
        # Close all connections
        await self.manager.close_all_connections()
        
        # Check disconnect was called twice
        self.assertEqual(mock_disconnect.call_count, 2)
        
        # Check all connections are closed and removed
        self.assertEqual(self.manager.connections, {})

class TestBridgeFunctions(unittest.TestCase):
    """Test cases for the bridge module functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear bridge manager connections
        bridge_manager.connections = {}
        self.session_id = "test_session"
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    async def test_initialize_bridge(self, mock_connect):
        """Test initialize_bridge function."""
        # Mock connection to succeed
        mock_connect.return_value = True
        
        # Initialize bridge
        connection = await initialize_bridge(self.session_id)
        
        # Check connection is created
        self.assertIsInstance(connection, BridgeConnection)
        self.assertEqual(connection.session_id, self.session_id)
        
        # Check connect was called
        mock_connect.assert_called_once()
        
        # Close connection
        await close_bridge(self.session_id)
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    @patch('agent.bridge.bridge.BridgeConnection.disconnect', new_callable=AsyncMock)
    async def test_close_bridge(self, mock_disconnect, mock_connect):
        """Test close_bridge function."""
        # Mock connection to succeed
        mock_connect.return_value = True
        mock_disconnect.return_value = True
        
        # Initialize bridge
        await initialize_bridge(self.session_id)
        
        # Close bridge
        result = await close_bridge(self.session_id)
        
        # Check disconnect was called
        mock_disconnect.assert_called_once()
        
        # Check connection is closed
        self.assertTrue(result)
        
        # Check get_bridge returns None
        connection = await get_bridge(self.session_id)
        self.assertIsNone(connection)
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    async def test_get_bridge(self, mock_connect):
        """Test get_bridge function."""
        # Mock connection to succeed
        mock_connect.return_value = True
        
        # Initialize bridge
        await initialize_bridge(self.session_id)
        
        # Get bridge
        connection = await get_bridge(self.session_id)
        
        # Check connection is retrieved
        self.assertIsInstance(connection, BridgeConnection)
        self.assertEqual(connection.session_id, self.session_id)
        
        # Close connection
        await close_bridge(self.session_id)
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    @patch('agent.bridge.bridge.BridgeConnection.send_message', new_callable=AsyncMock)
    async def test_send_event(self, mock_send_message, mock_connect):
        """Test send_event function."""
        # Mock connection to succeed
        mock_connect.return_value = True
        mock_send_message.return_value = True
        
        # Initialize bridge
        await initialize_bridge(self.session_id)
        
        # Send event
        result = await send_event(self.session_id, "test_event", {"key": "value"})
        
        # Check send_message was called
        mock_send_message.assert_called_once_with("test_event", {"key": "value"})
        
        # Check result is True
        self.assertTrue(result)
        
        # Close connection
        await close_bridge(self.session_id)
    
    @patch('agent.bridge.bridge.BridgeConnection.connect', new_callable=AsyncMock)
    @patch('agent.bridge.bridge.BridgeConnection.send_message', new_callable=AsyncMock)
    async def test_send_event_no_bridge(self, mock_send_message, mock_connect):
        """Test send_event function with no bridge."""
        # Don't initialize bridge
        
        # Send event
        result = await send_event(self.session_id, "test_event", {"key": "value"})
        
        # Check send_message was not called
        mock_send_message.assert_not_called()
        
        # Check result is False
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
