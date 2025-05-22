"""
Base Agent Module for OpenManusEnhanced

This module provides the base classes and utilities for the agent system.
"""

import abc
import enum
import json
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, model_validator

# Define agent states as an enum
class AgentState(str, enum.Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    TERMINATED = "terminated"  # Added missing TERMINATED state

# Event emitter for agent events
class EventEmitter:
    """
    Event emitter for agent events.
    
    This class provides a simple event system for the agent to emit events
    that can be subscribed to by other components.
    """
    
    def __init__(self):
        """Initialize the event emitter."""
        self._subscribers = {}
    
    def subscribe(self, event_type: str, callback: Callable) -> str:
        """
        Subscribe to an event.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is emitted
            
        Returns:
            Subscription ID
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = {}
        
        subscription_id = str(uuid.uuid4())
        self._subscribers[event_type][subscription_id] = callback
        
        return subscription_id
    
    def unsubscribe(self, event_type: str, subscription_id: str) -> bool:
        """
        Unsubscribe from an event.
        
        Args:
            event_type: Type of event to unsubscribe from
            subscription_id: Subscription ID to unsubscribe
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        if event_type not in self._subscribers:
            return False
        
        if subscription_id not in self._subscribers[event_type]:
            return False
        
        del self._subscribers[event_type][subscription_id]
        return True
    
    def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emit an event.
        
        Args:
            event_type: Type of event to emit
            data: Event data
        """
        if event_type not in self._subscribers:
            return
        
        # Add event metadata
        event_data = data.copy()  # Create a copy to avoid modifying the original
        
        # Call all subscribers
        for callback in self._subscribers[event_type].values():
            callback(event_data)

# Create a global event emitter instance
event_emitter = EventEmitter()

# Base tool class
class BaseTool(abc.ABC):
    """
    Base class for all tools.
    
    This class defines the interface for all tools used by the agent.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
    
    @abc.abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tool execution result
        """
        raise NotImplementedError("Tool must implement execute method")

# Export all classes and functions
__all__ = [
    'AgentState',
    'EventEmitter',
    'event_emitter',
    'BaseTool'
]
