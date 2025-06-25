from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from langsmith import traceable

# Load environment variables
load_dotenv()

# Import our modules
from .models import UserSession, Message, MessageType, WebSocketMessage
from .llm_service import LLMService
from .file_service import FileService
from .router import MessageRouter
from .agents import HeliosAgent, CeresAgent, GeneralAgent
from .external_bridge import ExternalWebSocketBridge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Multi-Agent POC Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_service = FileService()
llm_service = LLMService()
router = MessageRouter(llm_service)

# Initialize agents
helios = HeliosAgent(file_service, llm_service)
ceres = CeresAgent(file_service, llm_service)
general_agent = GeneralAgent(file_service, llm_service)

# Session storage
sessions: Dict[str, UserSession] = {}

# External WebSocket bridge
external_bridge: ExternalWebSocketBridge = None

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, user_id: str, agent: str = "System"):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                response = WebSocketMessage(
                    type="message",
                    message=message,
                    agent=agent,
                    timestamp=datetime.now().isoformat()
                )
                await websocket.send_text(response.model_dump_json())
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast(self, message: str, sender: str = "System"):
        """Send message to all connected users"""
        for user_id, websocket in list(self.active_connections.items()):
            try:
                response = WebSocketMessage(
                    type="broadcast",
                    message=message,
                    agent=sender,
                    timestamp=datetime.now().isoformat()
                )
                await websocket.send_text(response.model_dump_json())
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                self.disconnect(user_id)

manager = ConnectionManager()

