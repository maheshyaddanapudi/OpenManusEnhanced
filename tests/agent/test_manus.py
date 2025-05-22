"""
Unit Tests for Manus Agent Module

This module contains unit tests for the Manus agent module.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch

from agent.core.manus import ManusAgent
from agent.core.base import AgentState, event_emitter

class TestManusAgent(unittest.TestCase):
    """Test cases for the ManusAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear event emitter subscriptions
        event_emitter._subscribers = {}
        
        # Create agent
        self.agent = ManusAgent(
            name="test_manus",
            description="Test Manus agent",
            workspace_directory="/test/workspace"
        )
    
    def test_init(self):
        """Test initialization of ManusAgent."""
        self.assertEqual(self.agent.name, "Manus")
        self.assertEqual(self.agent.description, "A versatile agent that can solve various tasks using multiple tools with real-time visualization")
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertIsNotNone(self.agent.session_id)
        self.assertIsNotNone(self.agent.created_at)
        self.assertIsNotNone(self.agent.browser_context)
        self.assertEqual(self.agent.browser_context["current_url"], None)
        self.assertEqual(self.agent.browser_context["history"], [])
    
    def test_register_manus_event_handlers(self):
        """Test registration of Manus-specific event handlers."""
        # Check that event handlers are registered
        event_types = [sub[0] for sub in self.agent._event_subscriptions]
        self.assertIn("browser:navigation", event_types)
        self.assertIn("human:interaction", event_types)
    
    def test_on_browser_navigation(self):
        """Test browser navigation event handler."""
        # Mock emit method
        with patch('agent.core.base.event_emitter.emit') as mock_emit:
            # Call handler with test data
            self.agent._on_browser_navigation({
                "url": "https://example.com",
                "timestamp": "2025-05-22T12:00:00Z"
            })
            
            # Check browser context is updated
            self.assertEqual(self.agent.browser_context["current_url"], "https://example.com")
            self.assertEqual(self.agent.browser_context["history"], ["https://example.com"])
            
            # Check visualization event is emitted
            mock_emit.assert_called_once()
            args = mock_emit.call_args[0]
            self.assertEqual(args[0], "visualization:browser_update")
            self.assertEqual(args[1]["agent_id"], self.agent.session_id)
            self.assertEqual(args[1]["url"], "https://example.com")
    
    def test_on_human_interaction_takeover(self):
        """Test human interaction event handler for takeover."""
        # Mock take_human_control method
        self.agent.take_human_control = MagicMock()
        
        # Call handler with takeover data
        self.agent._on_human_interaction({
            "type": "takeover"
        })
        
        # Check take_human_control is called
        self.agent.take_human_control.assert_called_once()
    
    def test_on_human_interaction_release(self):
        """Test human interaction event handler for release."""
        # Mock release_human_control method
        self.agent.release_human_control = MagicMock()
        
        # Call handler with release data
        self.agent._on_human_interaction({
            "type": "release"
        })
        
        # Check release_human_control is called
        self.agent.release_human_control.assert_called_once()
    
    def test_on_human_interaction_message(self):
        """Test human interaction event handler for message."""
        # Mock memory.add_message method
        self.agent.memory.add_message = MagicMock()
        
        # Call handler with message data
        self.agent._on_human_interaction({
            "type": "message",
            "message": "Hello, agent!"
        })
        
        # Check memory.add_message is called
        self.agent.memory.add_message.assert_called_once_with("user", "Hello, agent!")
    
    @patch('agent.core.base.event_emitter.emit')
    async def test_think(self, mock_emit):
        """Test think method."""
        # Call think method
        result = await self.agent.think()
        
        # Check state is set to THINKING
        self.assertEqual(self.agent.state, AgentState.THINKING)
        
        # Check visualization event is emitted
        mock_emit.assert_called_once()
        args = mock_emit.call_args[0]
        self.assertEqual(args[0], "visualization:agent_thinking")
        self.assertEqual(args[1]["agent_id"], self.agent.session_id)
        
        # Check result is True (continue)
        self.assertTrue(result)
    
    @patch('agent.core.base.event_emitter.emit')
    async def test_execute_browser_action(self, mock_emit):
        """Test execute_browser_action method."""
        # Call execute_browser_action method
        result = await self.agent.execute_browser_action("navigate", url="https://example.com")
        
        # Check state is temporarily set to EXECUTING
        self.assertEqual(self.agent.state, AgentState.IDLE)  # Should be reset after execution
        
        # Check visualization event is emitted
        mock_emit.assert_called_once()
        args = mock_emit.call_args[0]
        self.assertEqual(args[0], "visualization:browser_action")
        self.assertEqual(args[1]["agent_id"], self.agent.session_id)
        self.assertEqual(args[1]["action"], "navigate")
        self.assertEqual(args[1]["parameters"], {"url": "https://example.com"})
        
        # Check browser context is updated
        self.assertEqual(self.agent.browser_context["current_url"], "https://example.com")
        self.assertEqual(self.agent.browser_context["history"], ["https://example.com"])
        
        # Check result is success
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action"], "navigate")
    
    @patch('agent.core.base.event_emitter.emit')
    def test_cleanup(self, mock_emit):
        """Test cleanup method."""
        # Add a mock event subscription
        self.agent._event_subscriptions.append(("test_event", "test_id"))
        
        # Call cleanup method
        self.agent.cleanup()
        
        # Check visualization event is emitted
        mock_emit.assert_called_once()
        args = mock_emit.call_args[0]
        self.assertEqual(args[0], "visualization:browser_close")
        self.assertEqual(args[1]["agent_id"], self.agent.session_id)

if __name__ == "__main__":
    unittest.main()
