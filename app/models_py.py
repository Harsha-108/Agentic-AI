from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class MessageType(str, Enum):
    USER = "user"
    AGENT = "agent" 
    SYSTEM = "system"
    EXTERNAL = "external"

class Message(BaseModel):
    content: str
    sender: str = "user"
    message_type: MessageType = MessageType.USER
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class AgentIntent(BaseModel):
    agent: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    extracted_params: Optional[Dict[str, Any]] = None

class UserSession(BaseModel):
    user_id: str
    conversation_history: List[Message] = Field(default_factory=list)
    active_agent: Optional[str] = None
    session_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True

class WebSocketMessage(BaseModel):
    type: str = "message"
    message: str
    agent: Optional[str] = None
    timestamp: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ExternalConnectionStatus(BaseModel):
    name: str
    url: str
    connected: bool
    user_id: str
    last_message: Optional[datetime] = None
    message_count: int = 0

class HealthData(BaseModel):
    user_id: str
    workouts: List[Dict] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.now)

class NutritionData(BaseModel):
    user_id: str
    meals: List[Dict] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    nutrition_goals: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.now)