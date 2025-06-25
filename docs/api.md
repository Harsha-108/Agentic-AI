# Multi-Agent POC Backend - API Documentation

## Overview

The Multi-Agent POC Backend provides both REST API endpoints and WebSocket connections for real-time agent interactions.

## Base URL
- Local: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws/{user_id}`

## REST API Endpoints

### Health and Status

#### GET `/`
Get basic server information.

**Response:**
```json
{
  "message": "Multi-Agent POC Backend",
  "status": "running",
  "agents": ["helios", "ceres", "general"]
}
```

#### GET `/health`
Get detailed health status and metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "active_sessions": 5,
  "active_connections": 3,
  "external_bridge": {
    "connected": true,
    "url": "wss://external-server.com/ws",
    "user_id": "poc-backend"
  },
  "agents": {
    "helios": "fitness & exercise",
    "ceres": "nutrition & food",
    "general": "general assistance"
  }
}
```

### Session Management

#### GET `/sessions`
Get information about active user sessions.

**Response:**
```json
{
  "total_sessions": 3,
  "sessions": [
    {
      "user_id": "user123",
      "created_at": "2024-01-01T10:00:00Z",
      "last_activity": "2024-01-01T12:00:00Z",
      "message_count": 15
    }
  ]
}
```

### External WebSocket Management

#### GET `/external-status`
Get status of external WebSocket connections.

**Response:**
```json
{
  "connected": true,
  "url": "wss://external-server.com/ws",
  "user_id": "poc-backend",
  "reconnect_attempts": 0,
  "handlers_count": 1
}
```

#### POST `/send-to-external`
Send message to external WebSocket server.

**Request Body:**
```json
{
  "content": "Hello from POC backend!",
  "agent": "Assistant"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message sent to external WebSocket"
}
```

### User File Management

#### GET `/user/{user_id}/files`
Get list of files for a specific user.

**Response:**
```json
{
  "user_id": "user123",
  "files": [
    "conversations.md",
    "helios_data.json",
    "ceres_data.json"
  ]
}
```

#### GET `/user/{user_id}/file/{filename}`
Get content of a specific user file.

**Response:**
```json
{
  "user_id": "user123",
  "filename": "conversations.md",
  "content": "[2024-01-01 12:00:00] User: Hello\n[2024-01-01 12:00:01] Assistant: Hi there!"
}
```

## WebSocket API

### Connection
Connect to: `ws://localhost:8000/ws/{user_id}`

Where `{user_id}` is any unique identifier for the user session.

### Message Format

#### Sending Messages
```json
{
  "type": "message",
  "message": "I want to start working out",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Receiving Messages
```json
{
  "type": "message",
  "message": "Great! I'm Helios, your fitness assistant. Let's create a workout plan for you!",
  "agent": "Helios 💪",
  "timestamp": "2024-01-01T12:00:01Z"
}
```

### Message Types

| Type | Description | Example |
|------|-------------|---------|
| `message` | Regular chat message | User question or agent response |
| `system` | System notifications | Connection status, typing indicators |
| `typing` | Typing indicator | Agent is processing |
| `error` | Error messages | Connection or processing errors |

### Agent Types

| Agent | Trigger Keywords | Capabilities |
|-------|------------------|--------------|
| **Helios 💪** | workout, exercise, fitness, gym, training | Workout planning, exercise advice, fitness tracking |
| **Ceres 🥗** | food, nutrition, meal, diet, recipe | Meal planning, nutrition advice, dietary tracking |
| **General 🤖** | hello, help, general questions | Greetings, general assistance, routing |

## Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (file or resource doesn't exist)
- `500` - Internal Server Error

### WebSocket Error Messages
```json
{
  "type": "error",
  "message": "Sorry, I encountered an error processing your message. Please try again.",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

Currently no rate limiting is implemented in the POC. For production use, consider:
- WebSocket connection limits per IP
- Message rate limits per user
- API request rate limits

## Authentication

The POC doesn't implement authentication. For production:
- Add JWT token authentication
- Implement user registration/login
- Secure WebSocket connections with tokens

## Data Storage

### User Context Files
Each user gets a directory in `user_contexts/{user_id}/`:
- `conversations.md` - All conversation logs
- `helios_data.json` - Fitness data and preferences
- `ceres_data.json` - Nutrition data and preferences
- `notes.md` - User notes and reminders

### File Format Examples

#### Conversation Log (`conversations.md`)
```
[2024-01-01 12:00:00] User: I want to start working out
[2024-01-01 12:00:01] Helios 💪: Great! Let's create a workout plan for you!
```

#### Agent Data (`helios_data.json`)
```json
{
  "workouts": [
    {
      "type": "cardio",
      "duration": "30 minutes",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "goals": [
    {
      "goal": "Build muscle",
      "set_date": "2024-01-01T10:00:00Z",
      "status": "active"
    }
  ],
  "preferences": {},
  "last_updated": "2024-01-01T12:00:00Z"
}
```

## External WebSocket Integration

The backend can connect to external WebSocket servers and process messages through local agents.

### Configuration
Set in `.env` file:
```bash
EXTERNAL_WS_URL=wss://external-server.onrender.com/ws
EXTERNAL_WS_USER_ID=poc-backend
```

### Message Flow
1. External server sends message → POC backend receives
2. POC backend routes to appropriate agent (Helios/Ceres/General)
3. Agent processes and generates response
4. Response sent back to external server
5. Interaction logged locally

## Testing

### Load Testing
```bash
python clients/load_test.py --clients 10 --duration 30
```

### External Monitoring
```bash
python clients/external_monitor.py wss://external-server.com/ws
```

### Health Check
```bash
curl http://localhost:8000/health
```
