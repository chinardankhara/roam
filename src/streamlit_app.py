import streamlit as st
import asyncio
from ai_utils import ConversationManager
from typing import Dict, Any, List
from datetime import datetime
from templates.styles import RESET_BUTTON_CSS
from templates.flight_cards import (
    get_flight_segment_html,
    get_inspiration_card_html,
    format_datetime
)
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Apply CSS
st.markdown(RESET_BUTTON_CSS, unsafe_allow_html=True)

# Add airline codes mapping
AIRLINE_CODES = {
    "AR": "Aerolineas Argentinas",
    "AM": "Aeromexico",
    "UX": "Air Europa",
    "AF": "Air France",
    "CI": "China Airlines",
    "MU": "China Eastern Airlines",
    "OK": "Czech Airlines",
    "DL": "Delta Air Lines",
    "GA": "Garuda Indonesia",
    "AZ": "ITA Airways",
    "KQ": "Kenya Airways",
    "KL": "KLM Royal Dutch Airlines",
    "KE": "Korean Air",
    "ME": "Middle East Airlines",
    "SV": "Saudi Arabian Airlines",
    "SK": "SAS Scandinavian Airlines",
    "RO": "TAROM",
    "VN": "Vietnam Airlines",
    "VS": "Virgin Atlantic",
    "MF": "Xiamen Airlines"
}

def display_direct_flight_results(results: Dict[str, Any]) -> None:
    """Display direct flight search results."""
    if "roundTrip" in results:
        st.subheader("✈️ Round-trip Flight Options")
        
        for departure in results["roundTrip"]["results"]:
            with st.expander(f"💰 ${departure['departureMinPrice']} · {len(departure['returnItineraries'])} return options"):
                # Display outbound flight details
                for segment in departure['departureItinerary']:
                    airline_name = AIRLINE_CODES.get(segment['airlineName'], segment['airlineName'])
                    st.markdown(
                        get_flight_segment_html(segment, airline_name, "#1E88E5"),
                        unsafe_allow_html=True
                    )
                
                # Show return options
                st.markdown("### Return Options:")
                for return_option in departure['returnItineraries']:
                    st.markdown(f"""
                    <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                        <div style="font-size: 1.2em; color: #2E7D32;">
                            💰 Total price: ${return_option['totalPrice']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    for segment in return_option['returnItinerary']:
                        airline_name = AIRLINE_CODES.get(segment['airlineName'], segment['airlineName'])
                        st.markdown(
                            get_flight_segment_html(segment, airline_name, "#2E7D32"),
                            unsafe_allow_html=True
                        )
                    st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.subheader("✈️ One-way Flight Options")
        for result in results["oneWay"]["results"]:
            with st.expander(f"💰 ${result['totalPrice']}"):
                for segment in result['departureItinerary']:
                    airline_name = AIRLINE_CODES.get(segment['airlineName'], segment['airlineName'])
                    st.markdown(
                        get_flight_segment_html(segment, airline_name, "#1E88E5"),
                        unsafe_allow_html=True
                    )

def display_inspiration_results(results: List[Dict[str, Any]]) -> None:
    """Display flight inspiration results in a grid of cards."""
    st.subheader("✈️ Flight Inspiration Results")
    sorted_results = sorted(results, key=lambda x: float(x['price']))
    
    cols_per_row = 3
    for i in range(0, len(sorted_results), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(sorted_results):
                with col:
                    with st.container():
                        st.markdown(
                            get_inspiration_card_html(sorted_results[i + j]),
                            unsafe_allow_html=True
                        )

# Initialize session state
if "conversation_manager" not in st.session_state:
    st.session_state.conversation_manager = ConversationManager()
if "messages" not in st.session_state:
    st.session_state.messages = []

# Simple title without reset button
st.title("✈️ Delta Tailwind")

# Add chat input
user_input = st.chat_input("How can I assist you with your travel plans today?")

# Display chat history and handle new messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = asyncio.run(
                st.session_state.conversation_manager.process_message(user_input)
            )
            
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.markdown(response)
            
            if hasattr(st.session_state.conversation_manager, '_search_completed'):
                if hasattr(st.session_state.conversation_manager, 'inspiration_results'):
                    display_inspiration_results(
                        st.session_state.conversation_manager.inspiration_results
                    )
                elif hasattr(st.session_state.conversation_manager, 'flight_results'):
                    display_direct_flight_results(
                        st.session_state.conversation_manager.flight_results
                    ) 