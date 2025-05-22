"""
Tool Call Agent Module for OpenManusEnhanced

This module provides the ToolCallAgent class which extends the base agent
with tool calling capabilities.
"""

import json
import time
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .base import BaseTool, AgentState, event_emitter

class ToolCollection:
    """
    Collection of tools available to the agent.
    
    This class manages the tools available to the agent and provides
    methods for registering and retrieving tools.
    """
    
    def __init__(self):
        """Initialize the tool collection."""
        self._tools = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool with the collection.
        
        Args:
            tool: Tool to register
        """
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool if found, None otherwise
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            List of all registered tools
        """
        return list(self._tools.values())
    
    def get_tool_descriptions(self) -> List[Dict[str, str]]:
        """
        Get descriptions of all registered tools.
        
        Returns:
            List of tool descriptions
        """
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self._tools.values()
        ]

class ToolCallAgent:
    """
    Agent with tool calling capabilities.
    
    This class extends the base agent with the ability to call tools
    and process their results.
    """
    
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        """
        Initialize the tool call agent.
        
        Args:
            tools: List of tools to register
        """
        self.state = AgentState.IDLE
        self.tool_collection = ToolCollection()
        
        # Register tools if provided
        if tools:
            for tool in tools:
                self.tool_collection.register_tool(tool)
        
        # Subscribe to events
        self._event_subscriptions = []
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool with the agent.
        
        Args:
            tool: Tool to register
        """
        self.tool_collection.register_tool(tool)
        
        # Emit tool registration event
        event_emitter.emit("tool_registered", {
            "tool_name": tool.name,
            "tool_description": tool.description
        })
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call a tool by name.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
        """
        # Update agent state
        self._set_state(AgentState.EXECUTING)
        
        # Get the tool
        tool = self.tool_collection.get_tool(tool_name)
        if not tool:
            self._set_state(AgentState.ERROR)
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Emit tool call event
        event_emitter.emit("tool_call", {
            "tool_name": tool_name,
            "arguments": kwargs
        })
        
        try:
            # Execute the tool
            start_time = time.time()
            result = tool.execute(**kwargs)
            execution_time = time.time() - start_time
            
            # Emit tool result event
            event_emitter.emit("tool_result", {
                "tool_name": tool_name,
                "result": result,
                "execution_time": execution_time
            })
            
            # Update agent state
            self._set_state(AgentState.IDLE)
            
            return result
        except Exception as e:
            # Update agent state
            self._set_state(AgentState.ERROR)
            
            # Emit tool error event
            event_emitter.emit("tool_error", {
                "tool_name": tool_name,
                "error": str(e)
            })
            
            # Re-raise the exception
            raise
    
    def _set_state(self, state: AgentState) -> None:
        """
        Set the agent state.
        
        Args:
            state: New agent state
        """
        old_state = self.state
        self.state = state
        
        # Emit state change event
        event_emitter.emit("state_change", {
            "old_state": old_state,
            "new_state": state
        })

# Export all classes
__all__ = [
    'ToolCollection',
    'ToolCallAgent'
]
