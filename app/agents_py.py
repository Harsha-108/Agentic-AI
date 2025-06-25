from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import logging
from .models import Message, HealthData, NutritionData
from .llm_service import LLMService
from .file_service import FileService

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str, system_prompt: str, file_service: FileService, llm_service: LLMService):
        self.name = name
        self.system_prompt = system_prompt
        self.file_service = file_service
        self.llm_service = llm_service
        self.tools = self._register_tools()
    
    @abstractmethod
    def _register_tools(self) -> Dict[str, callable]:
        """Register available tools for this agent"""
        pass
    
    async def process_message(self, user_id: str, message: str, conversation_history: List[Message]) -> str:
        """Process a message and return response"""
        try:
            # Build conversation context
            context = self._build_context(conversation_history)
            
            # Get LLM response
            response = await self.llm_service.get_completion(
                messages=[
                    {"role": "user", "content": f"Context: {context}\n\nUser message: {message}"}
                ],
                system_prompt=self.system_prompt,
                temperature=0.7
            )
            
            # Log interaction
            await self.file_service.log_to_file(
                user_id, 
                f"{self.name.lower()}_interactions.md",
                f"User: {message}\n{self.name}: {response}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {self.name} agent: {e}")
            return f"I apologize, but I encountered an error while processing your request. Please try again."
    
    def _build_context(self, conversation_history: List[Message], max_messages: int = 10) -> str:
        """Build conversation context from history"""
        if not conversation_history:
            return "No previous conversation."
        
        recent_messages = conversation_history[-max_messages:]
        context_lines = []
        
        for msg in recent_messages:
            context_lines.append(f"{msg.sender}: {msg.content}")
        
        return "\n".join(context_lines)

class HeliosAgent(BaseAgent):
    """Fitness and exercise agent"""
    
    def __init__(self, file_service: FileService, llm_service: LLMService):
        system_prompt = """You are Helios 💪, a fitness and exercise expert agent. You help users with:

        🏋️ Workout planning and routines
        🏃 Exercise recommendations
        📊 Fitness goal setting and tracking
        💪 Strength training advice
        🏃‍♀️ Cardio optimization
        🧘 Recovery and flexibility
        📈 Progress monitoring

        Your personality:
        - Energetic and motivating
        - Evidence-based approach
        - Adaptable to all fitness levels
        - Safety-first mindset
        - Use fitness emojis: 💪, 🏋️, 🏃, 🔥, 📈

        Always ask about current fitness level, any injuries, and specific goals before giving detailed advice.
        Keep responses practical and actionable.
        """
        
        super().__init__("Helios", system_prompt, file_service, llm_service)
    
    def _register_tools(self) -> Dict[str, callable]:
        return {
            "save_workout": self.save_workout,
            "get_workout_history": self.get_workout_history,
            "set_fitness_goal": self.set_fitness_goal,
            "get_user_fitness_data": self.get_user_fitness_data
        }
    
    async def save_workout(self, user_id: str, workout_data: Dict[str, Any]) -> str:
        """Save workout data for user"""
        try:
            existing_data = await self.file_service.load_json(user_id, "helios_data.json")
            if not existing_data:
                existing_data = {"workouts": [], "goals": [], "preferences": {}}
            
            workout_data["timestamp"] = workout_data.get("timestamp", "now")
            existing_data["workouts"].append(workout_data)
            
            await self.file_service.save_json(user_id, "helios_data.json", existing_data)
            return f"💪 Workout saved! You've logged {len(existing_data['workouts'])} workouts total."
            
        except Exception as e:
            return f"Error saving workout: {str(e)}"
    
    async def get_workout_history(self, user_id: str) -> str:
        """Get user's workout history"""
        try:
            data = await self.file_service.load_json(user_id, "helios_data.json")
            if not data or not data.get("workouts"):
                return "No workout history found. Let's start tracking your fitness journey! 🏃‍♀️"
            
            recent_workouts = data["workouts"][-5:]  # Last 5 workouts
            summary = f"📈 Your recent workouts ({len(data['workouts'])} total):\n"
            
            for i, workout in enumerate(recent_workouts, 1):
                workout_type = workout.get("type", "Workout")
                duration = workout.get("duration", "Unknown duration")
                summary += f"{i}. {workout_type} - {duration}\n"
            
            return summary
            
        except Exception as e:
            return f"Error retrieving workout history: {str(e)}"
    
    async def set_fitness_goal(self, user_id: str, goal: str) -> str:
        """Set fitness goal for user"""
        try:
            existing_data = await self.file_service.load_json(user_id, "helios_data.json")
            if not existing_data:
                existing_data = {"workouts": [], "goals": [], "preferences": {}}
            
            existing_data["goals"].append({
                "goal": goal,
                "set_date": "now",
                "status": "active"
            })
            
            await self.file_service.save_json(user_id, "helios_data.json", existing_data)
            return f"🎯 Goal set: {goal}. Let's crush it together! 💪"
            
        except Exception as e:
            return f"Error setting goal: {str(e)}"
    
    async def get_user_fitness_data(self, user_id: str) -> Dict[str, Any]:
        """Get all fitness data for user"""
        data = await self.file_service.load_json(user_id, "helios_data.json")
        return data or {"workouts": [], "goals": [], "preferences": {}}

