import openai
import os
import json
import logging
from typing import List, Dict, Any, Optional
from .models import Message, AgentIntent

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    async def get_completion(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Get completion from OpenAI"""
        try:
            # Prepare messages
            formatted_messages = []
            
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            
            formatted_messages.extend(messages)
            
            # Get completion
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            return f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"
    
    async def classify_intent(
        self, 
        message: str, 
        conversation_history: List[Message],
        available_agents: List[str]
    ) -> AgentIntent:
        """Classify user intent and route to appropriate agent"""
        
        # Build context from conversation history
        history_context = ""
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            for msg in recent_messages:
                history_context += f"{msg.sender}: {msg.content}\n"
        
        classification_prompt = f"""
        You are a message router for a multi-agent system. Analyze the user's message and determine which agent should handle it.

        Available agents:
        - helios: Handles fitness, workouts, exercise, training, gym activities, physical health, sports
        - ceres: Handles nutrition, food, meals, diet, recipes, cooking, eating habits, dietary advice
        - general: For greetings, general questions, chitchat, or unclear requests

        Recent conversation context:
        {history_context}

        User message: "{message}"

        Respond with a JSON object containing:
        {{
            "agent": "agent_name",
            "confidence": 0.8,
            "reasoning": "explanation of why this agent was chosen",
            "extracted_params": {{"param": "value"}}
        }}

        Rules:
        - Route fitness/exercise/workout questions to helios
        - Route food/nutrition/diet questions to ceres  
        - Route greetings and general chat to general
        - If uncertain, use general with lower confidence
        - Confidence should be 0.0-1.0
        """
        
        try:
            response = await self.get_completion(
                messages=[{"role": "user", "content": message}],
                system_prompt=classification_prompt,
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse JSON response
            intent_data = json.loads(response)
            
            return AgentIntent(
                agent=intent_data.get("agent", "general"),
                confidence=float(intent_data.get("confidence", 0.5)),
                reasoning=intent_data.get("reasoning", "Default routing"),
                extracted_params=intent_data.get("extracted_params", {})
            )
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return AgentIntent(
                agent="general",
                confidence=0.3,
                reasoning=f"Error in classification: {str(e)}"
            )