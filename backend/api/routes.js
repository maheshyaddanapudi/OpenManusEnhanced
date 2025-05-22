"""
Backend API Module for OpenManusEnhanced

This module provides the Express.js API endpoints for the backend server.
It handles agent session management, tool execution, and event streaming.
"""

const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const { AgentManager } = require('../services/agentManager');
const { SessionManager } = require('../services/sessionManager');
const { EventBus } = require('../services/eventBus');

// Initialize managers
const agentManager = new AgentManager();
const sessionManager = new SessionManager();
const eventBus = new EventBus();

/**
 * Create a new agent session
 * POST /api/sessions
 */
router.post('/sessions', async (req, res) => {
  try {
    const { name, systemPrompt } = req.body;
    
    // Create session
    const sessionId = uuidv4();
    const session = await sessionManager.createSession({
      id: sessionId,
      name: name || 'New Session',
      createdAt: new Date(),
      status: 'initializing'
    });
    
    // Initialize agent
    await agentManager.createAgent(sessionId, {
      systemPrompt: systemPrompt
    });
    
    // Update session status
    await sessionManager.updateSession(sessionId, {
      status: 'ready'
    });
    
    res.status(201).json(session);
  } catch (error) {
    console.error('Error creating session:', error);
    res.status(500).json({ error: 'Failed to create session' });
  }
});

/**
 * Get all sessions
 * GET /api/sessions
 */
router.get('/sessions', async (req, res) => {
  try {
    const sessions = await sessionManager.getAllSessions();
    res.json(sessions);
  } catch (error) {
    console.error('Error getting sessions:', error);
    res.status(500).json({ error: 'Failed to get sessions' });
  }
});

/**
 * Get a session by ID
 * GET /api/sessions/:id
 */
router.get('/sessions/:id', async (req, res) => {
  try {
    const session = await sessionManager.getSession(req.params.id);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    res.json(session);
  } catch (error) {
    console.error('Error getting session:', error);
    res.status(500).json({ error: 'Failed to get session' });
  }
});

/**
 * Delete a session
 * DELETE /api/sessions/:id
 */
router.delete('/sessions/:id', async (req, res) => {
  try {
    const sessionId = req.params.id;
    
    // Stop agent if running
    await agentManager.stopAgent(sessionId);
    
    // Delete session
    await sessionManager.deleteSession(sessionId);
    
    res.status(204).end();
  } catch (error) {
    console.error('Error deleting session:', error);
    res.status(500).json({ error: 'Failed to delete session' });
  }
});

/**
 * Send a message to an agent
 * POST /api/sessions/:id/messages
 */
router.post('/sessions/:id/messages', async (req, res) => {
  try {
    const sessionId = req.params.id;
    const { content } = req.body;
    
    // Check if session exists
    const session = await sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    // Add message to session
    const message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date()
    };
    
    await sessionManager.addMessage(sessionId, message);
    
    // Send message to agent
    await agentManager.sendMessage(sessionId, message);
    
    res.status(201).json(message);
  } catch (error) {
    console.error('Error sending message:', error);
    res.status(500).json({ error: 'Failed to send message' });
  }
});

/**
 * Get all messages for a session
 * GET /api/sessions/:id/messages
 */
router.get('/sessions/:id/messages', async (req, res) => {
  try {
    const sessionId = req.params.id;
    
    // Check if session exists
    const session = await sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    // Get messages
    const messages = await sessionManager.getMessages(sessionId);
    
    res.json(messages);
  } catch (error) {
    console.error('Error getting messages:', error);
    res.status(500).json({ error: 'Failed to get messages' });
  }
});

/**
 * Start an agent
 * POST /api/sessions/:id/start
 */
router.post('/sessions/:id/start', async (req, res) => {
  try {
    const sessionId = req.params.id;
    
    // Check if session exists
    const session = await sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    // Start agent
    await agentManager.startAgent(sessionId);
    
    // Update session status
    await sessionManager.updateSession(sessionId, {
      status: 'running'
    });
    
    res.status(200).json({ status: 'running' });
  } catch (error) {
    console.error('Error starting agent:', error);
    res.status(500).json({ error: 'Failed to start agent' });
  }
});

/**
 * Stop an agent
 * POST /api/sessions/:id/stop
 */
router.post('/sessions/:id/stop', async (req, res) => {
  try {
    const sessionId = req.params.id;
    
    // Check if session exists
    const session = await sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    // Stop agent
    await agentManager.stopAgent(sessionId);
    
    // Update session status
    await sessionManager.updateSession(sessionId, {
      status: 'stopped'
    });
    
    res.status(200).json({ status: 'stopped' });
  } catch (error) {
    console.error('Error stopping agent:', error);
    res.status(500).json({ error: 'Failed to stop agent' });
  }
});

/**
 * Take control of an agent
 * POST /api/sessions/:id/control/take
 */
router.post('/sessions/:id/control/take', async (req, res) => {
  try {
    const sessionId = req.params.id;
    
    // Check if session exists
    const session = await sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    // Take control
    await agentManager.takeControl(sessionId);
    
    // Update session status
    await sessionManager.updateSession(sessionId, {
      status: 'human_control'
    });
    
    res.status(200).json({ status: 'human_control' });
  } catch (error) {
    console.error('Error taking control:', error);
    res.status(500).json({ error: 'Failed to take control' });
  }
});

/**
 * Release control of an agent
 * POST /api/sessions/:id/control/release
 */
router.post('/sessions/:id/control/release', async (req, res) => {
  try {
    const sessionId = req.params.id;
    
    // Check if session exists
    const session = await sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    // Release control
    await agentManager.releaseControl(sessionId);
    
    // Update session status
    await sessionManager.updateSession(sessionId, {
      status: 'running'
    });
    
    res.status(200).json({ status: 'running' });
  } catch (error) {
    console.error('Error releasing control:', error);
    res.status(500).json({ error: 'Failed to release control' });
  }
});

/**
 * Execute a tool as human
 * POST /api/sessions/:id/tools/:tool
 */
router.post('/sessions/:id/tools/:tool', async (req, res) => {
  try {
    const sessionId = req.params.id;
    const toolName = req.params.tool;
    const args = req.body;
    
    // Check if session exists
    const session = await sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    // Check if session is in human control
    if (session.status !== 'human_control') {
      return res.status(400).json({ error: 'Session must be in human control to execute tools' });
    }
    
    // Execute tool
    const result = await agentManager.executeHumanTool(sessionId, toolName, args);
    
    res.status(200).json(result);
  } catch (error) {
    console.error('Error executing tool:', error);
    res.status(500).json({ error: 'Failed to execute tool' });
  }
});

/**
 * Subscribe to session events (Server-Sent Events)
 * GET /api/sessions/:id/events
 */
router.get('/sessions/:id/events', async (req, res) => {
  try {
    const sessionId = req.params.id;
    
    // Check if session exists
    const session = await sessionManager.getSession(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    // Set up SSE
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();
    
    // Function to send events to client
    const sendEvent = (event) => {
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    };
    
    // Subscribe to events for this session
    const subscriptionId = eventBus.subscribe(sessionId, sendEvent);
    
    // Send initial state
    sendEvent({
      type: 'session_state',
      data: {
        session,
        messages: await sessionManager.getMessages(sessionId)
      }
    });
    
    // Handle client disconnect
    req.on('close', () => {
      eventBus.unsubscribe(sessionId, subscriptionId);
    });
  } catch (error) {
    console.error('Error setting up event stream:', error);
    res.status(500).json({ error: 'Failed to set up event stream' });
  }
});

module.exports = router;
