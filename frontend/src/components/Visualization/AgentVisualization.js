import React, { useState, useEffect, useRef } from 'react';
import webSocketService from '../../services/WebSocketService';
import './AgentVisualization.css';

/**
 * AgentVisualization Component
 * 
 * Displays real-time visualization of agent activities and tool usage,
 * similar to Manus AI's screen sharing capability.
 */
const AgentVisualization = ({ sessionId, agentName = 'Manus' }) => {
  const [agentState, setAgentState] = useState('IDLE');
  const [currentTool, setCurrentTool] = useState(null);
  const [toolHistory, setToolHistory] = useState([]);
  const [browserContent, setBrowserContent] = useState(null);
  const [terminalContent, setTerminalContent] = useState([]);
  const [isHumanControlActive, setIsHumanControlActive] = useState(false);
  
  const visualizationRef = useRef(null);
  const subscriptions = useRef([]);

  // Connect to WebSocket when component mounts
  useEffect(() => {
    const initializeWebSocket = async () => {
      try {
        await webSocketService.connect(sessionId);
        console.log('WebSocket connected for agent visualization');
        subscribeToEvents();
      } catch (error) {
        console.error('Failed to connect WebSocket for visualization:', error);
      }
    };

    initializeWebSocket();

    // Cleanup on unmount
    return () => {
      unsubscribeFromEvents();
      webSocketService.disconnect();
    };
  }, [sessionId]);

  // Subscribe to relevant events
  const subscribeToEvents = () => {
    // Agent state changes
    subscriptions.current.push(
      webSocketService.subscribe('agent_event', handleAgentEvent)
    );
    
    // Tool events
    subscriptions.current.push(
      webSocketService.subscribe('tool_event', handleToolEvent)
    );
    
    // Visualization events
    subscriptions.current.push(
      webSocketService.subscribe('visualization_event', handleVisualizationEvent)
    );
    
    // Browser visualization
    subscriptions.current.push(
      webSocketService.subscribe('visualization:browser_update', handleBrowserUpdate)
    );
    
    // Terminal visualization
    subscriptions.current.push(
      webSocketService.subscribe('visualization:terminal_update', handleTerminalUpdate)
    );
    
    // Human control events
    subscriptions.current.push(
      webSocketService.subscribe('human:interaction', handleHumanInteraction)
    );
  };

  // Unsubscribe from events
  const unsubscribeFromEvents = () => {
    // Fixed: Handle subscriptions correctly without assuming format
    subscriptions.current.forEach(subscription => {
      // In the actual implementation, subscription is just the ID
      // No need to split as it's already the subscription ID
      webSocketService.unsubscribe(subscription);
    });
    subscriptions.current = [];
  };

  // Handle agent events
  const handleAgentEvent = (data) => {
    if (data.new_state) {
      setAgentState(data.new_state);
    }
  };

  // Handle tool events
  const handleToolEvent = (data) => {
    if (data.tool_name) {
      setCurrentTool({
        name: data.tool_name,
        startTime: data.timestamp,
        status: data.status || 'running'
      });
      
      if (data.status === 'completed' || data.status === 'error') {
        setToolHistory(prev => [
          {
            name: data.tool_name,
            startTime: data.timestamp,
            endTime: Date.now(),
            status: data.status,
            result: data.result
          },
          ...prev.slice(0, 9) // Keep last 10 items
        ]);
        
        // Clear current tool after a delay
        setTimeout(() => {
          setCurrentTool(null);
        }, 2000);
      }
    }
  };

  // Handle visualization events
  const handleVisualizationEvent = (data) => {
    // Generic handler for visualization events
    console.log('Visualization event:', data);
  };

  // Handle browser updates
  const handleBrowserUpdate = (data) => {
    setBrowserContent({
      url: data.url,
      screenshot: data.screenshot,
      content: data.content,
      timestamp: data.timestamp
    });
  };

  // Handle terminal updates
  const handleTerminalUpdate = (data) => {
    if (data.content) {
      setTerminalContent(prev => [...prev, {
        content: data.content,
        timestamp: data.timestamp
      }]);
    }
  };

  // Handle human interaction events
  const handleHumanInteraction = (data) => {
    if (data.type === 'takeover') {
      setIsHumanControlActive(true);
    } else if (data.type === 'release') {
      setIsHumanControlActive(false);
    }
  };

  // Request human control
  const requestHumanControl = () => {
    webSocketService.sendMessage('human_control', {
      control_type: 'takeover_request',
      timestamp: Date.now()
    });
  };

  // Release human control
  const releaseHumanControl = () => {
    webSocketService.sendMessage('human_control', {
      control_type: 'release',
      timestamp: Date.now()
    });
  };

  return (
    <div className="agent-visualization" ref={visualizationRef}>
      <div className="visualization-header">
        <h2>{agentName} Visualization</h2>
        <div className="agent-status">
          Status: <span className={`status-${agentState.toLowerCase()}`}>{agentState}</span>
        </div>
        
        <div className="control-buttons">
          {isHumanControlActive ? (
            <button 
              className="control-button release" 
              onClick={releaseHumanControl}
            >
              Release Control
            </button>
          ) : (
            <button 
              className="control-button takeover" 
              onClick={requestHumanControl}
            >
              Take Control
            </button>
          )}
        </div>
      </div>
      
      <div className="visualization-content">
        <div className="visualization-panel browser-panel">
          <h3>Browser Visualization</h3>
          {browserContent ? (
            <div className="browser-content">
              <div className="browser-header">
                <input 
                  type="text" 
                  className="url-bar" 
                  value={browserContent.url || ''} 
                  readOnly 
                />
              </div>
              <div className="browser-body">
                {browserContent.screenshot ? (
                  <img 
                    src={browserContent.screenshot} 
                    alt="Browser screenshot" 
                    className="browser-screenshot" 
                  />
                ) : (
                  <div className="browser-text-content">
                    {browserContent.content || 'No content to display'}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="empty-state">No browser activity</div>
          )}
        </div>
        
        <div className="visualization-panel terminal-panel">
          <h3>Terminal Visualization</h3>
          <div className="terminal-content">
            {terminalContent.length > 0 ? (
              <pre>
                {terminalContent.map((entry, index) => (
                  <div key={index} className="terminal-line">
                    {entry.content}
                  </div>
                ))}
              </pre>
            ) : (
              <div className="empty-state">No terminal activity</div>
            )}
          </div>
        </div>
      </div>
      
      <div className="tool-activity">
        <h3>Tool Activity</h3>
        {currentTool ? (
          <div className="current-tool">
            <div className="tool-name">{currentTool.name}</div>
            <div className="tool-status">{currentTool.status}</div>
            <div className="tool-progress">
              <div className="progress-bar"></div>
            </div>
          </div>
        ) : (
          <div className="no-tool">No active tool</div>
        )}
        
        <div className="tool-history">
          <h4>Recent Tools</h4>
          {toolHistory.length > 0 ? (
            <ul>
              {toolHistory.map((tool, index) => (
                <li key={index} className={`tool-history-item ${tool.status}`}>
                  <span className="tool-history-name">{tool.name}</span>
                  <span className="tool-history-status">{tool.status}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">No tool history</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentVisualization;
