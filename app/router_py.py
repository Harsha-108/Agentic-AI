from typing import List
import logging
from langsmith import traceable
from .models import Message, AgentIntent
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class MessageRouter:
    """Routes messages to appropriate agents based on content analysis"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.available_agents = ["helios", "ceres", "general"]
    
    @traceable(name="route_message")
    async def route_message(self, message: str, conversation_history: List[Message]) -> AgentIntent:
        """Analyze message and determine which agent should handle it with LangSmith tracing"""
        
        # Quick keyword-based routing for efficiency
        quick_route = self._quick_route(message)
        if quick_route:
            logger.info(f"Quick route successful: {quick_route.agent} (confidence: {quick_route.confidence})")
            return quick_route
        
        # Use LLM for complex routing
        logger.info("Using LLM classification for routing")
        return await self.llm_service.classify_intent(
            message, 
            conversation_history, 
            self.available_agents
        )
    
    @traceable(name="quick_route")
    def _quick_route(self, message: str) -> AgentIntent:
        """Fast keyword-based routing for common patterns with tracing"""
        message_lower = message.lower()
        
        # Fitness keywords
        fitness_keywords = [
            "workout", "exercise", "gym", "fitness", "training", "run", "lift", 
            "cardio", "strength", "muscle", "pushup", "squat", "deadlift",
            "marathon", "sprint", "yoga", "pilates", "crossfit", "weightlifting"
        ]
        
        # Nutrition keywords  
        nutrition_keywords = [
            "food", "eat", "meal", "diet", "nutrition", "recipe", "cook", "calories",
            "protein", "carbs", "fat", "vitamins", "hungry", "breakfast", "lunch", 
            "dinner", "snack", "vegetarian", "vegan", "keto", "weight loss"
        ]
        
        # Greeting keywords
        greeting_keywords = [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "how are you", "what's up", "greetings", "yo"
        ]
        
        # Check for fitness content
        fitness_score = sum(1 for keyword in fitness_keywords if keyword in message_lower)
        if fitness_score >= 1:
            return AgentIntent(
                agent="helios",
                confidence=0.8 + min(fitness_score * 0.1, 0.2),
                reasoning=f"Found {fitness_score} fitness-related keywords",
                extracted_params={"keywords_found": fitness_score}
            )
        
        # Check for nutrition content
        nutrition_score = sum(1 for keyword in nutrition_keywords if keyword in message_lower)
        if nutrition_score >= 1:
            return AgentIntent(
                agent="ceres",
                confidence=0.8 + min(nutrition_score * 0.1, 0.2),
                reasoning=f"Found {nutrition_score} nutrition-related keywords",
                extracted_params={"keywords_found": nutrition_score}
            )
        
        # Check for greetings
        greeting_score = sum(1 for keyword in greeting_keywords if keyword in message_lower)
        if greeting_score >= 1:
            return AgentIntent(
                agent="general",
                confidence=0.9,
                reasoning="Greeting or general conversation",
                extracted_params={"greeting": True}
            )
        
        # If no quick match, return None to trigger LLM routing
        return None
    
    def get_routing_stats(self) -> dict:
        """Get statistics about routing decisions"""
        return {
            "available_agents": self.available_agents,
            "routing_methods": ["keyword_based", "llm_analysis"],
            "supported_domains": ["fitness", "nutrition", "general"]
        }