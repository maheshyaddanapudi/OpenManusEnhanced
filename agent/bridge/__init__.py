"""
Bridge Module Initialization for OpenManusEnhanced

This module initializes the bridge package.
"""

from .bridge import (
    initialize_bridge,
    close_bridge,
    get_bridge,
    send_event,
    BridgeConnection,
    BridgeManager,
    bridge_manager
)

__all__ = [
    'initialize_bridge',
    'close_bridge',
    'get_bridge',
    'send_event',
    'BridgeConnection',
    'BridgeManager',
    'bridge_manager'
]
