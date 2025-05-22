# OpenManusEnhanced

An open-source alternative to Manus AI with advanced visualization capabilities and human control features.

## Overview

OpenManusEnhanced builds upon the foundation of OpenManus to create a powerful, self-hosted AI agent platform with a modern web interface, real-time tool visualization, and seamless human-agent control handoff.

## Key Features

- **Rich Web Interface**: Modern, responsive UI for multi-turn conversations
- **Tool Visualization**: Real-time display of agent's computer and tool usage
- **Human Control**: Seamless takeover and return of control between human and agent
- **Self-Hosting**: Complete local deployment without external dependencies

## Architecture

OpenManusEnhanced follows a modular architecture:

```
OpenManusEnhanced/
├── agent/                    # Python agent core
│   ├── core/                # Enhanced OpenManus
│   ├── tools/               # Tool implementations
│   └── bridge/              # Node.js communication
├── backend/                 # Node.js server
│   ├── api/                # REST endpoints
│   ├── websocket/          # Real-time events
│   └── services/           # Business logic
├── frontend/               # React application
│   ├── components/         # UI components
│   ├── visualizers/        # Tool visualizers
│   └── hooks/              # Custom hooks
├── database/               # Schema and migrations
└── tests/                  # Test suites
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/maheshyaddanapudi/OpenManusEnhanced.git
   cd OpenManusEnhanced
   ```

2. Set up Python environment:
   ```bash
   # Using pyenv (recommended)
   pyenv install 3.12.10
   pyenv virtualenv 3.12.10 openmanus-enhanced
   pyenv local openmanus-enhanced
   
   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. Set up Node.js environment:
   ```bash
   cd backend
   npm install
   
   cd ../frontend
   npm install
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Running the Application

1. Start the backend:
   ```bash
   cd backend
   npm run start
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run start
   ```

3. Access the application at http://localhost:3000

## Development

This project is under active development. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenManus for the foundational agent framework
- OpenManusWeb for the initial web integration
- Suna AI for architectural inspiration
