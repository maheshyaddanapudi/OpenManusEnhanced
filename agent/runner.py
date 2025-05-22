"""
Agent Runner Module for OpenManusEnhanced

This module provides the entry point for running the agent.
It handles command-line arguments, initializes the agent, and
manages the WebSocket connection to the Node.js backend.
"""

import argparse
import asyncio
import json
import os
import sys
import uuid
from typing import Dict, Any, Optional

from agent.core.manus import ManusAgent
from agent.bridge.bridge import initialize_bridge, close_bridge, send_event

async def run_agent(session_id: str, system_prompt: str, port: int = 3001) -> None:
    """
    Run the agent with the given session ID and system prompt.
    
    Args:
        session_id: Session ID for the agent
        system_prompt: System prompt for the agent
        port: WebSocket port for communication with Node.js backend
    """
    # Initialize agent
    agent = ManusAgent(
        session_id=session_id,
        system_prompt=system_prompt,
        workspace_directory=os.path.join(os.getcwd(), 'workspace', session_id)
    )
    
    # Initialize bridge
    bridge = await initialize_bridge(session_id, f"ws://localhost:{port}/agent/{session_id}")
    
    try:
        # Send initialization event
        await send_event(session_id, "agent_initialized", {
            "agent_id": session_id,
            "timestamp": agent.created_at.isoformat()
        })
        
        # Wait for commands
        while True:
            # This is a placeholder - in a real implementation, this would
            # wait for commands from the Node.js backend via the bridge
            
            # For now, we'll just sleep
            await asyncio.sleep(1)
    finally:
        # Clean up
        agent.cleanup()
        await close_bridge(session_id)

def parse_args() -> Dict[str, Any]:
    """
    Parse command-line arguments.
    
    Returns:
        Dictionary of parsed arguments
    """
    parser = argparse.ArgumentParser(description='Run the OpenManusEnhanced agent')
    
    parser.add_argument('--session-id', type=str, default=str(uuid.uuid4()),
                        help='Session ID for the agent')
    parser.add_argument('--system-prompt', type=str, default='',
                        help='System prompt for the agent')
    parser.add_argument('--port', type=int, default=3001,
                        help='WebSocket port for communication with Node.js backend')
    
    return vars(parser.parse_args())

async def main() -> None:
    """
    Main entry point for the agent runner.
    """
    # Parse command-line arguments
    args = parse_args()
    
    # Run agent
    await run_agent(
        session_id=args['session_id'],
        system_prompt=args['system_prompt'],
        port=args['port']
    )

if __name__ == '__main__':
    # Run main function
    asyncio.run(main())