@traceable(name="process_external_message")
async def process_external_message(message_content: str, sender: str, message_type: str):
    """Process messages from external WebSocket through agents with tracing"""
    try:
        # Create virtual user session for external messages
        external_user_id = "external-socket-user"
        
        # Ensure external user session exists
        if external_user_id not in sessions:
            sessions[external_user_id] = UserSession(user_id=external_user_id)
        
        # Add incoming message to conversation history
        incoming_msg = Message(
            content=message_content,
            sender=sender,
            message_type=MessageType.EXTERNAL
        )
        sessions[external_user_id].conversation_history.append(incoming_msg)
        
        # Route message to appropriate agent
        intent = await router.route_message(
            message_content,
            sessions[external_user_id].conversation_history
        )
        
        logger.info(f"Routing external message to {intent.agent} (confidence: {intent.confidence})")
        
        # Get response from the appropriate agent
        if intent.agent == "helios":
            response = await helios.process_message(
                external_user_id, message_content, sessions[external_user_id].conversation_history
            )
            agent_name = "Helios 💪"
        elif intent.agent == "ceres":
            response = await ceres.process_message(
                external_user_id, message_content, sessions[external_user_id].conversation_history
            )
            agent_name = "Ceres 🥗"
        else:
            response = await general_agent.process_message(
                external_user_id, message_content, sessions[external_user_id].conversation_history
            )
            agent_name = "Assistant 🤖"
        
        # Add agent response to conversation history
        agent_msg = Message(
            content=response,
            sender=intent.agent,
            message_type=MessageType.AGENT
        )
        sessions[external_user_id].conversation_history.append(agent_msg)
        
        # Send response back to external WebSocket
        if external_bridge:
            await external_bridge.send_to_external(response, agent_name)
        
        # Log the interaction
        await file_service.log_to_file(
            external_user_id,
            "external_conversations.md",
            f"[{sender}]: {message_content}\n[{agent_name}]: {response}"
        )
        
        # Broadcast to local connections that external conversation happened
        await manager.broadcast(
            f"External conversation: {sender} asked about {intent.agent} domain",
            "External Monitor"
        )
        
    except Exception as e:
        logger.error(f"Error processing external message: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize external WebSocket connection on startup"""
    global external_bridge
    
    external_url = os.getenv("EXTERNAL_WS_URL")
    if external_url:
        external_user_id = os.getenv("EXTERNAL_WS_USER_ID", "poc-backend")
        
        logger.info(f"Setting up external WebSocket bridge to: {external_url}")
        external_bridge = ExternalWebSocketBridge(external_url, external_user_id)
        
        # Add our message processor as a handler
        external_bridge.add_message_handler(process_external_message)
        
        # Connect to external WebSocket
        success = await external_bridge.connect_to_external()
        if success:
            logger.info("✅ External WebSocket bridge established successfully")
        else:
            logger.error("❌ Failed to establish external WebSocket bridge")
    else:
        logger.info("No external WebSocket URL configured")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up external connections on shutdown"""
    global external_bridge
    if external_bridge:
        await external_bridge.disconnect()

# REST API Endpoints

@app.get("/")
async def root():
    return {"message": "Multi-Agent POC Backend", "status": "running", "agents": ["helios", "ceres", "general"]}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    external_status = external_bridge.get_status() if external_bridge else {"connected": False}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(sessions),
        "active_connections": len(manager.active_connections),
        "external_bridge": external_status,
        "agents": {
            "helios": "fitness & exercise",
            "ceres": "nutrition & food", 
            "general": "general assistance"
        }
    }

@app.get("/sessions")
async def get_sessions():
    """Get active user sessions"""
    return {
        "total_sessions": len(sessions),
        "sessions": [
            {
                "user_id": session.user_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "message_count": len(session.conversation_history)
            }
            for session in sessions.values()
        ]
    }

@app.get("/external-status")
async def external_status():
    """Get external WebSocket connection status"""
    if external_bridge:
        return external_bridge.get_status()
    return {"connected": False, "message": "No external bridge configured"}

@app.post("/send-to-external")
async def send_to_external_endpoint(message: dict):
    """Send message to external WebSocket"""
    if external_bridge and external_bridge.is_connected:
        content = message.get("content", message.get("message", ""))
        agent = message.get("agent", "Manual")
        
        if not content:
            raise HTTPException(status_code=400, detail="Message content is required")
        
        success = await external_bridge.send_to_external(content, agent)
        return {"success": success, "message": "Message sent to external WebSocket"}
    
    return {"success": False, "error": "Not connected to external WebSocket"}

@app.get("/user/{user_id}/files")
async def get_user_files(user_id: str):
    """Get list of files for a user"""
    files = await file_service.list_user_files(user_id)
    return {"user_id": user_id, "files": files}

@app.get("/user/{user_id}/file/{filename}")
async def get_user_file(user_id: str, filename: str):
    """Get content of a specific user file"""
    content = await file_service.read_file(user_id, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"user_id": user_id, "filename": filename, "content": content}

# WebSocket endpoint
@app.websocket("/ws/{user_id}")
@traceable(name="websocket_endpoint")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket endpoint for real-time communication with tracing"""
    await manager.connect(websocket, user_id)
    
    # Initialize user session
    if user_id not in sessions:
        sessions[user_id] = UserSession(user_id=user_id)
    
    # Send welcome message
    await manager.send_personal_message(
        "🤖 Welcome! I'm your multi-agent assistant. I have specialists in fitness (Helios 💪) and nutrition (Ceres 🥗). How can I help you today?",
        user_id,
        "System"
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                user_message = message_data.get("message", "").strip()
                
                if not user_message:
                    continue
                
                logger.info(f"Received from {user_id}: {user_message}")
                
                # Update session activity
                sessions[user_id].last_activity = datetime.now()
                
                # Add user message to conversation history
                user_msg = Message(
                    content=user_message,
                    sender=user_id,
                    message_type=MessageType.USER
                )
                sessions[user_id].conversation_history.append(user_msg)
                
                # Route message to appropriate agent
                intent = await router.route_message(
                    user_message,
                    sessions[user_id].conversation_history
                )
                
                logger.info(f"Routing to {intent.agent} (confidence: {intent.confidence})")
                
                # Send typing indicator
                await manager.send_personal_message(
                    f"{intent.agent.title()} is thinking...",
                    user_id,
                    "System"
                )
                
                # Get response from appropriate agent
                if intent.agent == "helios":
                    response = await helios.process_message(
                        user_id, user_message, sessions[user_id].conversation_history
                    )
                    agent_name = "Helios 💪"
                elif intent.agent == "ceres":
                    response = await ceres.process_message(
                        user_id, user_message, sessions[user_id].conversation_history
                    )
                    agent_name = "Ceres 🥗"
                else:
                    response = await general_agent.process_message(
                        user_id, user_message, sessions[user_id].conversation_history
                    )
                    agent_name = "Assistant 🤖"
                
                # Add agent response to conversation history
                agent_msg = Message(
                    content=response,
                    sender=intent.agent,
                    message_type=MessageType.AGENT
                )
                sessions[user_id].conversation_history.append(agent_msg)
                
                # Send response to user
                await manager.send_personal_message(response, user_id, agent_name)
                
                # Log conversation
                await file_service.log_to_file(
                    user_id,
                    "conversations.md",
                    f"User: {user_message}\n{agent_name}: {response}"
                )
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    "Please send valid JSON messages.",
                    user_id,
                    "System"
                )
            except Exception as e:
                logger.error(f"Error processing message from {user_id}: {e}")
                await manager.send_personal_message(
                    "Sorry, I encountered an error processing your message. Please try again.",
                    user_id,
                    "System"
                )
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)