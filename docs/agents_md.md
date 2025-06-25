# Multi-Agent System Documentation

## Overview

The Multi-Agent POC Backend features three specialized AI agents, each powered by OpenAI's GPT-4o-mini and designed for specific domains.

## Agent Architecture

### Base Agent Class
All agents inherit from `BaseAgent` which provides:
- LLM integration for natural language processing
- File service for context storage
- Tool registration and execution
- Conversation history management
- Error handling and logging

### Message Flow
1. **Input** → User sends message via WebSocket
2. **Routing** → MessageRouter analyzes intent and selects agent
3. **Processing** → Selected agent processes message with LLM
4. **Tools** → Agent may execute tools (save data, retrieve history)
5. **Response** → Agent generates natural language response
6. **Storage** → Interaction logged to user context files

## Agent Profiles

### 🏋️ Helios - Fitness Agent

**Personality:** Energetic, motivating, safety-focused
**Domain:** Fitness, exercise, workouts, training

#### Capabilities
- **Workout Planning**: Create personalized exercise routines
- **Exercise Guidance**: Provide form tips and technique advice
- **Goal Setting**: Help users set and track fitness objectives
- **Progress Tracking**: Monitor workout history and improvements
- **Recovery Advice**: Suggest rest periods and flexibility work

#### Tools Available
| Tool | Purpose | Example |
|------|---------|---------|
| `save_workout` | Log completed workouts | Exercise type, sets, reps, duration |
| `get_workout_history` | Retrieve past workouts | Show last 5 workout sessions |
| `set_fitness_goal` | Set fitness objectives | "Build muscle", "Lose weight" |
| `get_user_fitness_data` | Access all fitness data | Complete fitness profile |

#### Trigger Keywords
- Primary: workout, exercise, gym, fitness, training
- Secondary: muscle, cardio, strength, run, lift, squat
- Advanced: crossfit, pilates, yoga, marathon, deadlift

#### Example Interactions
```
User: "I want to start working out but I'm a beginner"
Helios: "💪 Awesome! Starting your fitness journey is exciting! As a beginner, 
let's focus on building a solid foundation. I'd recommend starting with 
bodyweight exercises 2-3 times per week. What's your main goal - building 
strength, losing weight, or improving overall health?"

User: "Log my workout: 30 minutes running, 3 sets of pushups"
Helios: "🎯 Great job! I've logged your workout session. That's some solid 
cardio and strength work! How did you feel during the run? Keep up the 
excellent work - consistency is key! 💪"
```

#### Data Storage
Stores in `helios_data.json`:
- Workout history with exercises, sets, reps
- Fitness goals and target dates
- Personal preferences (equipment, time availability)
- Progress metrics and achievements

---

### 🥗 Ceres - Nutrition Agent

**Personality:** Warm, nurturing, science-based, inclusive
**Domain:** Nutrition, food, meals, diet planning

#### Capabilities
- **Meal Planning**: Create balanced, personalized meal plans
- **Nutritional Analysis**: Assess dietary intake and balance
- **Recipe Suggestions**: Recommend recipes based on preferences
- **Dietary Management**: Handle restrictions, allergies, special diets
- **Education**: Provide nutrition science and healthy eating tips

#### Tools Available
| Tool | Purpose | Example |
|------|---------|---------|
| `save_meal` | Log meals and nutrition | Breakfast items, calories, macros |
| `get_meal_history` | Retrieve eating patterns | Show recent meals and trends |
| `set_dietary_preference` | Store diet restrictions | Vegetarian, gluten-free, keto |
| `get_user_nutrition_data` | Access nutrition profile | Complete dietary history |

#### Trigger Keywords
- Primary: food, nutrition, meal, diet, recipe
- Secondary: eat, hungry, calories, protein, vitamins
- Advanced: vegetarian, keto, macros, supplements

#### Example Interactions
```
User: "What should I eat for breakfast?"
Ceres: "🌅 Good morning! For a nutritious breakfast, I'd suggest something 
with protein, healthy fats, and complex carbs. How about Greek yogurt with 
berries and granola, or avocado toast with eggs? Do you have any dietary 
preferences or restrictions I should know about?"

User: "I'm vegetarian and need high protein meals"
Ceres: "🌱 Perfect! There are so many delicious high-protein vegetarian 
options! Try lentil dal with quinoa, chickpea salad wraps, or tofu stir-fry. 
Beans, nuts, seeds, and dairy (if you eat it) are your protein powerhouses. 
Would you like me to create a weekly meal plan for you?"
```

