"""
Backend Services Module for OpenManusEnhanced

This module provides the core services for the backend server,
including agent management, session management, and event bus.
"""

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs').promises;
const WebSocket = require('ws');

/**
 * Agent Manager Service
 * 
 * Manages agent processes and communication with Python agents
 */
class AgentManager {
  constructor() {
    this.agents = new Map();
    this.connections = new Map();
    this.eventBus = null;
  }

  /**
   * Set the event bus for broadcasting events
   * @param {EventBus} eventBus - Event bus instance
   */
  setEventBus(eventBus) {
    this.eventBus = eventBus;
  }

  /**
   * Create a new agent for a session
   * @param {string} sessionId - Session ID
   * @param {Object} options - Agent options
   * @returns {Promise<Object>} - Agent info
   */
  async createAgent(sessionId, options = {}) {
    // Check if agent already exists
    if (this.agents.has(sessionId)) {
      throw new Error(`Agent already exists for session ${sessionId}`);
    }

    // Create agent process
    const agentProcess = spawn('python3.12', [
      path.join(__dirname, '../../agent/runner.py'),
      '--session-id', sessionId,
      '--system-prompt', options.systemPrompt || '',
      '--port', '3001' // WebSocket port
    ], {
      env: {
        ...process.env,
        PYTHONPATH: path.join(__dirname, '../..')
      }
    });

    // Store agent process
    this.agents.set(sessionId, {
      process: agentProcess,
      status: 'initializing',
      options
    });

    // Handle process events
    agentProcess.stdout.on('data', (data) => {
      console.log(`Agent ${sessionId} stdout: ${data}`);
      
      // Broadcast agent output event
      if (this.eventBus) {
        this.eventBus.publish(sessionId, {
          type: 'agent_output',
          data: {
            output: data.toString(),
            timestamp: new Date()
          }
        });
      }
    });

    agentProcess.stderr.on('data', (data) => {
      console.error(`Agent ${sessionId} stderr: ${data}`);
      
      // Broadcast agent error event
      if (this.eventBus) {
        this.eventBus.publish(sessionId, {
          type: 'agent_error',
          data: {
            error: data.toString(),
            timestamp: new Date()
          }
        });
      }
    });

    agentProcess.on('close', (code) => {
      console.log(`Agent ${sessionId} process exited with code ${code}`);
      
      // Update agent status
      const agent = this.agents.get(sessionId);
      if (agent) {
        agent.status = 'stopped';
      }
      
      // Broadcast agent stopped event
      if (this.eventBus) {
        this.eventBus.publish(sessionId, {
          type: 'agent_stopped',
          data: {
            exitCode: code,
            timestamp: new Date()
          }
        });
      }
    });

    // Wait for agent to initialize
    await new Promise((resolve, reject) => {
      // Set timeout for initialization
      const timeout = setTimeout(() => {
        reject(new Error('Agent initialization timed out'));
      }, 30000);

      // Set up WebSocket connection handler
      const handleConnection = (ws, req) => {
        const url = new URL(req.url, 'http://localhost');
        const pathParts = url.pathname.split('/');
        const connSessionId = pathParts[pathParts.length - 1];

        if (connSessionId === sessionId) {
          // Store connection
          this.connections.set(sessionId, ws);

          // Handle WebSocket messages
          ws.on('message', (message) => {
            try {
              const event = JSON.parse(message);
              
              // Handle agent events
              if (event.type === 'agent_initialized') {
                // Update agent status
                const agent = this.agents.get(sessionId);
                if (agent) {
                  agent.status = 'ready';
                }
                
                // Broadcast agent initialized event
                if (this.eventBus) {
                  this.eventBus.publish(sessionId, {
                    type: 'agent_initialized',
                    data: {
                      timestamp: new Date()
                    }
                  });
                }
                
                // Resolve promise
                clearTimeout(timeout);
                resolve();
              } else {
                // Forward other events to event bus
                if (this.eventBus) {
                  this.eventBus.publish(sessionId, event);
                }
              }
            } catch (error) {
              console.error('Error handling WebSocket message:', error);
            }
          });

          // Handle WebSocket close
          ws.on('close', () => {
            console.log(`WebSocket connection closed for session ${sessionId}`);
            this.connections.delete(sessionId);
          });

          // Handle WebSocket error
          ws.on('error', (error) => {
            console.error(`WebSocket error for session ${sessionId}:`, error);
          });
        }
      };

      // Add connection handler to global WebSocket server
      // Note: In a real implementation, this would be handled by a WebSocket server
      // For now, we'll just simulate it
      setTimeout(() => {
        // Simulate WebSocket connection
        const ws = {
          on: (event, handler) => {
            // Simulate event handlers
          },
          send: (data) => {
            // Simulate sending data
            console.log(`WebSocket send: ${data}`);
          }
        };
        
        // Store connection
        this.connections.set(sessionId, ws);
        
        // Update agent status
        const agent = this.agents.get(sessionId);
        if (agent) {
          agent.status = 'ready';
        }
        
        // Broadcast agent initialized event
        if (this.eventBus) {
          this.eventBus.publish(sessionId, {
            type: 'agent_initialized',
            data: {
              timestamp: new Date()
            }
          });
        }
        
        // Resolve promise
        clearTimeout(timeout);
        resolve();
      }, 1000);
    });

    return {
      sessionId,
      status: 'ready'
    };
  }

