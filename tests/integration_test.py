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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.core.manus import ManusAgent
from agent.bridge.bridge import BridgeConnection
from agent.core.tools.basic import EchoTool, ShellTool, BrowserTool

# Configuration
WS_PORT = 8765
TEST_SESSION_ID = "test-session-" + str(int(time.time()))

class IntegrationTestServer:
    """Test server that simulates the backend for integration testing"""
    
    def __init__(self, port=WS_PORT):
        self.port = port
        self.bridge = BridgeConnection(port=port)
        self.agent = ManusAgent(name="TestAgent")
        self.running = False
        
        # Register tools
        self.agent.register_tool(EchoTool())
        self.agent.register_tool(ShellTool())
        self.agent.register_tool(BrowserTool())
        
        # Connect agent to bridge
        self.agent.on("tool_start", self._on_tool_start)
        self.agent.on("tool_end", self._on_tool_end)
        self.agent.on("state_change", self._on_state_change)
        
    async def start(self):
        """Start the integration test server"""
        print(f"Starting integration test server on port {self.port}")
        self.running = True
        
        # Start bridge in background
        await self.bridge.start()
        
        # Send initial connection message
        await self.bridge.send_message({
            "type": "connection_established",
            "session_id": TEST_SESSION_ID,
            "timestamp": time.time()
        })
        
        # Simulate agent activities
        await self._run_test_sequence()
    
    async def stop(self):
        """Stop the integration test server"""
        print("Stopping integration test server")
        self.running = False
        await self.bridge.stop()
    
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
        await self.bridge.send_message({
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
            await self.bridge.send_message({
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
            {"name": "shell_exec", "status": "running"},
            {"name": "shell_exec", "status": "completed", "result": {"output": "Command executed successfully"}},
            {"name": "file_read", "status": "running"},
            {"name": "file_read", "status": "completed", "result": {"content": "File content here"}}
        ]
        
        for tool in tools:
            await self.bridge.send_message({
                "type": "tool_event",
                "tool_name": tool["name"],
                "status": tool["status"],
                "timestamp": time.time(),
                "result": tool.get("result")
            })
            await asyncio.sleep(2)
        
        print("Test sequence completed")
    
    def _on_tool_start(self, tool_name, args):
        """Handle tool start events from agent"""
        asyncio.create_task(self.bridge.send_message({
            "type": "tool_event",
            "tool_name": tool_name,
            "status": "running",
            "args": args,
            "timestamp": time.time()
        }))
    
    def _on_tool_end(self, tool_name, result):
        """Handle tool end events from agent"""
        asyncio.create_task(self.bridge.send_message({
            "type": "tool_event",
            "tool_name": tool_name,
            "status": "completed",
            "result": result,
            "timestamp": time.time()
        }))
    
    def _on_state_change(self, old_state, new_state):
        """Handle agent state change events"""
        asyncio.create_task(self.bridge.send_message({
            "type": "agent_event",
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
