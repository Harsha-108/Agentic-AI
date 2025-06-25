# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Multi-Agent POC Backend - a sophisticated FastAPI-based WebSocket server implementing specialized AI agents with external WebSocket bridging capabilities. The system combines local AI agents (Helios for fitness, Ceres for nutrition) with intelligent message routing, file-based context storage, and seamless external integration.

## Architecture

### Core Components
- **FastAPI Server** (`app/main_py.py`): Central orchestrator with WebSocket hub, ConnectionManager, and REST API
- **Agent System** (`app/agents_py.py`): Three specialized AI agents inheriting from BaseAgent
- **Message Routing** (`app/router_py.py`): Two-tier routing (fast keywords + LLM classification)
- **LLM Service** (`app/llm_service_py.py`): OpenAI GPT-4o-mini integration with intent classification
- **File Service** (`app/file_service_py.py`): Async file operations for context storage
- **External Bridge** (`app/external_bridge_py.py`): Auto-reconnecting external WebSocket connections
- **Data Models** (`app/models_py.py`): Pydantic models for type safety and validation

### Agent Specializations
- **Helios 💪**: Fitness specialist with workout tracking tools (save_workout, get_workout_history)
- **Ceres 🥗**: Nutrition expert with meal logging tools (save_meal, dietary_preferences)
- **General 🤖**: Coordinator with note-taking capabilities and agent routing

### Message Flow Architecture
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

## Development Commands

### Start Development Server
```bash
./run.sh
```
This script handles:
- Virtual environment setup (`python3 -m venv venv`)
- Dependency installation (`pip install -r requirements.txt`)
- Environment validation (OpenAI API key check)
- Server startup (`uvicorn main:app --reload`)

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

### Manual Server Start
```bash
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional - External WebSocket integration
EXTERNAL_WS_URL=wss://external-server.com/ws
EXTERNAL_WS_USER_ID=poc-backend
```

### Dependencies
Install via: `pip install -r requirements.txt`
- fastapi
- uvicorn[standard]
- websockets
- openai
- python-dotenv
- aiofiles

## Key Endpoints

### WebSocket
- `ws://localhost:8000/ws/{user_id}` - Real-time agent chat

### REST API
- `GET /health` - Server health and metrics
- `GET /external-status` - External WebSocket status
- `POST /send-to-external` - Send to external WebSocket
- `GET /user/{user_id}/files` - User context files

## File Structure

### User Context Storage
Each user gets a directory in `user_contexts/{user_id}/`:
- `conversations.md` - Human-readable chat logs with timestamps
- `helios_data.json` - Fitness data (workouts, goals, preferences)  
- `ceres_data.json` - Nutrition data (meals, dietary preferences, allergies)
- `notes.md` - General notes and reminders
- `external_conversations.md` - External WebSocket interactions (if applicable)

### Agent Tool Systems
**Helios Tools**: save_workout, get_workout_history, set_fitness_goal, get_user_fitness_data
**Ceres Tools**: save_meal, get_meal_history, set_dietary_preference, get_user_nutrition_data  
**General Tools**: save_note, get_notes

### Two-Tier Message Routing
**Tier 1 - Fast Keyword Routing** (<10ms):
- Fitness keywords: workout, exercise, gym, fitness, training, muscle, cardio
- Nutrition keywords: food, eat, meal, diet, nutrition, recipe, calories, protein
- Greeting keywords: hello, hi, hey, good morning

**Tier 2 - LLM Classification** (200-1000ms):
- Used when keyword routing fails
- Considers conversation history context
- Returns confidence scores (0.0-1.0)
- Fallback to General agent if uncertain

## Testing

### Load Testing
```bash
python clients/load_test_py.py --clients 10 --duration 30
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Browser Test Clients
- `clients/test_local_client.html` - Local WebSocket testing
- `clients/test_external_client.html` - External WebSocket testing

## External Integration

The system bridges external WebSocket servers with local agents through `ExternalWebSocketBridge`:

### External Message Flow
```
External Server → ExternalBridge → process_external_message()
                                           ↓
                                   Virtual User Session
                                           ↓
                                   Standard Agent Pipeline
                                           ↓
                                   Response → ExternalBridge → External Server
```

### Configuration
```bash
EXTERNAL_WS_URL=wss://friend-server.onrender.com/ws/{user_id}
EXTERNAL_WS_USER_ID=poc-backend
```

### Features
- Auto-reconnection with exponential backoff
- Handles both JSON and plain text messages
- Creates virtual user sessions for external messages
- Logs all external interactions to `external-socket-user/` directory

## Code Conventions

- **Naming**: Files use `snake_py.py` naming convention (due to import conflicts)
- **Async/Await**: All I/O operations are async for performance
- **Error Handling**: Graceful degradation with try/catch blocks
- **Logging**: Structured logging with timestamps throughout
- **Type Hints**: Pydantic models ensure type safety
- **File Storage**: Human-readable markdown + structured JSON
- **Base Classes**: All agents inherit from `BaseAgent`

## Performance Characteristics

- **Keyword Routing**: <10ms response time
- **LLM Classification**: 200-1000ms (OpenAI API dependent)
- **Tool Execution**: 50-200ms (file operations)
- **Concurrent Connections**: Tested with 50+ simultaneous WebSocket connections
- **Message Throughput**: 100+ messages/minute per agent

## Important Implementation Details

- **ConnectionManager**: Handles WebSocket lifecycle and message broadcasting
- **Service Injection**: FileService and LLMService injected into all agents
- **Context Preservation**: Conversation history maintained across sessions
- **Tool Registration**: Agents register tools via `_register_tools()` method
- **Validation**: Pydantic models validate all data structures
- **External Bridge**: Creates virtual users for external message processing