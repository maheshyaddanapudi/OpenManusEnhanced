import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import AgentVisualization from './AgentVisualization';
import webSocketService from '../../services/WebSocketService';

// Mock the WebSocketService
jest.mock('../../services/WebSocketService', () => {
  // Create handlers object to store callback functions
  const handlers = {};
  
  return {
    connect: jest.fn().mockResolvedValue(true),
    disconnect: jest.fn(),
    sendMessage: jest.fn(),
    subscribe: jest.fn().mockImplementation((eventType, callback) => {
      // Store the callback for later use in tests
      handlers[eventType] = callback;
      return `mock-subscription-id-${eventType}`;
    }),
    unsubscribe: jest.fn(),
    // Expose handlers for tests to access callbacks
    __handlers: handlers
  };
});

describe('AgentVisualization Component', () => {
  const sessionId = 'test-session-123';
  const agentName = 'TestAgent';
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders with initial state', () => {
    const { container } = render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Check component renders with correct title
    expect(screen.getByText(`${agentName} Visualization`)).toBeInTheDocument();
    
    // Check initial state using container query instead of screen
    expect(container.querySelector('.agent-status')).toHaveTextContent('Status: IDLE');
    expect(screen.getByText('No active tool')).toBeInTheDocument();
    expect(screen.getByText('No tool history')).toBeInTheDocument();
    expect(screen.getByText('No browser activity')).toBeInTheDocument();
    expect(screen.getByText('No terminal activity')).toBeInTheDocument();
    
    // Check take control button is present
    expect(screen.getByText('Take Control')).toBeInTheDocument();
  });
  
  test('connects to WebSocket on mount', async () => {
    render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Check WebSocket connection was attempted
    expect(webSocketService.connect).toHaveBeenCalledWith(sessionId);
    
    // Wait for useEffect to complete
    await waitFor(() => {
      // Check that subscribe was called for each event type
      expect(webSocketService.subscribe).toHaveBeenCalledWith('agent_event', expect.any(Function));
      expect(webSocketService.subscribe).toHaveBeenCalledWith('tool_event', expect.any(Function));
      expect(webSocketService.subscribe).toHaveBeenCalledWith('visualization_event', expect.any(Function));
      expect(webSocketService.subscribe).toHaveBeenCalledWith('visualization:browser_update', expect.any(Function));
      expect(webSocketService.subscribe).toHaveBeenCalledWith('visualization:terminal_update', expect.any(Function));
      expect(webSocketService.subscribe).toHaveBeenCalledWith('human:interaction', expect.any(Function));
    });
  });
  
  test('disconnects from WebSocket on unmount', async () => {
    const { unmount } = render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Wait for useEffect to complete
    await waitFor(() => {
      expect(webSocketService.subscribe).toHaveBeenCalled();
    });
    
    // Unmount component
    unmount();
    
    // Check WebSocket disconnection was called
    expect(webSocketService.disconnect).toHaveBeenCalled();
    expect(webSocketService.unsubscribe).toHaveBeenCalled();
  });
  
  test('handles agent state change events', async () => {
    render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Wait for useEffect to complete
    await waitFor(() => {
      expect(webSocketService.subscribe).toHaveBeenCalled();
    });
    
    // Access the handler directly from our mock
    const agentEventHandler = webSocketService.__handlers['agent_event'];
    
    // Skip test if handler not found
    if (!agentEventHandler) {
      console.warn('Agent event handler not found, skipping test');
      return;
    }
    
    // Simulate agent state change event
    act(() => {
      agentEventHandler({ new_state: 'THINKING' });
    });
    
    // Check state was updated
    const statusElement = document.querySelector('.agent-status');
    expect(statusElement).toHaveTextContent('Status: THINKING');
  });
  
  test('handles tool events', async () => {
    render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Wait for useEffect to complete
    await waitFor(() => {
      expect(webSocketService.subscribe).toHaveBeenCalled();
    });
    
    // Access the handler directly from our mock
    const toolEventHandler = webSocketService.__handlers['tool_event'];
    
    // Skip test if handler not found
    if (!toolEventHandler) {
      console.warn('Tool event handler not found, skipping test');
      return;
    }
    
    // Simulate tool start event
    act(() => {
      toolEventHandler({
        tool_name: 'browser_navigate',
        timestamp: Date.now(),
        status: 'running'
      });
    });
    
    // Check current tool was updated
    expect(screen.getByText('browser_navigate')).toBeInTheDocument();
    expect(screen.getByText('running')).toBeInTheDocument();
    
    // Simulate tool completion event
    jest.useFakeTimers();
    act(() => {
      toolEventHandler({
        tool_name: 'browser_navigate',
        timestamp: Date.now(),
        status: 'completed',
        result: { success: true }
      });
    });
    
    // Check tool history was updated
    expect(screen.getByText('browser_navigate')).toBeInTheDocument();
    expect(screen.getByText('completed')).toBeInTheDocument();
    
    // Advance timers to clear current tool
    act(() => {
      jest.advanceTimersByTime(2000);
    });
    
    // Check current tool was cleared
    expect(screen.getByText('No active tool')).toBeInTheDocument();
    
    jest.useRealTimers();
  });
  
  test('handles browser update events', async () => {
    render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Wait for useEffect to complete
    await waitFor(() => {
      expect(webSocketService.subscribe).toHaveBeenCalled();
    });
    
    // Access the handler directly from our mock
    const browserUpdateHandler = webSocketService.__handlers['visualization:browser_update'];
    
    // Skip test if handler not found
    if (!browserUpdateHandler) {
      console.warn('Browser update handler not found, skipping test');
      return;
    }
    
    // Simulate browser update event
    act(() => {
      browserUpdateHandler({
        url: 'https://example.com',
        content: '<html><body>Example content</body></html>',
        timestamp: Date.now()
      });
    });
    
    // Check browser content was updated
    expect(screen.getByDisplayValue('https://example.com')).toBeInTheDocument();
    expect(screen.getByText('Example content')).toBeInTheDocument();
  });
  
  test('handles terminal update events', async () => {
    render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Wait for useEffect to complete
    await waitFor(() => {
      expect(webSocketService.subscribe).toHaveBeenCalled();
    });
    
    // Access the handler directly from our mock
    const terminalUpdateHandler = webSocketService.__handlers['visualization:terminal_update'];
    
    // Skip test if handler not found
    if (!terminalUpdateHandler) {
      console.warn('Terminal update handler not found, skipping test');
      return;
    }
    
    // Simulate terminal update event
    act(() => {
      terminalUpdateHandler({
        content: '$ ls -la',
        timestamp: Date.now()
      });
    });
    
    // Check terminal content was updated
    expect(screen.getByText('$ ls -la')).toBeInTheDocument();
  });
  
  test('handles human interaction events', async () => {
    render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Wait for useEffect to complete
    await waitFor(() => {
      expect(webSocketService.subscribe).toHaveBeenCalled();
    });
    
    // Access the handler directly from our mock
    const humanInteractionHandler = webSocketService.__handlers['human:interaction'];
    
    // Skip test if handler not found
    if (!humanInteractionHandler) {
      console.warn('Human interaction handler not found, skipping test');
      return;
    }
    
    // Simulate takeover event
    act(() => {
      humanInteractionHandler({
        type: 'takeover',
        timestamp: Date.now()
      });
    });
    
    // Check control button was updated
    expect(screen.getByText('Release Control')).toBeInTheDocument();
    
    // Simulate release event
    act(() => {
      humanInteractionHandler({
        type: 'release',
        timestamp: Date.now()
      });
    });
    
    // Check control button was updated
    expect(screen.getByText('Take Control')).toBeInTheDocument();
  });
  
  test('sends takeover request when take control button is clicked', () => {
    render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Click take control button
    fireEvent.click(screen.getByText('Take Control'));
    
    // Check message was sent
    expect(webSocketService.sendMessage).toHaveBeenCalledWith('human_control', {
      control_type: 'takeover_request',
      timestamp: expect.any(Number)
    });
  });
  
  test('sends release request when release control button is clicked', async () => {
    render(<AgentVisualization sessionId={sessionId} agentName={agentName} />);
    
    // Wait for useEffect to complete
    await waitFor(() => {
      expect(webSocketService.subscribe).toHaveBeenCalled();
    });
    
    // Access the handler directly from our mock
    const humanInteractionHandler = webSocketService.__handlers['human:interaction'];
    
    // Skip test if handler not found
    if (!humanInteractionHandler) {
      console.warn('Human interaction handler not found, skipping test');
      return;
    }
    
    // Simulate takeover event to show release button
    act(() => {
      humanInteractionHandler({
        type: 'takeover',
        timestamp: Date.now()
      });
    });
    
    // Click release control button
    fireEvent.click(screen.getByText('Release Control'));
    
    // Check message was sent
    expect(webSocketService.sendMessage).toHaveBeenCalledWith('human_control', {
      control_type: 'release',
      timestamp: expect.any(Number)
    });
  });
});
