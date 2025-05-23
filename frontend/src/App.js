import React, { useState } from 'react';
import AgentVisualization from './components/Visualization/AgentVisualization';
import './App.css';

function App() {
  const [sessionId] = useState('test-session-' + Math.random().toString(36).substring(2, 9));
  
  return (
    <div className="App">
      <header className="App-header">
        <h1>OpenManusEnhanced</h1>
        <p>An open-source AI agent with real-time visualization</p>
      </header>
      <main>
        <AgentVisualization 
          sessionId={sessionId} 
          agentName="Manus"
        />
      </main>
      <footer>
        <p>Session ID: {sessionId}</p>
      </footer>
    </div>
  );
}

export default App;
