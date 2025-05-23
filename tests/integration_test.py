"""
Integration Test Script for OpenManusEnhanced

This script sets up a test environment to validate the integration
between the backend WebSocket bridge and frontend visualization components.
"""

import os
import sys
import asyncio
import json
import time
from threading import Thread

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.core.manus import ManusAgent
from agent.bridge.bridge import BridgeConnection
from agent.core.tools.basic import TerminateTool, AskHumanTool, FileReadTool, ShellExecuteTool, BrowserNavigateTool
from agent.core.base import event_emitter

# Configuration
WS_URL = "ws://localhost:3001/agent"
TEST_SESSION_ID = "test-session-" + str(int(time.time()))

# Create aliases for expected tool names
ShellTool = ShellExecuteTool
BrowserTool = BrowserNavigateTool
EchoTool = AskHumanTool  # Using AskHumanTool as a substitute for EchoTool

class IntegrationTestServer:
    """Test server that simulates the backend for integration testing"""
    
    def __init__(self):
        self.bridge = BridgeConnection(session_id=TEST_SESSION_ID)
        self.agent = ManusAgent(name="TestAgent")
        self.running = False
        
        # Register tools
        self.agent.register_tool(EchoTool())
        self.agent.register_tool(ShellTool())
        self.agent.register_tool(BrowserTool())
        
        # Connect agent to bridge using event_emitter instead of direct agent.on method
        event_emitter.subscribe("tool:start", self._on_tool_start)
        event_emitter.subscribe("tool:completed", self._on_tool_end)
        event_emitter.subscribe("agent:state_change", self._on_state_change)
        
    async def start(self):
        """Start the integration test server"""
        print(f"Starting integration test server with session ID {TEST_SESSION_ID}")
        self.running = True
        
        # Connect to WebSocket server
        connected = await self.bridge.connect(WS_URL)
        if not connected:
            print("Failed to connect to WebSocket server. Is the backend running?")
            return
        
        # Send initial connection message
        await self.bridge.send_message("connection_established", {
            "session_id": TEST_SESSION_ID,
            "timestamp": time.time()
        })
        
        # Simulate agent activities
        await self._run_test_sequence()
    
    async def stop(self):
        """Stop the integration test server"""
        print("Stopping integration test server")
        self.running = False
        await self.bridge.disconnect()
    
    async def _run_test_sequence(self):
        """Run a sequence of test events to validate integration"""
        # Wait for frontend to connect
        await asyncio.sleep(2)
        
        # Simulate agent state changes
        print("Simulating agent state changes...")
        states = ["THINKING", "WORKING", "WAITING", "IDLE"]
        for state in states:
            self.agent.set_state(state)
            await asyncio.sleep(2)
        
        # Simulate browser visualization
        print("Simulating browser visualization...")
        await self.bridge.send_message("visualization_event", {
            "type": "visualization:browser_update",
            "url": "https://example.com",
            "content": "<html><body><h1>Example Website</h1><p>This is test content</p></body></html>",
            "timestamp": time.time()
        })
        await asyncio.sleep(2)
        
        # Simulate terminal visualization
        print("Simulating terminal visualization...")
        terminal_commands = [
            "$ ls -la",
            "total 20",
            "drwxr-xr-x 4 user user 4096 May 23 12:34 .",
            "drwxr-xr-x 3 user user 4096 May 23 12:30 ..",
            "$ echo 'Hello, world!'",
            "Hello, world!"
        ]
        
        for cmd in terminal_commands:
            await self.bridge.send_message("visualization_event", {
                "type": "visualization:terminal_update",
                "content": cmd,
                "timestamp": time.time()
            })
            await asyncio.sleep(0.5)
        
        # Simulate tool usage
        print("Simulating tool usage...")
        tools = [
            {"name": "browser_navigate", "status": "running"},
            {"name": "browser_navigate", "status": "completed", "result": {"success": True}},
            {"name": "shell_execute", "status": "running"},
            {"name": "shell_execute", "status": "completed", "result": {"output": "Command executed successfully"}},
            {"name": "file_read", "status": "running"},
            {"name": "file_read", "status": "completed", "result": {"content": "File content here"}}
        ]
        
        for tool in tools:
            await self.bridge.send_message("tool_event", {
                "tool_name": tool["name"],
                "status": tool["status"],
                "timestamp": time.time(),
                "result": tool.get("result")
            })
            await asyncio.sleep(2)
        
        print("Test sequence completed")
    
    def _on_tool_start(self, event_data):
        """Handle tool start events from agent"""
        tool_name = event_data.get("tool_name")
        args = event_data.get("args", {})
        asyncio.create_task(self.bridge.send_message("tool_event", {
            "tool_name": tool_name,
            "status": "running",
            "args": args,
            "timestamp": time.time()
        }))
    
    def _on_tool_end(self, event_data):
        """Handle tool end events from agent"""
        tool_name = event_data.get("tool_name")
        result = event_data.get("result", {})
        asyncio.create_task(self.bridge.send_message("tool_event", {
            "tool_name": tool_name,
            "status": "completed",
            "result": result,
            "timestamp": time.time()
        }))
    
    def _on_state_change(self, event_data):
        """Handle agent state change events"""
        old_state = event_data.get("old_state")
        new_state = event_data.get("new_state")
        asyncio.create_task(self.bridge.send_message("agent_event", {
            "old_state": old_state,
            "new_state": new_state,
            "timestamp": time.time()
        }))

def run_integration_test():
    """Run the integration test"""
    server = IntegrationTestServer()
    
    async def main():
        try:
            await server.start()
            # Keep server running for manual testing
            while server.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Integration test interrupted")
        finally:
            await server.stop()
    
    # Run the event loop
    asyncio.run(main())

if __name__ == "__main__":
    print(f"Starting OpenManusEnhanced integration test with session ID: {TEST_SESSION_ID}")
    print(f"Use this session ID in the frontend to connect to the test server")
    run_integration_test()
