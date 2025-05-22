"""
Main Server Module for OpenManusEnhanced

This module provides the Express.js server for the backend.
It sets up the API routes, WebSocket server, and static file serving.
"""

const express = require('express');
const http = require('http');
const path = require('path');
const WebSocket = require('ws');
const cors = require('cors');
const bodyParser = require('body-parser');
const apiRoutes = require('./api/routes');
const { AgentManager, SessionManager, EventBus } = require('./services');

// Create Express app
const app = express();
const port = process.env.PORT || 3000;

// Create HTTP server
const server = http.createServer(app);

// Create WebSocket server
const wss = new WebSocket.Server({ server, path: '/agent' });

// Create services
const agentManager = new AgentManager();
const sessionManager = new SessionManager();
const eventBus = new EventBus();

// Set up middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Set up API routes
app.use('/api', apiRoutes);

// Serve static files from frontend build directory
app.use(express.static(path.join(__dirname, '../frontend/build')));

// Serve index.html for all other routes (SPA fallback)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/build/index.html'));
});

// Set up WebSocket connection handler
wss.on('connection', (ws, req) => {
  console.log('WebSocket connection established');
  
  // Handle WebSocket messages
  ws.on('message', (message) => {
    console.log('WebSocket message received:', message);
  });
  
  // Handle WebSocket close
  ws.on('close', () => {
    console.log('WebSocket connection closed');
  });
  
  // Handle WebSocket error
  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

// Initialize services
async function initializeServices() {
  try {
    // Set event bus for agent manager
    agentManager.setEventBus(eventBus);
    
    // Initialize session manager
    await sessionManager.initialize();
    
    console.log('Services initialized successfully');
  } catch (error) {
    console.error('Error initializing services:', error);
  }
}

// Start server
async function startServer() {
  try {
    // Initialize services
    await initializeServices();
    
    // Start HTTP server
    server.listen(port, () => {
      console.log(`Server listening on port ${port}`);
    });
  } catch (error) {
    console.error('Error starting server:', error);
  }
}

// Handle process termination
process.on('SIGINT', async () => {
  console.log('Shutting down server...');
  
  // Close HTTP server
  server.close();
  
  // Exit process
  process.exit(0);
});

// Start server
startServer();

module.exports = { app, server };
