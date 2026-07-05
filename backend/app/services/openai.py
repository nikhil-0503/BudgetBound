import os
from typing import List, Dict, Any

class AITravelService:
    """
    Interface boundary for future OpenAI/LLM integration.
    Currently runs in mock mode returning the service integration status.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.is_connected = bool(self.api_key)

    def verify_connection(self):
        if not self.is_connected:
            raise NotImplementedError("AI service not connected yet. This feature will be available after API integration.")

    async def regenerate_trip(self, trip_id: int, user_instruction: str) -> Dict[str, Any]:
        """
        Regenerates a trip itinerary based on natural language instructions (e.g. 'Make it more historical' or 'Avoid walking').
        """
        self.verify_connection()
        # Future OpenAI API call logic goes here
        return {"status": "success"}

    async def explain_budget_choices(self, trip_id: int) -> Dict[str, Any]:
        """
        Provides natural language reasoning for the budget decisions made (e.g. 'Why is flight cost high?' or 'Why was Gokarna selected?').
        """
        self.verify_connection()
        return {"status": "success"}

    async def chat_assistant(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Interactive chat companion helping users pick states, adjust dining habits, or find hidden tourist spots.
        """
        self.verify_connection()
        return {"status": "success"}

    async def generate_personalized_plan(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fully custom planner generating itineraries without standard seed boundaries.
        """
        self.verify_connection()
        return {"status": "success"}

ai_travel_service = AITravelService()
