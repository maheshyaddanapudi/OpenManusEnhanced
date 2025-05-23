/**
 * WebSocketService Tests
 * 
 * This file contains unit tests for the WebSocketService that handles
 * real-time communication between the frontend and backend.
 */

import webSocketService from './WebSocketService';

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;
    this.readyState = 0; // CONNECTING
    this.sent = [];
    
    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = 1; // OPEN
      if (this.onopen) this.onopen({ target: this });
    }, 10);
  }
  
  send(data) {
    this.sent.push(data);
  }
  
  close() {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose({ code: 1000, reason: 'Normal closure', wasClean: true });
  }
  
  // Helper to simulate receiving a message
  receiveMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data });
    }
  }
  
  // Helper to simulate an error
  simulateError(error) {
    if (this.onerror) {
      this.onerror(error);
    }
  }
}

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket;

describe('WebSocketService', () => {
  const sessionId = 'test-session-123';
  
  beforeEach(() => {
    // Reset WebSocketService state
    webSocketService.socket = null;
    webSocketService.isConnected = false;
    webSocketService.reconnectAttempts = 0;
    webSocketService.eventHandlers = {};
    webSocketService.sessionId = null;
    
    // Spy on console methods
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.spyOn(console, 'warn').mockImplementation(() => {});
  });
  
  afterEach(() => {
    // Restore console methods
    console.log.mockRestore();
    console.error.mockRestore();
    console.warn.mockRestore();
  });
  
  test('connects to WebSocket server', async () => {
    const connectPromise = webSocketService.connect(sessionId);
    
    // Wait for connection to complete
    await connectPromise;
    
    // Check connection state
    expect(webSocketService.isConnected).toBe(true);
    expect(webSocketService.socket).not.toBeNull();
    expect(webSocketService.sessionId).toBe(sessionId);
    expect(webSocketService.reconnectAttempts).toBe(0);
    
    // Check WebSocket URL
    expect(webSocketService.socket.url).toContain(`ws://localhost:3001/frontend?session_id=${sessionId}`);
    
    // Check connection message was sent
    expect(webSocketService.socket.sent.length).toBe(1);
    const sentMessage = JSON.parse(webSocketService.socket.sent[0]);
    expect(sentMessage.type).toBe('connection');
    expect(sentMessage.data.status).toBe('connected');
  });
  
  test('disconnects from WebSocket server', async () => {
    // First connect
    await webSocketService.connect(sessionId);
    
    // Then disconnect
    webSocketService.disconnect();
    
    // Check connection state
    expect(webSocketService.isConnected).toBe(false);
    expect(webSocketService.socket).toBeNull();
  });
  
  test('sends messages when connected', async () => {
    // First connect
    await webSocketService.connect(sessionId);
    
    // Send message
    const result = webSocketService.sendMessage('test_type', { key: 'value' });
    
    // Check result
    expect(result).toBe(true);
    
    // Check message was sent
    expect(webSocketService.socket.sent.length).toBe(2); // Connection message + test message
    const sentMessage = JSON.parse(webSocketService.socket.sent[1]);
    expect(sentMessage.type).toBe('test_type');
    expect(sentMessage.data).toEqual({ key: 'value' });
    expect(sentMessage.session_id).toBe(sessionId);
  });
  
  test('does not send messages when disconnected', () => {
    // Don't connect
    
    // Try to send message
    const result = webSocketService.sendMessage('test_type', { key: 'value' });
    
    // Check result
    expect(result).toBe(false);
    
    // Check warning was logged
    expect(console.warn).toHaveBeenCalledWith('Cannot send message: WebSocket not connected');
  });
  
  test('handles incoming messages', async () => {
    // Create event handler mock
    const mockHandler = jest.fn();
    
    // Subscribe to event
    webSocketService.subscribe('test_event', mockHandler);
    
    // Connect
    await webSocketService.connect(sessionId);
    
    // Simulate receiving a message
    webSocketService.socket.receiveMessage(JSON.stringify({
      type: 'test_event',
      data: { key: 'value' },
      session_id: sessionId
    }));
    
    // Check handler was called
    expect(mockHandler).toHaveBeenCalledWith({ key: 'value' });
  });
  
  test('handles ping messages', async () => {
    // Connect
    await webSocketService.connect(sessionId);
    
    // Clear sent messages
    webSocketService.socket.sent = [];
    
    // Simulate receiving a ping message
    webSocketService.socket.receiveMessage(JSON.stringify({
      type: 'ping',
      data: {},
      session_id: sessionId
    }));
    
    // Check pong was sent
    expect(webSocketService.socket.sent.length).toBe(1);
    const sentMessage = JSON.parse(webSocketService.socket.sent[0]);
    expect(sentMessage.type).toBe('pong');
  });
  
  test('handles agent events', async () => {
    // Create event handler mock
    const mockHandler = jest.fn();
    
    // Subscribe to specific agent event
    webSocketService.subscribe('agent:state_change', mockHandler);
    
    // Connect
    await webSocketService.connect(sessionId);
    
    // Simulate receiving an agent event
    webSocketService.socket.receiveMessage(JSON.stringify({
      type: 'agent_event',
      data: {
        event_type: 'state_change',
        old_state: 'IDLE',
        new_state: 'THINKING'
      },
      session_id: sessionId
    }));
    
    // Check handler was called
    expect(mockHandler).toHaveBeenCalledWith({
      event_type: 'state_change',
      old_state: 'IDLE',
      new_state: 'THINKING'
    });
  });
  
  test('handles tool events', async () => {
    // Create event handler mock
    const mockHandler = jest.fn();
    
    // Subscribe to specific tool event
    webSocketService.subscribe('tool:browser_navigate:start', mockHandler);
    
    // Connect
    await webSocketService.connect(sessionId);
    
    // Simulate receiving a tool event
    webSocketService.socket.receiveMessage(JSON.stringify({
      type: 'tool_event',
      data: {
        tool_name: 'browser_navigate',
        event_type: 'start',
        url: 'https://example.com'
      },
      session_id: sessionId
    }));
    
    // Check handler was called
    expect(mockHandler).toHaveBeenCalledWith({
      tool_name: 'browser_navigate',
      event_type: 'start',
      url: 'https://example.com'
    });
  });
  
  test('handles visualization events', async () => {
    // Create event handler mock
    const mockHandler = jest.fn();
    
    // Subscribe to specific visualization event
    webSocketService.subscribe('visualization:browser_update', mockHandler);
    
    // Connect
    await webSocketService.connect(sessionId);
    
    // Simulate receiving a visualization event
    webSocketService.socket.receiveMessage(JSON.stringify({
      type: 'visualization_event',
      data: {
        visualization_type: 'browser_update',
        url: 'https://example.com',
        content: '<html><body>Example</body></html>'
      },
      session_id: sessionId
    }));
    
    // Check handler was called
    expect(mockHandler).toHaveBeenCalledWith({
      visualization_type: 'browser_update',
      url: 'https://example.com',
      content: '<html><body>Example</body></html>'
    });
  });
  
  test('subscribes and unsubscribes from events', () => {
    // Create event handler mock
    const mockHandler = jest.fn();
    
    // Subscribe to event
    const subscriptionId = webSocketService.subscribe('test_event', mockHandler);
    
    // Check subscription was created
    expect(webSocketService.eventHandlers['test_event']).toBeDefined();
    expect(webSocketService.eventHandlers['test_event'].length).toBe(1);
    expect(webSocketService.eventHandlers['test_event'][0].id).toBe(subscriptionId);
    expect(webSocketService.eventHandlers['test_event'][0].callback).toBe(mockHandler);
    
    // Unsubscribe from event
    const result = webSocketService.unsubscribe('test_event', subscriptionId);
    
    // Check unsubscription was successful
    expect(result).toBe(true);
    expect(webSocketService.eventHandlers['test_event'].length).toBe(0);
  });
  
  test('handles connection errors', async () => {
    // Mock WebSocket constructor to throw error
    const originalWebSocket = global.WebSocket;
    global.WebSocket = jest.fn().mockImplementation(() => {
      throw new Error('Connection failed');
    });
    
    // Try to connect
    try {
      await webSocketService.connect(sessionId);
      fail('Should have thrown an error');
    } catch (error) {
      // Check error was logged
      expect(console.error).toHaveBeenCalledWith('Error creating WebSocket:', expect.any(Error));
    }
    
    // Check connection state
    expect(webSocketService.isConnected).toBe(false);
    expect(webSocketService.socket).toBeNull();
    
    // Restore WebSocket
    global.WebSocket = originalWebSocket;
  });
  
  test('handles message parsing errors', async () => {
    // Connect
    await webSocketService.connect(sessionId);
    
    // Simulate receiving an invalid message
    webSocketService.socket.receiveMessage('invalid json');
    
    // Check error was logged
    expect(console.error).toHaveBeenCalledWith('Error parsing message:', expect.any(Error));
  });
});
