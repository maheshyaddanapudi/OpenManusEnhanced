/**
 * WebSocket Service for OpenManusEnhanced
 * 
 * This service manages the WebSocket connection between the frontend and backend,
 * handling real-time events and agent visualization data.
 */

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Initial delay in milliseconds
    this.eventHandlers = {};
    this.sessionId = null;
  }

  /**
   * Connect to the WebSocket server
   * @param {string} sessionId - Session ID for the connection
   * @param {string} url - WebSocket server URL (optional)
   * @returns {Promise} - Resolves when connected, rejects on failure
   */
  connect(sessionId, url = 'ws://localhost:3001/frontend') {
    return new Promise((resolve, reject) => {
      if (this.isConnected) {
        resolve();
        return;
      }

      this.sessionId = sessionId;
      const fullUrl = `${url}?session_id=${sessionId}`;
      
      try {
        this.socket = new WebSocket(fullUrl);
        
        this.socket.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this._sendConnectionMessage();
          resolve();
        };
        
        this.socket.onclose = (event) => {
          console.log(`WebSocket disconnected: ${event.code} - ${event.reason}`);
          this.isConnected = false;
          this._attemptReconnect();
        };
        
        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          if (!this.isConnected) {
            reject(error);
          }
        };
        
        this.socket.onmessage = (event) => {
          this._handleMessage(event.data);
        };
      } catch (error) {
        console.error('Error creating WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    if (this.socket && this.isConnected) {
      this.socket.close();
      this.isConnected = false;
      this.socket = null;
    }
  }

  /**
   * Send a message to the WebSocket server
   * @param {string} type - Message type
   * @param {object} data - Message data
   * @returns {boolean} - True if sent, false otherwise
   */
  sendMessage(type, data) {
    if (!this.isConnected || !this.socket) {
      console.warn('Cannot send message: WebSocket not connected');
      return false;
    }

    const message = {
      type,
      data,
      session_id: this.sessionId,
      timestamp: Date.now()
    };

    try {
      this.socket.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Error sending message:', error);
      return false;
    }
  }

  /**
   * Subscribe to an event
   * @param {string} eventType - Event type to subscribe to
   * @param {function} callback - Function to call when event is received
   * @returns {string} - Subscription ID
   */
  subscribe(eventType, callback) {
    if (!this.eventHandlers[eventType]) {
      this.eventHandlers[eventType] = [];
    }

    const subscriptionId = `${eventType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.eventHandlers[eventType].push({
      id: subscriptionId,
      callback
    });

    return subscriptionId;
  }

  /**
   * Unsubscribe from an event
   * @param {string} eventType - Event type
   * @param {string} subscriptionId - Subscription ID
   * @returns {boolean} - True if unsubscribed, false otherwise
   */
  unsubscribe(eventType, subscriptionId) {
    if (!this.eventHandlers[eventType]) {
      return false;
    }

    const initialLength = this.eventHandlers[eventType].length;
    this.eventHandlers[eventType] = this.eventHandlers[eventType].filter(
      handler => handler.id !== subscriptionId
    );

    return this.eventHandlers[eventType].length < initialLength;
  }

  /**
   * Send connection message to the server
   * @private
   */
  _sendConnectionMessage() {
    this.sendMessage('connection', {
      status: 'connected',
      client_info: {
        type: 'frontend',
        version: '1.0.0',
        user_agent: navigator.userAgent
      }
    });
  }

  /**
   * Attempt to reconnect to the WebSocket server
   * @private
   */
  _attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Maximum reconnection attempts reached');
      this._emitEvent('connection_failed', {
        reason: 'Maximum reconnection attempts reached'
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.isConnected) {
        this.connect(this.sessionId).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  /**
   * Handle incoming WebSocket message
   * @param {string} messageData - Raw message data
   * @private
   */
  _handleMessage(messageData) {
    try {
      const message = JSON.parse(messageData);
      const { type, data } = message;
      
      // Emit the event to all subscribers
      this._emitEvent(type, data);
      
      // Handle specific message types
      switch (type) {
        case 'ping':
          this.sendMessage('pong', { received_at: Date.now() });
          break;
          
        case 'agent_event':
          this._handleAgentEvent(data);
          break;
          
        case 'tool_event':
          this._handleToolEvent(data);
          break;
          
        case 'visualization_event':
          this._handleVisualizationEvent(data);
          break;
          
        default:
          // No special handling for other message types
          break;
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  }

  /**
   * Handle agent events
   * @param {object} data - Event data
   * @private
   */
  _handleAgentEvent(data) {
    // Special handling for agent events if needed
    this._emitEvent(`agent:${data.event_type || 'event'}`, data);
  }

  /**
   * Handle tool events
   * @param {object} data - Event data
   * @private
   */
  _handleToolEvent(data) {
    // Special handling for tool events if needed
    const toolName = data.tool_name || 'unknown';
    this._emitEvent(`tool:${toolName}:${data.event_type || 'event'}`, data);
  }

  /**
   * Handle visualization events
   * @param {object} data - Event data
   * @private
   */
  _handleVisualizationEvent(data) {
    // Special handling for visualization events if needed
    this._emitEvent(`visualization:${data.visualization_type || 'event'}`, data);
  }

  /**
   * Emit an event to all subscribers
   * @param {string} eventType - Event type
   * @param {object} data - Event data
   * @private
   */
  _emitEvent(eventType, data) {
    if (!this.eventHandlers[eventType]) {
      return;
    }

    this.eventHandlers[eventType].forEach(handler => {
      try {
        handler.callback(data);
      } catch (error) {
        console.error(`Error in event handler for ${eventType}:`, error);
      }
    });
  }
}

// Create singleton instance
const webSocketService = new WebSocketService();

export default webSocketService;