  /**
   * Start an agent
   * @param {string} sessionId - Session ID
   * @returns {Promise<void>}
   */
  async startAgent(sessionId) {
    // Check if agent exists
    const agent = this.agents.get(sessionId);
    if (!agent) {
      throw new Error(`Agent not found for session ${sessionId}`);
    }

    // Check if agent is ready
    if (agent.status !== 'ready' && agent.status !== 'stopped') {
      throw new Error(`Agent is not ready to start (status: ${agent.status})`);
    }

    // Get WebSocket connection
    const ws = this.connections.get(sessionId);
    if (!ws) {
      throw new Error(`WebSocket connection not found for session ${sessionId}`);
    }

    // Send start command
    ws.send(JSON.stringify({
      type: 'command',
      command: 'start'
    }));

    // Update agent status
    agent.status = 'running';

    // Broadcast agent started event
    if (this.eventBus) {
      this.eventBus.publish(sessionId, {
        type: 'agent_started',
        data: {
          timestamp: new Date()
        }
      });
    }
  }

  /**
   * Stop an agent
   * @param {string} sessionId - Session ID
   * @returns {Promise<void>}
   */
  async stopAgent(sessionId) {
    // Check if agent exists
    const agent = this.agents.get(sessionId);
    if (!agent) {
      throw new Error(`Agent not found for session ${sessionId}`);
    }

    // Get WebSocket connection
    const ws = this.connections.get(sessionId);
    if (ws) {
      // Send stop command
      ws.send(JSON.stringify({
        type: 'command',
        command: 'stop'
      }));
    }

    // Kill process if needed
    if (agent.process) {
      agent.process.kill();
    }

    // Update agent status
    agent.status = 'stopped';

    // Broadcast agent stopped event
    if (this.eventBus) {
      this.eventBus.publish(sessionId, {
        type: 'agent_stopped',
        data: {
          timestamp: new Date()
        }
      });
    }

    // Remove agent
    this.agents.delete(sessionId);
    this.connections.delete(sessionId);
  }

  /**
   * Send a message to an agent
   * @param {string} sessionId - Session ID
   * @param {Object} message - Message to send
   * @returns {Promise<void>}
   */
  async sendMessage(sessionId, message) {
    // Check if agent exists
    const agent = this.agents.get(sessionId);
    if (!agent) {
      throw new Error(`Agent not found for session ${sessionId}`);
    }

    // Get WebSocket connection
    const ws = this.connections.get(sessionId);
    if (!ws) {
      throw new Error(`WebSocket connection not found for session ${sessionId}`);
    }

    // Send message
    ws.send(JSON.stringify({
      type: 'message',
      message
    }));

    // Broadcast message sent event
    if (this.eventBus) {
      this.eventBus.publish(sessionId, {
        type: 'message_sent',
        data: {
          message,
          timestamp: new Date()
        }
      });
    }
  }

