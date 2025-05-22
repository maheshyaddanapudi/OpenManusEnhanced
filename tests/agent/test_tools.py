"""
Unit Tests for Basic Tools Module

This module contains unit tests for the basic tools module.
"""

import unittest
from unittest.mock import MagicMock, patch

from agent.core.tools.basic import (
    TerminateTool,
    AskHumanTool,
    FileReadTool,
    FileWriteTool,
    ShellExecuteTool,
    BrowserNavigateTool,
    BrowserClickTool
)

class TestTerminateTool(unittest.TestCase):
    """Test cases for the TerminateTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = TerminateTool()
    
    def test_init(self):
        """Test initialization of TerminateTool."""
        self.assertEqual(self.tool.name, "terminate")
        self.assertEqual(self.tool.description, "Terminate the agent execution when the task is complete.")
    
    @patch('agent.core.base.event_emitter.emit')
    def test_execute(self, mock_emit):
        """Test execute method."""
        # Execute tool
        result = self.tool.execute(reason="Test termination")
        
        # Check event is emitted
        mock_emit.assert_called_once()
        args = mock_emit.call_args[0]
        self.assertEqual(args[0], "agent:terminate")
        self.assertEqual(args[1]["reason"], "Test termination")
        
        # Check result
        self.assertEqual(result["status"], "terminated")
        self.assertEqual(result["reason"], "Test termination")

class TestAskHumanTool(unittest.TestCase):
    """Test cases for the AskHumanTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = AskHumanTool()
    
    def test_init(self):
        """Test initialization of AskHumanTool."""
        self.assertEqual(self.tool.name, "ask_human")
        self.assertEqual(self.tool.description, "Ask the human for input when you need additional information.")
    
    @patch('agent.core.base.event_emitter.emit')
    def test_execute(self, mock_emit):
        """Test execute method."""
        # Execute tool
        result = self.tool.execute(question="What is your name?")
        
        # Check event is emitted
        mock_emit.assert_called_once()
        args = mock_emit.call_args[0]
        self.assertEqual(args[0], "human:ask")
        self.assertEqual(args[1]["question"], "What is your name?")
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertTrue("response" in result)

class TestFileReadTool(unittest.TestCase):
    """Test cases for the FileReadTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = FileReadTool()
    
    def test_init(self):
        """Test initialization of FileReadTool."""
        self.assertEqual(self.tool.name, "file_read")
        self.assertEqual(self.tool.description, "Read the contents of a file.")
    
    @patch('agent.core.base.event_emitter.emit')
    def test_execute(self, mock_emit):
        """Test execute method."""
        # Execute tool
        result = self.tool.execute(file_path="/test/file.txt", start_line=0, end_line=10)
        
        # Check events are emitted
        self.assertEqual(mock_emit.call_count, 2)
        
        # Check first event (start)
        args1 = mock_emit.call_args_list[0][0]
        self.assertEqual(args1[0], "file:read_start")
        self.assertEqual(args1[1]["file_path"], "/test/file.txt")
        self.assertEqual(args1[1]["start_line"], 0)
        self.assertEqual(args1[1]["end_line"], 10)
        
        # Check second event (success)
        args2 = mock_emit.call_args_list[1][0]
        self.assertEqual(args2[0], "file:read_success")
        self.assertEqual(args2[1]["file_path"], "/test/file.txt")
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertTrue("content" in result)

class TestFileWriteTool(unittest.TestCase):
    """Test cases for the FileWriteTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = FileWriteTool()
    
    def test_init(self):
        """Test initialization of FileWriteTool."""
        self.assertEqual(self.tool.name, "file_write")
        self.assertEqual(self.tool.description, "Write content to a file.")
    
    @patch('agent.core.base.event_emitter.emit')
    def test_execute(self, mock_emit):
        """Test execute method."""
        # Execute tool
        result = self.tool.execute(file_path="/test/file.txt", content="Test content", append=False)
        
        # Check events are emitted
        self.assertEqual(mock_emit.call_count, 2)
        
        # Check first event (start)
        args1 = mock_emit.call_args_list[0][0]
        self.assertEqual(args1[0], "file:write_start")
        self.assertEqual(args1[1]["file_path"], "/test/file.txt")
        self.assertEqual(args1[1]["content_length"], len("Test content"))
        self.assertEqual(args1[1]["append"], False)
        
        # Check second event (success)
        args2 = mock_emit.call_args_list[1][0]
        self.assertEqual(args2[0], "file:write_success")
        self.assertEqual(args2[1]["file_path"], "/test/file.txt")
        self.assertEqual(args2[1]["mode"], "write")
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["file_path"], "/test/file.txt")
        self.assertEqual(result["mode"], "write")
        self.assertEqual(result["bytes_written"], len("Test content"))

