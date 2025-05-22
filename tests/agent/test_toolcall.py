"""
Unit Tests for Tool Call Module

This module contains unit tests for the tool call agent module.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Now import the modules
from agent.core.base import BaseTool, AgentState, event_emitter
from agent.core.toolcall import ToolCallAgent, ToolCollection

class MockTool(BaseTool):
    """Mock implementation of BaseTool for testing."""
    
    def execute(self, *args, **kwargs):
        """Mock implementation of execute method."""
        return {"status": "success", "args": args, "kwargs": kwargs}

class TestToolCollection(unittest.TestCase):
    """Test cases for the ToolCollection class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool_collection = ToolCollection()
        self.mock_tool = MockTool(name="mock_tool", description="Mock tool for testing")
    
    def test_register_tool(self):
        """Test registering a tool."""
        self.tool_collection.register_tool(self.mock_tool)
        self.assertIn("mock_tool", self.tool_collection._tools)
    
    def test_get_tool(self):
        """Test getting a tool by name."""
        self.tool_collection.register_tool(self.mock_tool)
        tool = self.tool_collection.get_tool("mock_tool")
        self.assertEqual(tool, self.mock_tool)
    
    def test_get_nonexistent_tool(self):
        """Test getting a nonexistent tool."""
        tool = self.tool_collection.get_tool("nonexistent_tool")
        self.assertIsNone(tool)
    
    def test_get_all_tools(self):
        """Test getting all tools."""
        self.tool_collection.register_tool(self.mock_tool)
        tools = self.tool_collection.get_all_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0], self.mock_tool)
    
    def test_get_tool_descriptions(self):
        """Test getting tool descriptions."""
        self.tool_collection.register_tool(self.mock_tool)
        descriptions = self.tool_collection.get_tool_descriptions()
        self.assertEqual(len(descriptions), 1)
        self.assertEqual(descriptions[0]["name"], "mock_tool")
        self.assertEqual(descriptions[0]["description"], "Mock tool for testing")

class TestToolCallAgent(unittest.TestCase):
    """Test cases for the ToolCallAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear event emitter subscribers
        event_emitter._subscribers = {}
        
        # Create mock tool
        self.mock_tool = MockTool(name="mock_tool", description="Mock tool for testing")
        
        # Create agent with mock tool
        self.agent = ToolCallAgent(tools=[self.mock_tool])
        
        # Create event listener
        self.event_listener = MagicMock()
    
    def test_init(self):
        """Test initialization of ToolCallAgent."""
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertIsInstance(self.agent.tool_collection, ToolCollection)
        self.assertIn("mock_tool", self.agent.tool_collection._tools)
    
    def test_register_tool(self):
        """Test registering a tool with the agent."""
        # Subscribe to tool registration event
        event_emitter.subscribe("tool_registered", self.event_listener)
        
        # Register a new tool
        new_tool = MockTool(name="new_tool", description="New tool for testing")
        self.agent.register_tool(new_tool)
        
        # Check that tool was registered
        self.assertIn("new_tool", self.agent.tool_collection._tools)
        
        # Check that event was emitted
        self.event_listener.assert_called_once()
        args, _ = self.event_listener.call_args
        self.assertEqual(args[0]["tool_name"], "new_tool")
    
    def test_call_tool(self):
        """Test calling a tool."""
        # Subscribe to events
        event_emitter.subscribe("tool_call", self.event_listener)
        event_emitter.subscribe("tool_result", self.event_listener)
        event_emitter.subscribe("state_change", self.event_listener)
        
        # Call the tool
        result = self.agent.call_tool("mock_tool", arg1="value1", arg2="value2")
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["kwargs"]["arg1"], "value1")
        self.assertEqual(result["kwargs"]["arg2"], "value2")
        
        # Check that events were emitted (4 events: state_change to EXECUTING, tool_call, tool_result, state_change to IDLE)
        self.assertEqual(self.event_listener.call_count, 4)
        
        # Check final state
        self.assertEqual(self.agent.state, AgentState.IDLE)
    
    def test_call_nonexistent_tool(self):
        """Test calling a nonexistent tool."""
        # Subscribe to state change event
        event_emitter.subscribe("state_change", self.event_listener)
        
        # Call nonexistent tool
        with self.assertRaises(ValueError):
            self.agent.call_tool("nonexistent_tool")
        
        # Check that state changed to ERROR
        self.assertEqual(self.agent.state, AgentState.ERROR)
        
        # Check that events were emitted (2 state changes: IDLE->EXECUTING, EXECUTING->ERROR)
        self.assertEqual(self.event_listener.call_count, 2)

if __name__ == "__main__":
    unittest.main()