  /**
   * Take control of an agent
   * @param {string} sessionId - Session ID
   * @returns {Promise<void>}
   */
  async takeControl(sessionId) {
    // Check if agent exists
    const agent = this.agents.get(sessionId);
    if (!agent) {
      throw new Error(`Agent not found for session ${sessionId}`);
    }

    // Get WebSocket connection
    const ws = this.connections.get(sessionId);
    if (!ws) {
      throw new Error(`WebSocket connection not found for session ${sessionId}`);
    }

    // Send take control command
    ws.send(JSON.stringify({
      type: 'command',
      command: 'take_control'
    }));

    // Update agent status
    agent.status = 'human_control';

    // Broadcast control taken event
    if (this.eventBus) {
      this.eventBus.publish(sessionId, {
        type: 'control_taken',
        data: {
          timestamp: new Date()
        }
      });
    }
  }

  /**
   * Release control of an agent
   * @param {string} sessionId - Session ID
   * @returns {Promise<void>}
   */
  async releaseControl(sessionId) {
    // Check if agent exists
    const agent = this.agents.get(sessionId);
    if (!agent) {
      throw new Error(`Agent not found for session ${sessionId}`);
    }

    // Get WebSocket connection
    const ws = this.connections.get(sessionId);
    if (!ws) {
      throw new Error(`WebSocket connection not found for session ${sessionId}`);
    }

    // Send release control command
    ws.send(JSON.stringify({
      type: 'command',
      command: 'release_control'
    }));

    // Update agent status
    agent.status = 'running';

    // Broadcast control released event
    if (this.eventBus) {
      this.eventBus.publish(sessionId, {
        type: 'control_released',
        data: {
          timestamp: new Date()
        }
      });
    }
  }

  /**
   * Execute a tool as human
   * @param {string} sessionId - Session ID
   * @param {string} toolName - Tool name
   * @param {Object} args - Tool arguments
   * @returns {Promise<Object>} - Tool execution result
   */
  async executeHumanTool(sessionId, toolName, args) {
    // Check if agent exists
    const agent = this.agents.get(sessionId);
    if (!agent) {
      throw new Error(`Agent not found for session ${sessionId}`);
    }

    // Check if agent is in human control
    if (agent.status !== 'human_control') {
      throw new Error(`Agent must be in human control to execute tools (status: ${agent.status})`);
    }

    // Get WebSocket connection
    const ws = this.connections.get(sessionId);
    if (!ws) {
      throw new Error(`WebSocket connection not found for session ${sessionId}`);
    }

    // Generate tool execution ID
    const executionId = `tool_${Date.now()}`;

    // Send tool execution command
    ws.send(JSON.stringify({
      type: 'tool_execution',
      executionId,
      toolName,
      args
    }));

    // Wait for tool execution result
    return new Promise((resolve, reject) => {
      // Set timeout for tool execution
      const timeout = setTimeout(() => {
        reject(new Error('Tool execution timed out'));
      }, 30000);

      // Set up event handler
      const handleToolResult = (event) => {
        if (event.type === 'tool_execution_result' && event.executionId === executionId) {
          // Remove event handler
          this.eventBus.unsubscribeFromEvent(sessionId, 'tool_execution_result', handleToolResult);

          // Clear timeout
          clearTimeout(timeout);

          // Resolve or reject based on result
          if (event.error) {
            reject(new Error(event.error));
          } else {
            resolve(event.result);
          }
        }
      };

      // Subscribe to tool execution result event
      this.eventBus.subscribeToEvent(sessionId, 'tool_execution_result', handleToolResult);
    });
  }
}

/**
 * Session Manager Service
 * 
 * Manages agent sessions and messages
 */
class SessionManager {
  constructor() {
    this.sessions = new Map();
    this.messages = new Map();
    this.dataDir = path.join(__dirname, '../../database');
  }

