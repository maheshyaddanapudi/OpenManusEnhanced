"""
Unit Tests for Bridge Module

This module contains unit tests for the bridge module.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch

from agent.bridge.bridge import (
    BridgeConnection,
    BridgeManager,
    bridge_manager,
    initialize_bridge,
    close_bridge,
    get_bridge,
    send_event
)

class TestBridgeConnection(unittest.TestCase):
    """Test cases for the BridgeConnection class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.session_id = "test_session"
        self.connection = BridgeConnection(self.session_id)
    
    def test_init(self):
        """Test initialization of BridgeConnection."""
        self.assertEqual(self.connection.session_id, self.session_id)
        self.assertFalse(self.connection.connected)
        self.assertIsNone(self.connection.socket)
        self.assertEqual(self.connection.event_subscriptions, [])
        self.assertFalse(self.connection.running)
    
    @patch('builtins.print')
    async def test_connect(self, mock_print):
        """Test connect method."""
        # Call connect method
        result = await self.connection.connect()
        
        # Check connection is established
        self.assertTrue(self.connection.connected)
        self.assertTrue(self.connection.running)
        
        # Check result is True
        self.assertTrue(result)
    
    async def test_disconnect(self):
        """Test disconnect method."""
        # First connect
        await self.connection.connect()
        
        # Then disconnect
        result = await self.connection.disconnect()
        
        # Check connection is closed
        self.assertFalse(self.connection.connected)
        self.assertFalse(self.connection.running)
        
        # Check result is True
        self.assertTrue(result)
    
    @patch('builtins.print')
    async def test_send_message(self, mock_print):
        """Test send_message method."""
        # First connect
        await self.connection.connect()
        
        # Send message
        result = await self.connection.send_message("test_type", {"key": "value"})
        
        # Check result is True
        self.assertTrue(result)
        
        # Check message is printed (simulating WebSocket send)
        mock_print.assert_called()
        
        # Disconnect
        await self.connection.disconnect()

class TestBridgeManager(unittest.TestCase):
    """Test cases for the BridgeManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = BridgeManager()
        self.session_id = "test_session"
    
    def test_init(self):
        """Test initialization of BridgeManager."""
        self.assertEqual(self.manager.connections, {})
    
    async def test_create_connection(self):
        """Test create_connection method."""
        # Create connection
        connection = await self.manager.create_connection(self.session_id)
        
        # Check connection is created and stored
        self.assertIsInstance(connection, BridgeConnection)
        self.assertEqual(connection.session_id, self.session_id)
        self.assertIn(self.session_id, self.manager.connections)
        self.assertEqual(self.manager.connections[self.session_id], connection)
        
        # Check connection is connected
        self.assertTrue(connection.connected)
        
        # Close connection
        await self.manager.close_connection(self.session_id)
    
    async def test_get_connection(self):
        """Test get_connection method."""
        # Create connection
        await self.manager.create_connection(self.session_id)
        
        # Get connection
        connection = await self.manager.get_connection(self.session_id)
        
        # Check connection is retrieved
        self.assertIsInstance(connection, BridgeConnection)
        self.assertEqual(connection.session_id, self.session_id)
        
        # Close connection
        await self.manager.close_connection(self.session_id)
    
    async def test_close_connection(self):
        """Test close_connection method."""
        # Create connection
        await self.manager.create_connection(self.session_id)
        
        # Close connection
        result = await self.manager.close_connection(self.session_id)
        
        # Check connection is closed and removed
        self.assertTrue(result)
        self.assertNotIn(self.session_id, self.manager.connections)
    
    async def test_close_all_connections(self):
        """Test close_all_connections method."""
        # Create multiple connections
        await self.manager.create_connection("session1")
        await self.manager.create_connection("session2")
        
        # Close all connections
        await self.manager.close_all_connections()
        
        # Check all connections are closed and removed
        self.assertEqual(self.manager.connections, {})

class TestBridgeFunctions(unittest.TestCase):
    """Test cases for the bridge module functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear bridge manager connections
        bridge_manager.connections = {}
        self.session_id = "test_session"
    
    async def test_initialize_bridge(self):
        """Test initialize_bridge function."""
        # Initialize bridge
        connection = await initialize_bridge(self.session_id)
        
        # Check connection is created
        self.assertIsInstance(connection, BridgeConnection)
        self.assertEqual(connection.session_id, self.session_id)
        self.assertTrue(connection.connected)
        
        # Close connection
        await close_bridge(self.session_id)
    
    async def test_close_bridge(self):
        """Test close_bridge function."""
        # Initialize bridge
        await initialize_bridge(self.session_id)
        
        # Close bridge
        result = await close_bridge(self.session_id)
        
        # Check connection is closed
        self.assertTrue(result)
        
        # Check get_bridge returns None
        connection = await get_bridge(self.session_id)
        self.assertIsNone(connection)
    
    async def test_get_bridge(self):
        """Test get_bridge function."""
        # Initialize bridge
        await initialize_bridge(self.session_id)
        
        # Get bridge
        connection = await get_bridge(self.session_id)
        
        # Check connection is retrieved
        self.assertIsInstance(connection, BridgeConnection)
        self.assertEqual(connection.session_id, self.session_id)
        
        # Close connection
        await close_bridge(self.session_id)
    
    @patch('builtins.print')
    async def test_send_event(self, mock_print):
        """Test send_event function."""
        # Initialize bridge
        await initialize_bridge(self.session_id)
        
        # Send event
        result = await send_event(self.session_id, "test_event", {"key": "value"})
        
        # Check result is True
        self.assertTrue(result)
        
        # Check message is printed (simulating WebSocket send)
        mock_print.assert_called()
        
        # Close connection
        await close_bridge(self.session_id)

if __name__ == "__main__":
    unittest.main()