#### Data Storage
Stores in `ceres_data.json`:
- Meal logs with foods, portions, timing
- Dietary preferences and restrictions
- Allergies and food sensitivities
- Nutrition goals (weight, health objectives)

---

### 🤖 General Assistant Agent

**Personality:** Friendly, helpful, informative, good at routing
**Domain:** General conversation, greetings, coordination

#### Capabilities
- **Conversation Management**: Handle greetings and general chat
- **Agent Routing**: Direct users to appropriate specialists
- **Note Taking**: Save reminders and general information
- **Information**: Provide general knowledge and explanations
- **Coordination**: Manage multi-agent interactions

#### Tools Available
| Tool | Purpose | Example |
|------|---------|---------|
| `save_note` | Store user notes | Reminders, preferences, goals |
| `get_notes` | Retrieve saved notes | Show recent notes and reminders |

#### Trigger Keywords
- Primary: hello, hi, help, what, how
- Secondary: general questions, greetings
- Fallback: Any unclear or non-specific requests

#### Example Interactions
```
User: "Hello! What can you help me with?"
General: "🤖 Hello there! I'm your AI assistant team coordinator. I work with 
two specialists: Helios 💪 (fitness & exercise) and Ceres 🥗 (nutrition & food). 
I can help with general questions, take notes, and direct you to the right 
expert. What would you like to explore today?"

User: "Can you save a note that I prefer morning workouts?"
General: "📝 Note saved! I'll remember that you prefer morning workouts. 
This could be helpful for Helios when creating your exercise schedule. 
Is there anything else you'd like me to remember about your preferences?"
```

#### Data Storage
Stores in `notes.md`:
- User preferences and reminders
- General notes and observations
- Cross-agent coordination information

## Message Routing System

### Routing Logic
1. **Explicit Mentions**: "@helios" or "@ceres" force direct routing
2. **Keyword Analysis**: Fast pattern matching for common terms
3. **LLM Classification**: Complex intent analysis for ambiguous messages
4. **Confidence Scoring**: Routes with confidence levels (0.0-1.0)

### Routing Examples
| Message | Routed To | Confidence | Reasoning |
|---------|-----------|------------|-----------|
| "I want to work out" | Helios | 0.95 | Clear fitness intent |
| "What should I eat?" | Ceres | 0.90 | Clear nutrition question |
| "Hello there!" | General | 0.95 | Greeting detected |
| "I need help getting healthier" | General | 0.60 | Ambiguous, needs clarification |

### Multi-Domain Handling
For requests spanning multiple domains:
```
User: "I want to lose weight - need both diet and exercise advice"
→ General Agent coordinates response:
"This sounds like you need both nutrition and fitness guidance! Let me 
connect you with both Ceres 🥗 for dietary advice and Helios 💪 for 
exercise planning. They'll work together to help you reach your goals!"
```

## Context Management

### Conversation Memory
- Each agent maintains conversation history
- Context shared between agents for same user
- LLM uses history for personalized responses
- Memory persists across sessions

### File-Based Storage
- Human-readable markdown logs
- Structured JSON data for agent tools
- Easy backup and data portability
- Transparent user data access

### Context Examples
```
User Context Directory:
user_contexts/demo-user/
├── conversations.md          # All conversations
├── helios_data.json         # Fitness data
├── ceres_data.json          # Nutrition data
├── notes.md                 # General notes
└── external_conversations.md # External interactions
```

## Extension and Customization

### Adding New Agents
1. Create agent class inheriting from `BaseAgent`
2. Define system prompt and personality
3. Register tools with `_register_tools()`
4. Add agent to router classification
5. Update main server routing logic

### Custom Tools
```python
async def custom_tool(self, user_id: str, args: Dict) -> str:
    """Custom tool implementation"""
    # Process arguments
    # Perform action
    # Save data if needed
    # Return success message
```

### Agent Personality Customization
Modify system prompts to change:
- Tone and communication style
- Expertise focus areas
- Response formats and structure
- Emoji usage and branding

## Performance Considerations

### Response Times
- Keyword routing: <10ms
- LLM classification: 200-1000ms
- Tool execution: 50-200ms
- File operations: <50ms

### Scaling Strategies
- Cache common LLM responses
- Implement agent response pooling
- Use faster models for routing
- Add Redis for session storage

### Memory Management
- Limit conversation history length
- Compress old context files
- Implement conversation summarization
- Clean up inactive sessions