  /**
   * Initialize the session manager
   * @returns {Promise<void>}
   */
  async initialize() {
    // Create data directory if it doesn't exist
    try {
      await fs.mkdir(this.dataDir, { recursive: true });
    } catch (error) {
      console.error('Error creating data directory:', error);
    }

    // Load sessions from disk
    try {
      const sessionsFile = path.join(this.dataDir, 'sessions.json');
      const sessionsData = await fs.readFile(sessionsFile, 'utf8');
      const sessions = JSON.parse(sessionsData);

      for (const session of sessions) {
        this.sessions.set(session.id, session);
      }
    } catch (error) {
      // Ignore if file doesn't exist
      if (error.code !== 'ENOENT') {
        console.error('Error loading sessions:', error);
      }
    }

    // Load messages from disk
    try {
      const messagesDir = path.join(this.dataDir, 'messages');
      await fs.mkdir(messagesDir, { recursive: true });

      const files = await fs.readdir(messagesDir);
      for (const file of files) {
        if (file.endsWith('.json')) {
          const sessionId = file.replace('.json', '');
          const messagesData = await fs.readFile(path.join(messagesDir, file), 'utf8');
          const messages = JSON.parse(messagesData);

          this.messages.set(sessionId, messages);
        }
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  }

  /**
   * Save sessions to disk
   * @returns {Promise<void>}
   */
  async saveSessions() {
    try {
      const sessionsFile = path.join(this.dataDir, 'sessions.json');
      const sessions = Array.from(this.sessions.values());
      await fs.writeFile(sessionsFile, JSON.stringify(sessions, null, 2));
    } catch (error) {
      console.error('Error saving sessions:', error);
    }
  }

  /**
   * Save messages for a session to disk
   * @param {string} sessionId - Session ID
   * @returns {Promise<void>}
   */
  async saveMessages(sessionId) {
    try {
      const messagesDir = path.join(this.dataDir, 'messages');
      await fs.mkdir(messagesDir, { recursive: true });

      const messagesFile = path.join(messagesDir, `${sessionId}.json`);
      const messages = this.messages.get(sessionId) || [];
      await fs.writeFile(messagesFile, JSON.stringify(messages, null, 2));
    } catch (error) {
      console.error(`Error saving messages for session ${sessionId}:`, error);
    }
  }

  /**
   * Create a new session
   * @param {Object} session - Session data
   * @returns {Promise<Object>} - Created session
   */
  async createSession(session) {
    // Store session
    this.sessions.set(session.id, session);
    this.messages.set(session.id, []);

    // Save to disk
    await this.saveSessions();

    return session;
  }

  /**
   * Get a session by ID
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} - Session data
   */
  async getSession(sessionId) {
    return this.sessions.get(sessionId);
  }

  /**
   * Get all sessions
   * @returns {Promise<Array<Object>>} - All sessions
   */
  async getAllSessions() {
    return Array.from(this.sessions.values());
  }

  /**
   * Update a session
   * @param {string} sessionId - Session ID
   * @param {Object} updates - Session updates
   * @returns {Promise<Object>} - Updated session
   */
  async updateSession(sessionId, updates) {
    // Get session
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }

    // Update session
    Object.assign(session, updates);

    // Save to disk
    await this.saveSessions();

    return session;
  }

  /**
   * Delete a session
   * @param {string} sessionId - Session ID
   * @returns {Promise<void>}
   */
  async deleteSession(sessionId) {
    // Remove session
    this.sessions.delete(sessionId);
    this.messages.delete(sessionId);

    // Save to disk
    await this.saveSessions();

    // Delete messages file
    try {
      const messagesFile = path.join(this.dataDir, 'messages', `${sessionId}.json`);
      await fs.unlink(messagesFile);
    } catch (error) {
      // Ignore if file doesn't exist
      if (error.code !== 'ENOENT') {
        console.error(`Error deleting messages file for session ${sessionId}:`, error);
      }
    }
  }

  /**
   * Add a message to a session
   * @param {string} sessionId - Session ID
   * @param {Object} message - Message data
   * @returns {Promise<Object>} - Added message
   */
  async addMessage(sessionId, message) {
    // Get messages
    let messages = this.messages.get(sessionId);
    if (!messages) {
      messages = [];
      this.messages.set(sessionId, messages);
    }

    // Add message
    messages.push(message);

    // Save to disk
    await this.saveMessages(sessionId);

    return message;
  }

  /**
   * Get all messages for a session
   * @param {string} sessionId - Session ID
   * @returns {Promise<Array<Object>>} - Session messages
   */
  async getMessages(sessionId) {
    return this.messages.get(sessionId) || [];
  }
}

/**
 * Event Bus Service
 * 
 * Manages event subscriptions and publishing
 */
class EventBus {
  constructor() {
    this.subscribers = new Map();
    this.eventSubscribers = new Map();
  }

