import asyncio
from ai_utils import ConversationManager
import os
from openai import OpenAI

async def chat_session():
    manager = ConversationManager()
    print("Flight Booking Assistant (type 'quit' to exit)")
    print("What would you like to do? Book a specific flight or get travel inspiration?")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == 'quit':
            break
            
        try:
            print(1)
            response = await manager.process_message(user_input)
            print(2)
            print(f"\nAssistant: {response}")
            
            # Optional: Print current state for debugging
            if manager.current_state:
                print("\nCurrent State:", manager.current_state.__dict__)
            print(3)  
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(chat_session()) 