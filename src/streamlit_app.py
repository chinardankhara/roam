import streamlit as st
import asyncio
from ai_utils import ConversationManager
from typing import Dict, Any, List

# Custom CSS for the reset button
st.markdown("""
    <style>
    .stButton button {
        width: 150px;
        background-color: #FF4B4B;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #FF3333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

def display_inspiration_results(results: List[Dict[str, Any]]) -> None:
    """Display flight inspiration results in a grid of cards."""
    st.subheader("✈️ Flight Inspiration Results")
    
    # Sort results by price
    sorted_results = sorted(results, key=lambda x: float(x['price']))
    
    # Create rows of 3 cards each
    cols_per_row = 3
    for i in range(0, len(sorted_results), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(sorted_results):
                flight = sorted_results[i + j]
                with col:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                border: 1px solid #e0e0e0;
                                border-radius: 10px;
                                padding: 15px;
                                margin: 5px;
                                background-color: white;
                            ">
                                <h3 style="color: #1E88E5;">{flight['destination']}</h3>
                                <p style="font-size: 24px; color: #2E7D32; margin: 10px 0;">
                                    ${flight['price']}
                                </p>
                                <p style="color: #666;">
                                    🛫 {flight['departureDate']}<br>
                                    🛬 {flight['returnDate']}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

# Initialize session state
if "conversation_manager" not in st.session_state:
    st.session_state.conversation_manager = ConversationManager()
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header with title and reset button
header_col1, header_col2 = st.columns([6, 1])
with header_col1:
    st.title("✈️ Flight Booking Assistant")
with header_col2:
    if st.button("🔄 Reset Chat"):
        st.session_state.conversation_manager = ConversationManager()
        st.session_state.messages = []
        st.experimental_rerun()

# Chat input
user_input = st.chat_input("Type your message here...")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Process new messages
if user_input:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = asyncio.run(
                st.session_state.conversation_manager.process_message(user_input)
            )
            
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write(response)
            
            # Display flight inspiration results after the response text
            if hasattr(st.session_state.conversation_manager, '_search_completed'):
                display_inspiration_results(
                    st.session_state.conversation_manager.inspiration_results
                ) 