  /**
   * Subscribe to all events for a session
   * @param {string} sessionId - Session ID
   * @param {Function} callback - Callback function
   * @returns {string} - Subscription ID
   */
  subscribe(sessionId, callback) {
    // Generate subscription ID
    const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Get subscribers for session
    let subscribers = this.subscribers.get(sessionId);
    if (!subscribers) {
      subscribers = new Map();
      this.subscribers.set(sessionId, subscribers);
    }

    // Add subscriber
    subscribers.set(subscriptionId, callback);

    return subscriptionId;
  }

  /**
   * Unsubscribe from all events for a session
   * @param {string} sessionId - Session ID
   * @param {string} subscriptionId - Subscription ID
   * @returns {boolean} - Whether unsubscription was successful
   */
  unsubscribe(sessionId, subscriptionId) {
    // Get subscribers for session
    const subscribers = this.subscribers.get(sessionId);
    if (!subscribers) {
      return false;
    }

    // Remove subscriber
    return subscribers.delete(subscriptionId);
  }

  /**
   * Subscribe to a specific event type for a session
   * @param {string} sessionId - Session ID
   * @param {string} eventType - Event type
   * @param {Function} callback - Callback function
   * @returns {string} - Subscription ID
   */
  subscribeToEvent(sessionId, eventType, callback) {
    // Generate subscription ID
    const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Get event subscribers
    let eventSubscribers = this.eventSubscribers.get(eventType);
    if (!eventSubscribers) {
      eventSubscribers = new Map();
      this.eventSubscribers.set(eventType, eventSubscribers);
    }

    // Get session subscribers
    let sessionSubscribers = eventSubscribers.get(sessionId);
    if (!sessionSubscribers) {
      sessionSubscribers = new Map();
      eventSubscribers.set(sessionId, sessionSubscribers);
    }

    // Add subscriber
    sessionSubscribers.set(subscriptionId, callback);

    return subscriptionId;
  }

  /**
   * Unsubscribe from a specific event type for a session
   * @param {string} sessionId - Session ID
   * @param {string} eventType - Event type
   * @param {Function} callback - Callback function
   * @returns {boolean} - Whether unsubscription was successful
   */
  unsubscribeFromEvent(sessionId, eventType, callback) {
    // Get event subscribers
    const eventSubscribers = this.eventSubscribers.get(eventType);
    if (!eventSubscribers) {
      return false;
    }

    // Get session subscribers
    const sessionSubscribers = eventSubscribers.get(sessionId);
    if (!sessionSubscribers) {
      return false;
    }

    // Find subscription ID for callback
    for (const [subscriptionId, cb] of sessionSubscribers.entries()) {
      if (cb === callback) {
        // Remove subscriber
        return sessionSubscribers.delete(subscriptionId);
      }
    }

    return false;
  }

  /**
   * Publish an event for a session
   * @param {string} sessionId - Session ID
   * @param {Object} event - Event data
   */
  publish(sessionId, event) {
    // Get subscribers for session
    const subscribers = this.subscribers.get(sessionId);
    if (subscribers) {
      // Notify subscribers
      for (const callback of subscribers.values()) {
        try {
          callback(event);
        } catch (error) {
          console.error(`Error notifying subscriber for session ${sessionId}:`, error);
        }
      }
    }

    // Get event subscribers
    const eventType = event.type;
    const eventSubscribers = this.eventSubscribers.get(eventType);
    if (eventSubscribers) {
      // Get session subscribers
      const sessionSubscribers = eventSubscribers.get(sessionId);
      if (sessionSubscribers) {
        // Notify subscribers
        for (const callback of sessionSubscribers.values()) {
          try {
            callback(event);
          } catch (error) {
            console.error(`Error notifying event subscriber for session ${sessionId} and event ${eventType}:`, error);
          }
        }
      }
    }
  }
}

module.exports = {
  AgentManager,
  SessionManager,
  EventBus
};
