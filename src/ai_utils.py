from typing import TypeVar, Generic, Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import openai
import json

# Intent Classification
class Intent(Enum):
    UNKNOWN = "unknown"
    DIRECT_FLIGHT = "direct_flight"
    INSPIRATION = "inspiration"

# Base State Management
class ConversationState(ABC):
    @abstractmethod
    def update(self, key: str, value: Any) -> None: pass
    
    @abstractmethod
    def get(self, key: str) -> Any: pass
    
    @abstractmethod
    def is_complete(self) -> bool: pass

@dataclass
class DirectFlightState(ConversationState):
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    passengers: int = 1
    travel_class: str = "ECONOMY"
    
    def update(self, key: str, value: Any) -> None:
        setattr(self, key, value)
    
    def get(self, key: str) -> Any:
        return getattr(self, key)
    
    def is_complete(self) -> bool:
        return all([self.origin, self.destination, self.departure_date])

@dataclass
class InspirationState(ConversationState):
    origin: Optional[str] = None
    date_range: Optional[tuple] = None
    duration: Optional[int] = None
    max_price: Optional[int] = None
    
    def update(self, key: str, value: Any) -> None:
        setattr(self, key, value)
    
    def get(self, key: str) -> Any:
        return getattr(self, key)
    
    def is_complete(self) -> bool:
        return all([self.origin, self.date_range, self.duration])

# Conversation Manager
class ConversationManager:
    def __init__(self):
        self.history: List[Dict] = []
        self.current_intent: Intent = Intent.UNKNOWN
        self.current_state: Optional[ConversationState] = None
    
    async def process_message(self, message: str) -> str:
        # 1. If no intent, classify intent
        if self.current_intent == Intent.UNKNOWN:
            self.current_intent = await self._classify_intent(message)
            self.current_state = self._create_state_for_intent()
        
        # 2. Update state based on message
        await self._update_state(message)
        
        # 3. Generate response based on current state
        response = await self._generate_response()
        
        # 4. Update history
        self._update_history(message, response)
        
        return response
    
    async def classify_intent(message: str) -> Intent:
        """
        Use GPT-4 to classify user intent from their message.
        Returns a specific Intent enum value.
        """
        system_prompt = """You are a flight booking assistant. Classify the user's intent.
        
        Return a JSON object with a single field:
        {
            "intent": "direct_flight" | "inspiration" | "unknown"
        }
        
        Where:
        - direct_flight: User wants to book a specific flight between locations
        - inspiration: User wants suggestions for where to travel from a particular origin airport
        - unknown: Can't determine the intent"""

        try:
            response = await openai.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content
            intent_str = json.loads(result)["intent"]
            return Intent(intent_str)
        except (ValueError, KeyError, json.JSONDecodeError):
            return Intent.UNKNOWN
        
    def _create_state_for_intent(self) -> ConversationState:
        if self.current_intent == Intent.DIRECT_FLIGHT:
            return DirectFlightState()
        elif self.current_intent == Intent.INSPIRATION:
            return InspirationState()
        # Add more states as needed
    
    async def _update_state(self, message: str) -> None:
        """Extract relevant information from user message and update state."""
        system_prompt = f"""You are a flight booking assistant. Extract relevant information from the user message.
        Current intent: {self.current_intent.value}
        
        Return a JSON object with any of these fields that are mentioned (only include fields that are explicitly mentioned):
        
        For direct_flight:
        {{
            "origin": "IATA code",
            "destination": "IATA code",
            "departure_date": "YYYY-MM-DD",
            "return_date": "YYYY-MM-DD",  # Optional - omit for one-way flights
            "passengers": number,
            "travel_class": "ECONOMY" | "BUSINESS" | "FIRST"
        }}
        
        For inspiration:
        {{
            "origin": "IATA code",
            "date_range": ["YYYY-MM-DD", "YYYY-MM-DD"],  # If user provides single date, use same date twice
            "duration": number,
            "max_price": number
        }}
        
        Notes:
        - For direct flights, return_date is optional. Omit it for one-way flights.
        - For inspiration search, date_range is inclusive. If user mentions only one date, use it as both start and end date.
        - Always convert dates to YYYY-MM-DD format.
        - Always convert airport names to IATA codes."""

        try:
            response = await openai.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0
            )
            
            extracted_info = json.loads(response.choices[0].message.content)
            
            # Update state with extracted information
            for key, value in extracted_info.items():
                self.current_state.update(key, value)
                
        except Exception as e:
            print(f"Error updating state: {e}")

    async def _generate_response(self) -> str:
        """Generate appropriate response based on current state."""
        if not self.current_state:
            return "I'm not sure what you're looking for. Can you please clarify if you want to book a specific flight or get travel suggestions?"

        # Create a summary of the current state
        state_dict = {key: getattr(self.current_state, key) 
                     for key in self.current_state.__annotations__}
        
        system_prompt = f"""You are a helpful flight booking assistant.
        Current intent: {self.current_intent.value}
        Current state: {json.dumps(state_dict)}
        
        If the state is complete, summarize the search criteria and indicate you'll search for flights.
        If the state is incomplete, ask for the missing required information in a natural, conversational way.
        
        Return a JSON object:
        {{
            "response": "your response message",
            "state_complete": boolean
        }}"""

        try:
            response = await openai.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate response"}
                ],
                temperature=0.7  # Slightly higher for more natural responses
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # If state is complete, perform the search
            if result["state_complete"] and self.current_state.is_complete():
                if self.current_intent == Intent.DIRECT_FLIGHT:
                    # Call direct flight search
                    pass
                elif self.current_intent == Intent.INSPIRATION:
                    # Call inspiration search
                    pass
            
            return result["response"]
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm having trouble processing your request. Could you please rephrase it?"

    def _update_history(self, message: str, response: str) -> None:
        self.history.append({
            "user": message,
            "assistant": response,
            "intent": self.current_intent.value,
            "state": self.current_state.__dict__ if self.current_state else None
        })
