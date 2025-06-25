# 🤖 Agentic-AI: Multi-Agent POC Backend

A sophisticated FastAPI-based WebSocket server implementing specialized AI agents with external WebSocket bridging capabilities. This system combines local AI agents with intelligent message routing, file-based context storage, and seamless external integration.

## ✨ Features

- **🎯 Specialized AI Agents**: Three purpose-built agents (Helios for fitness, Ceres for nutrition, General for coordination)
- **⚡ Two-Tier Message Routing**: Fast keyword routing (<10ms) with intelligent LLM fallback
- **🔌 External WebSocket Bridge**: Auto-reconnecting connections to external services
- **💾 File-Based Context Storage**: Human-readable conversation logs with structured data
- **🚀 Real-Time Communication**: WebSocket hub with concurrent connection management
- **🛠️ Tool Integration**: Each agent has specialized tools for their domain
- **📊 Health Monitoring**: Built-in health checks and performance metrics

## 🏗️ Architecture

```
User → WebSocket → ConnectionManager → MessageRouter
                                           ↓
                                   Intent Classification
                                    (Keywords + LLM)
                                           ↓
                                   Agent Selection
                               ┌──────────┼──────────┐
                               ↓          ↓          ↓
                         Helios 💪   Ceres 🥗   General 🤖
                               ↓          ↓          ↓
                       LLM Processing + Tool Execution
                               ↓          ↓          ↓
                       File Logging + Context Storage
                               ↓          ↓          ↓
                           Response → WebSocket → User
```

### Core Components

- **FastAPI Server** (`app/main_py.py`): Central orchestrator with WebSocket hub
- **Agent System** (`app/agents_py.py`): Specialized AI agents with inheritance
- **Message Routing** (`app/router_py.py`): Two-tier intelligent routing system
- **LLM Service** (`app/llm_service_py.py`): OpenAI GPT-4o-mini integration
- **File Service** (`app/file_service_py.py`): Async file operations
- **External Bridge** (`app/external_bridge_py.py`): External WebSocket connections

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API Key

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Harsha-108/Agentic-AI.git
   cd Agentic-AI
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Start the server**
   ```bash
   ./run.sh
   ```

That's it! The server will be running at `http://localhost:8000`

### Alternative Commands
```bash
# Load testing
./run.sh test

# External WebSocket monitoring
./run.sh monitor [websocket_url]

# Health check
./run.sh health

# Clean environment
./run.sh clean
```

## 🤖 AI Agents

### Helios 💪 - Fitness Specialist
- **Purpose**: Workout tracking, fitness planning, exercise guidance
- **Tools**: `save_workout`, `get_workout_history`, `set_fitness_goal`
- **Expertise**: Exercise routines, fitness goals, progress tracking

### Ceres 🥗 - Nutrition Expert
- **Purpose**: Meal logging, dietary guidance, nutrition planning
- **Tools**: `save_meal`, `get_meal_history`, `set_dietary_preference`
- **Expertise**: Nutrition advice, meal planning, dietary restrictions

### General 🤖 - Coordinator
- **Purpose**: Note-taking, agent routing, general assistance
- **Tools**: `save_note`, `get_notes`
- **Expertise**: Task coordination, information management

## 📡 API Endpoints

### WebSocket
- `ws://localhost:8000/ws/{user_id}` - Real-time agent chat

### REST API
- `GET /health` - Server health and metrics
- `GET /external-status` - External WebSocket status
- `POST /send-to-external` - Send to external WebSocket
- `GET /user/{user_id}/files` - User context files

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional - External WebSocket integration
EXTERNAL_WS_URL=wss://external-server.com/ws
EXTERNAL_WS_USER_ID=poc-backend
```

### Dependencies

All dependencies are managed through `requirements.txt`:
- fastapi
- uvicorn[standard]
- websockets
- openai
- python-dotenv
- aiofiles

## 📁 File Structure

```
Agent_Workflow/
├── app/
│   ├── main_py.py              # FastAPI server & WebSocket hub
│   ├── agents_py.py            # AI agent implementations
│   ├── router_py.py            # Message routing system
│   ├── llm_service_py.py       # OpenAI integration
│   ├── file_service_py.py      # File operations
│   ├── external_bridge_py.py   # External WebSocket bridge
│   └── models_py.py            # Pydantic data models
├── clients/
│   ├── test_local_client.html  # Local WebSocket testing
│   ├── test_external_client.html # External WebSocket testing
│   └── load_test_py.py         # Load testing script
├── user_contexts/              # User data storage
├── docs/
│   └── Workflow_documentation.md # Detailed documentation
├── run.sh                      # Universal startup script
├── requirements.txt            # Python dependencies
└── .env.example               # Environment template
```

## 🧪 Testing

### Load Testing
```bash
python clients/load_test_py.py --clients 10 --duration 30
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Browser Testing
- Open `clients/test_local_client.html` for local WebSocket testing
- Open `clients/test_external_client.html` for external bridge testing

## 📊 Performance

- **Keyword Routing**: <10ms response time
- **LLM Classification**: 200-1000ms (OpenAI API dependent)
- **Tool Execution**: 50-200ms (file operations)
- **Concurrent Connections**: Tested with 50+ simultaneous WebSocket connections
- **Message Throughput**: 100+ messages/minute per agent

## 🔌 External Integration

The system can bridge external WebSocket servers with local agents:

```bash
EXTERNAL_WS_URL=wss://friend-server.onrender.com/ws/{user_id}
EXTERNAL_WS_USER_ID=poc-backend
```

Features:
- Auto-reconnection with exponential backoff
- Handles both JSON and plain text messages
- Creates virtual user sessions for external messages
- Logs all external interactions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. See the repository for license details.

## 🆘 Support

- **Documentation**: Check `docs/Workflow_documentation.md` for detailed information
- **Issues**: Report bugs or feature requests in the GitHub issues
- **Health Check**: Use `/health` endpoint for system diagnostics

---

**Built with FastAPI, OpenAI GPT-4o-mini, and WebSocket technology** 🚀