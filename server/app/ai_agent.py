"""AI Agent service for driver assistance and recommendations."""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from pydantic import BaseModel

from app.models import DriverPreferences
from app.service import DataService


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None


class AIAgentService:
    """AI Agent service for driver assistance."""
    
    def __init__(self):
        """Initialize the AI Agent service."""
        self.data_service = DataService()
        # Initialize Gemini client
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            # Use a supported model (gemini-2.5-flash is available and fast)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
    def _get_system_prompt(self, driver_preferences: Optional[DriverPreferences] = None) -> str:
        """Get the system prompt for the AI agent."""
        base_prompt = """You are a helpful AI assistant for a ride-sharing driver using the Uber app. Your goal is to provide concise, actionable advice to help them maximize their earnings, improve their ratings, and manage their well-being.

Keep your responses short and to the point. The driver is likely busy and needs quick answers.

You have access to real-time data about:
- Current surge patterns and pricing
- Weather conditions affecting demand
- Historical performance data
- Zone recommendations
- Driver preferences and work patterns

Example topics you can help with:
- Best times/locations to drive based on current data
- Strategies for getting more tips
- Dealing with difficult passengers
- Vehicle maintenance reminders
- Promoting driver safety and wellness (e.g., taking breaks)
- Zone recommendations based on surge and demand patterns
- Weather-based driving advice
"""
        
        if driver_preferences:
            base_prompt += f"""

Driver Context:
- Preferred working hours: {driver_preferences.preferred_start_time} - {driver_preferences.preferred_end_time}
- Preferred city/area: {driver_preferences.preferred_city}
- Break preferences: {driver_preferences.break_duration_minutes} minutes
- Vehicle type: {getattr(driver_preferences, 'vehicle_type', 'Not specified')}
"""
        
        return base_prompt
    
    async def get_driver_context(self, driver_id: str) -> Dict[str, Any]:
        """Get relevant context about the driver for the AI agent."""
        try:
            # Get driver preferences
            driver_prefs = await self.data_service.get_driver_preferences(driver_id)
            
            # Get recent performance data
            recent_trips = await self.data_service.get_recent_completed_trips(driver_id, limit=10)
            
            # Get current surge data
            current_surge = await self.data_service.get_current_surge_data()
            
            # Get weather data
            current_weather = await self.data_service.get_current_weather()
            
            context = {
                "driver_preferences": driver_prefs.model_dump() if driver_prefs else None,
                "recent_trips_count": len(recent_trips),
                "current_surge_zones": len(current_surge) if current_surge else 0,
                "weather_conditions": current_weather.get("conditions") if current_weather else "Unknown"
            }
            
            return context
            
        except Exception as e:
            # Return minimal context if there's an error
            return {"error": f"Could not fetch driver context: {str(e)}"}
    
    async def chat(
        self, 
        driver_id: str,
        message: str, 
        chat_history: List[ChatMessage] = None
    ) -> str:
        """Process a chat message and return AI response."""
        
        if chat_history is None:
            chat_history = []
        
        try:
            # Get driver context
            driver_context = await self.get_driver_context(driver_id)
            driver_prefs = None
            
            if "driver_preferences" in driver_context and driver_context["driver_preferences"]:
                # Convert dict back to DriverPreferences if available
                from app.models import DriverPreferences
                driver_prefs = DriverPreferences(**driver_context["driver_preferences"])
            
            # Build system prompt with context
            system_prompt = self._get_system_prompt(driver_prefs)
            
            if driver_context and "error" not in driver_context:
                system_prompt += f"""

Current Context:
- Recent trips completed: {driver_context.get('recent_trips_count', 0)}
- Active surge zones: {driver_context.get('current_surge_zones', 0)}
- Weather: {driver_context.get('weather_conditions', 'Unknown')}
"""
            
            # Prepare the conversation for Gemini
            conversation_parts = [system_prompt]
            
            # Add chat history
            for msg in chat_history:
                if msg.role == "user":
                    conversation_parts.append(f"USER: {msg.content}")
                else:
                    conversation_parts.append(f"ASSISTANT: {msg.content}")
            
            # Add current user message
            conversation_parts.append(f"USER: {message}")
            conversation_parts.append("ASSISTANT:")
            
            # Combine into a single prompt
            full_prompt = "\n\n".join(conversation_parts)
            
            # Call Gemini API
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )
            
            # Handle response safely
            if response.parts:
                return response.text
            else:
                return "I understand you're looking for driving advice. Let me help you with some tips: Focus on peak hours (7-9 AM, 5-7 PM), keep your car clean, be friendly to passengers, and check surge areas regularly. Stay safe and drive smart!"
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")  # For debugging
            return f"Sorry, I'm having trouble connecting to the AI service right now. Please try again later."
    
    async def get_proactive_suggestions(self, driver_id: str) -> List[str]:
        """Get proactive suggestions for the driver based on current conditions."""
        
        try:
            context = await self.get_driver_context(driver_id)
            
            suggestions = []
            
            # Check surge patterns
            if context.get("current_surge_zones", 0) > 0:
                suggestions.append("🔥 High surge areas detected! Check the map for best zones.")
            
            # Weather-based suggestions
            weather = context.get("weather_conditions", "").lower()
            if "rain" in weather:
                suggestions.append("☔ Rainy weather increases demand - consider staying online longer.")
            elif "snow" in weather:
                suggestions.append("❄️ Snowy conditions - drive safely and expect higher demand.")
            
            # Time-based suggestions
            current_hour = datetime.now().hour
            if 7 <= current_hour <= 9:
                suggestions.append("🌅 Morning rush hour - airports and business districts are busy.")
            elif 17 <= current_hour <= 19:
                suggestions.append("🌆 Evening rush hour - great time for rides to transit hubs.")
            elif 22 <= current_hour or current_hour <= 3:
                suggestions.append("🌙 Late night - focus on entertainment districts and airports.")
            
            # Recent performance
            recent_trips = context.get("recent_trips_count", 0)
            if recent_trips == 0:
                suggestions.append("🚗 Ready to start your day? Check zone recommendations first!")
            elif recent_trips >= 5:
                suggestions.append("⭐ Great work today! Consider taking a break if you're feeling tired.")
            
            return suggestions[:3]  # Return max 3 suggestions
            
        except Exception:
            return ["Welcome! I'm here to help you maximize your earnings today."]
    
    async def generate_wellness_reminder(self, driver_id: str, hours_driven: float) -> Optional[str]:
        """Generate a wellness reminder based on driving time."""
        
        if hours_driven >= 0.05:
            driver_context = await self.get_driver_context(driver_id)
            driver_name = "Driver"
            
            if (driver_context.get("driver_preferences") and 
                driver_context["driver_preferences"].get("preferred_name")):
                driver_name = driver_context["driver_preferences"]["preferred_name"]
            
            return f"Hey {driver_name}, you've been driving for {hours_driven:.1f} hours now. Time for a well-deserved break! Consider taking 15-30 minutes to recharge. Would you like some suggestions for how to spend your break time?"
        
        return None