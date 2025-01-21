from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from booking_utils import get_flight_inspiration, get_flights
from datetime import datetime

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_prompt(prompt_type: str, **kwargs) -> str:
    # Use os.path.join for cross-platform compatibility
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts.json")
    with open(prompt_path, "r") as f:
        prompts = json.load(f)
    
    if isinstance(prompts[prompt_type], dict):
        prompt = prompts[prompt_type]["system"]
    else:
        prompt = prompts[prompt_type]
    
    # Replace any placeholders in the prompt with provided kwargs
    for key, value in kwargs.items():
        placeholder = "{" + key + "}"
        if placeholder in prompt:
            prompt = prompt.replace(placeholder, str(value))
    
    prompt += f"\nCurrent date and time: {datetime.now().isoformat()}"
    return prompt

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
        print(f"\nProcessing message: {message}")
        
        # 1. If no intent, classify intent
        if self.current_intent == Intent.UNKNOWN:
            print("Classifying intent...")
            self.current_intent = await self._classify_intent(message)
            print(f"Classified intent: {self.current_intent}")
            self.current_state = self._create_state_for_intent()
        
        # 2. Update state based on message
        await self._update_state(message)
        print(4)
        # 3. Generate response based on current state
        response = await self._generate_response()
        print(5)
        # 4. Update history
        self._update_history(message, response)
        
        return response
    
    async def _classify_intent(self, message: str) -> Intent:
        """Use GPT-4 to classify user intent from their message."""
        try:
            response = await client.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": load_prompt("intent")},
                    {"role": "user", "content": message}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content
            intent_str = json.loads(result)["intent"].lower()
            return Intent(intent_str)
        except (ValueError, KeyError, json.JSONDecodeError):
            return Intent.UNKNOWN
        
    def _create_state_for_intent(self) -> ConversationState:
        if self.current_intent == Intent.DIRECT_FLIGHT:
            return DirectFlightState()
        elif self.current_intent == Intent.INSPIRATION:
            return InspirationState()
        return None
    
    async def _update_state(self, message: str) -> None:
        """Extract relevant information from user message and update state."""
        try:
            print("Debug: Starting _update_state")
            if self.current_state is None:
                print("Debug: No current state")
                return
            
            print("Debug: Current state:", self.current_state.__dict__)
            
            messages = [
                {
                    "role": "system", 
                    "content": load_prompt(
                        "state_update",
                        intent=self.current_intent.value,
                        state=json.dumps(self.current_state.__dict__)
                    )
                },
                {
                    "role": "user",
                    "content": f"User message: {message}"
                }
            ]
            
            response = await client.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=messages,
                temperature=0
            )
            
            content = response.choices[0].message.content
            print("Debug: Response content:", content)
            
            extracted_info = json.loads(content)
            print("Debug: Parsed JSON:", extracted_info)
            
            # Clean up and validate values before updating state
            if 'origin' in extracted_info:
                if extracted_info['origin'].upper() == 'ATLANTA':
                    extracted_info['origin'] = 'ATL'
                if extracted_info['origin'].upper() == 'BOSTON':
                    extracted_info['origin'] = 'BOS'
            
            if 'destination' in extracted_info:
                if extracted_info['destination'].upper() == 'ATLANTA':
                    extracted_info['destination'] = 'ATL'
                if extracted_info['destination'].upper() == 'BOSTON':
                    extracted_info['destination'] = 'BOS'
            
            # Update state with cleaned values
            for key, value in extracted_info.items():
                if value is not None and not isinstance(value, str):
                    self.current_state.update(key, value)
                elif isinstance(value, str) and not any(placeholder in value.upper() for placeholder in ["IATA CODE", "YYYY-MM-DD"]):
                    self.current_state.update(key, value)

            # Check completion based on intent
            if self.current_intent == Intent.DIRECT_FLIGHT:
                if all(getattr(self.current_state, field) is not None 
                      for field in ['origin', 'destination', 'departure_date']):
                    await self._search_direct_flights()
            elif self.current_intent == Intent.INSPIRATION:
                if all(getattr(self.current_state, field) is not None 
                      for field in ['origin', 'date_range', 'duration', 'max_price']):
                    await self._search_inspiration()
                
        except Exception as e:
            print(f"Error updating state: {str(e)}")
            import traceback
            print(traceback.format_exc())

    async def _search_direct_flights(self) -> None:
        """Search for direct flights using the flight API."""
        try:
            results = await get_flights(
                origin=self.current_state.origin,
                destination=self.current_state.destination,
                departure_date=self.current_state.departure_date,
                return_date=self.current_state.return_date,
                adults=self.current_state.passengers,
                travel_class=self.current_state.travel_class
            )
            print("\nFound flight options:")
            for flight in results["flights"]:
                print(f"- {flight}")
        except Exception as e:
            print(f"Error searching flights: {str(e)}")

    async def _search_inspiration(self) -> None:
        """Search for flight inspiration."""
        try:
            results = await get_flight_inspiration(
                origin=self.current_state.origin,
                departure_date=self.current_state.date_range,
                duration=self.current_state.duration,
                max_price=self.current_state.max_price
            )
            print("\nFound flight options:")
            for result in results:
                print(f"- {result['destination']}: ${result['price']} ({result['departureDate']} to {result['returnDate']})")
            self._search_completed = True  # Mark that we've completed the search
        except Exception as e:
            print(f"Error searching flights: {str(e)}")

    async def _generate_response(self) -> str:
        """Generate appropriate response based on current state."""
        if not self.current_state:
            return "I'm not sure what you're looking for. Can you please clarify if you want to book a specific flight or get travel suggestions?"

        # If we've already searched and found results, don't generate a chatty response
        if hasattr(self, '_search_completed') and self._search_completed:
            return ""  # Return empty string to avoid additional messages after showing results

        state_dict = {key: getattr(self.current_state, key) 
                     for key in self.current_state.__annotations__}
        
        try:
            raw_prompt = load_prompt("response_generation")
            messages = [
                {"role": "system", "content": raw_prompt},
                {"role": "user", "content": f"Current intent: {self.current_intent.value}\nCurrent state: {json.dumps(state_dict)}\nGenerate response"}
            ]
            
            response = await client.chat.completions.create(
                model="gpt-4-1106-preview",
                response_format={"type": "json_object"},
                messages=messages,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("response", "I'm having trouble understanding. Could you please provide more details?")
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I'm having trouble processing your request. Could you please rephrase it?"

    def _update_history(self, message: str, response: str) -> None:
        self.history.append({
            "user": message,
            "assistant": response,
            "intent": self.current_intent.value,
            "state": self.current_state.__dict__ if self.current_state else None
        })