class CeresAgent(BaseAgent):
    """Nutrition and food agent"""
    
    def __init__(self, file_service: FileService, llm_service: LLMService):
        system_prompt = """You are Ceres 🥗, a nutrition and food expert agent. You help users with:

        🍽️ Meal planning and recipes
        🥬 Nutritional advice and education
        🍎 Dietary recommendations
        📊 Nutrition tracking
        🚫 Allergy and dietary restriction management
        🥘 Cooking tips and techniques
        📈 Health goal-based nutrition

        Your personality:
        - Warm and nurturing
        - Science-based nutrition knowledge
        - Inclusive of all dietary preferences
        - Practical and budget-conscious
        - Use food emojis: 🥗, 🍎, 🥘, 🌱, 📊

        Always ask about dietary restrictions, allergies, and health goals before making recommendations.
        Provide balanced, sustainable nutrition advice.
        """
        
        super().__init__("Ceres", system_prompt, file_service, llm_service)
    
    def _register_tools(self) -> Dict[str, callable]:
        return {
            "save_meal": self.save_meal,
            "get_meal_history": self.get_meal_history,
            "set_dietary_preference": self.set_dietary_preference,
            "get_user_nutrition_data": self.get_user_nutrition_data
        }
    
    async def save_meal(self, user_id: str, meal_data: Dict[str, Any]) -> str:
        """Save meal data for user"""
        try:
            existing_data = await self.file_service.load_json(user_id, "ceres_data.json")
            if not existing_data:
                existing_data = {"meals": [], "dietary_preferences": [], "allergies": [], "nutrition_goals": {}}
            
            meal_data["timestamp"] = meal_data.get("timestamp", "now")
            existing_data["meals"].append(meal_data)
            
            await self.file_service.save_json(user_id, "ceres_data.json", existing_data)
            return f"🍽️ Meal logged! You've tracked {len(existing_data['meals'])} meals total."
            
        except Exception as e:
            return f"Error saving meal: {str(e)}"
    
    async def get_meal_history(self, user_id: str) -> str:
        """Get user's meal history"""
        try:
            data = await self.file_service.load_json(user_id, "ceres_data.json")
            if not data or not data.get("meals"):
                return "No meal history found. Let's start tracking your nutrition journey! 🌱"
            
            recent_meals = data["meals"][-5:]  # Last 5 meals
            summary = f"📊 Your recent meals ({len(data['meals'])} total):\n"
            
            for i, meal in enumerate(recent_meals, 1):
                meal_name = meal.get("name", "Meal")
                meal_type = meal.get("type", "Snack")
                summary += f"{i}. {meal_name} ({meal_type})\n"
            
            return summary
            
        except Exception as e:
            return f"Error retrieving meal history: {str(e)}"
    
    async def set_dietary_preference(self, user_id: str, preference: str) -> str:
        """Set dietary preference for user"""
        try:
            existing_data = await self.file_service.load_json(user_id, "ceres_data.json")
            if not existing_data:
                existing_data = {"meals": [], "dietary_preferences": [], "allergies": [], "nutrition_goals": {}}
            
            if preference not in existing_data["dietary_preferences"]:
                existing_data["dietary_preferences"].append(preference)
            
            await self.file_service.save_json(user_id, "ceres_data.json", existing_data)
            return f"🌱 Dietary preference added: {preference}. I'll keep this in mind for future recommendations!"
            
        except Exception as e:
            return f"Error setting dietary preference: {str(e)}"
    
    async def get_user_nutrition_data(self, user_id: str) -> Dict[str, Any]:
        """Get all nutrition data for user"""
        data = await self.file_service.load_json(user_id, "ceres_data.json")
        return data or {"meals": [], "dietary_preferences": [], "allergies": [], "nutrition_goals": {}}

class GeneralAgent(BaseAgent):
    """General purpose assistant agent"""
    
    def __init__(self, file_service: FileService, llm_service: LLMService):
        system_prompt = """You are a General Assistant 🤖, a helpful and friendly AI agent. You help with:

        💬 General conversation and questions
        📚 Information and explanations
        🤝 Greetings and social interaction
        🔗 Routing to specialized agents when needed
        📝 Note-taking and reminders
        🎯 Goal planning and organization

        Your personality:
        - Friendly and approachable
        - Helpful and informative
        - Good at understanding context
        - Proactive in suggesting better agents for specific tasks
        - Use general emojis: 🤖, 💬, 📚, 🤝, ✨

        When users ask about fitness, direct them to Helios 💪
        When users ask about nutrition, direct them to Ceres 🥗
        """
        
        super().__init__("General Assistant", system_prompt, file_service, llm_service)
    
    def _register_tools(self) -> Dict[str, callable]:
        return {
            "save_note": self.save_note,
            "get_notes": self.get_notes
        }
    
    async def save_note(self, user_id: str, note: str) -> str:
        """Save a note for the user"""
        try:
            await self.file_service.log_to_file(user_id, "notes.md", f"Note: {note}")
            return f"📝 Note saved! I'll remember that for you."
            
        except Exception as e:
            return f"Error saving note: {str(e)}"
    
    async def get_notes(self, user_id: str) -> str:
        """Get user's notes"""
        try:
            notes = await self.file_service.read_file(user_id, "notes.md")
            if not notes:
                return "📝 No notes found. Feel free to ask me to save something for you!"
            
            # Return last few lines
            lines = notes.strip().split('\n')
            recent_notes = lines[-5:] if len(lines) > 5 else lines
            
            return f"📚 Your recent notes:\n" + "\n".join(recent_notes)
            
        except Exception as e:
            return f"Error retrieving notes: {str(e)}"