class TestShellExecuteTool(unittest.TestCase):
    """Test cases for the ShellExecuteTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = ShellExecuteTool()
    
    def test_init(self):
        """Test initialization of ShellExecuteTool."""
        self.assertEqual(self.tool.name, "shell_execute")
        self.assertEqual(self.tool.description, "Execute a shell command.")
    
    @patch('agent.core.base.event_emitter.emit')
    def test_execute(self, mock_emit):
        """Test execute method."""
        # Execute tool
        result = self.tool.execute(command="ls -la", working_dir="/test")
        
        # Check events are emitted
        self.assertEqual(mock_emit.call_count, 2)
        
        # Check first event (start)
        args1 = mock_emit.call_args_list[0][0]
        self.assertEqual(args1[0], "shell:execute_start")
        self.assertEqual(args1[1]["command"], "ls -la")
        self.assertEqual(args1[1]["working_dir"], "/test")
        
        # Check second event (success)
        args2 = mock_emit.call_args_list[1][0]
        self.assertEqual(args2[0], "shell:execute_success")
        self.assertEqual(args2[1]["command"], "ls -la")
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["command"], "ls -la")
        self.assertTrue("output" in result)
        self.assertEqual(result["exit_code"], 0)

class TestBrowserNavigateTool(unittest.TestCase):
    """Test cases for the BrowserNavigateTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = BrowserNavigateTool()
    
    def test_init(self):
        """Test initialization of BrowserNavigateTool."""
        self.assertEqual(self.tool.name, "browser_navigate")
        self.assertEqual(self.tool.description, "Navigate to a URL in the browser.")
    
    @patch('agent.core.base.event_emitter.emit')
    def test_execute(self, mock_emit):
        """Test execute method."""
        # Execute tool
        result = self.tool.execute(url="https://example.com")
        
        # Check events are emitted
        self.assertEqual(mock_emit.call_count, 2)
        
        # Check first event (start)
        args1 = mock_emit.call_args_list[0][0]
        self.assertEqual(args1[0], "browser:navigate_start")
        self.assertEqual(args1[1]["url"], "https://example.com")
        
        # Check second event (success)
        args2 = mock_emit.call_args_list[1][0]
        self.assertEqual(args2[0], "browser:navigate_success")
        self.assertEqual(args2[1]["url"], "https://example.com")
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["url"], "https://example.com")
        self.assertTrue("content" in result)

class TestBrowserClickTool(unittest.TestCase):
    """Test cases for the BrowserClickTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = BrowserClickTool()
    
    def test_init(self):
        """Test initialization of BrowserClickTool."""
        self.assertEqual(self.tool.name, "browser_click")
        self.assertEqual(self.tool.description, "Click an element in the browser.")
    
    @patch('agent.core.base.event_emitter.emit')
    def test_execute(self, mock_emit):
        """Test execute method."""
        # Execute tool
        result = self.tool.execute(selector="#submit-button")
        
        # Check events are emitted
        self.assertEqual(mock_emit.call_count, 2)
        
        # Check first event (start)
        args1 = mock_emit.call_args_list[0][0]
        self.assertEqual(args1[0], "browser:click_start")
        self.assertEqual(args1[1]["selector"], "#submit-button")
        
        # Check second event (success)
        args2 = mock_emit.call_args_list[1][0]
        self.assertEqual(args2[0], "browser:click_success")
        self.assertEqual(args2[1]["selector"], "#submit-button")
        
        # Check result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["selector"], "#submit-button")

if __name__ == "__main__":
    unittest.main()
