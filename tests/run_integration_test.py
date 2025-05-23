"""
Integration Test Runner for OpenManusEnhanced

This script runs the backend server and frontend client for integration testing.
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
import threading

# Configuration
BACKEND_PORT = 8765
FRONTEND_PORT = 3000
TEST_SESSION_ID = "test-session-" + str(int(time.time()))

def run_backend_server():
    """Run the backend integration test server"""
    print("Starting backend integration test server...")
    subprocess.run([
        "python", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "integration_test.py")
    ])

def run_frontend_server():
    """Run the frontend development server"""
    print("Starting frontend development server...")
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"))
    subprocess.run(["npm", "start"])

def open_browser():
    """Open browser with test session ID"""
    print(f"Opening browser with test session ID: {TEST_SESSION_ID}")
    time.sleep(5)  # Wait for servers to start
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}?session={TEST_SESSION_ID}")

def main():
    """Run the integration test"""
    print("=== OpenManusEnhanced Integration Test Runner ===")
    print(f"Test Session ID: {TEST_SESSION_ID}")
    
    # Start backend server in a separate thread
    backend_thread = threading.Thread(target=run_backend_server)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Start frontend server in a separate thread
    frontend_thread = threading.Thread(target=run_frontend_server)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    # Open browser
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Keep main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping integration test...")
        sys.exit(0)

if __name__ == "__main__":
    main()
