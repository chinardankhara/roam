import streamlit as st
import asyncio
from ai_utils import ConversationManager
from typing import Dict, Any, List
from datetime import datetime

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

def format_datetime(dt_str: str) -> str:
    """Format datetime string to more readable format."""
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime("%I:%M %p, %b %d")  # e.g., "5:30 PM, Mar 02"

def display_direct_flight_results(results: Dict[str, Any]) -> None:
    """Display direct flight search results."""
    if "roundTrip" in results:
        st.subheader("✈️ Round-trip Flight Options")
        
        # Step 1: Display outbound flights in a more compact way
        st.markdown("### Select your outbound flight:")
        
        for departure in results["roundTrip"]["results"]:
            with st.expander(f"💰 ${departure['departureMinPrice']} · {len(departure['returnItineraries'])} return options"):
                # Display outbound flight details
                for segment in departure['departureItinerary']:
                    airline_name = AIRLINE_CODES.get(segment['airlineName'], segment['airlineName'])
                    st.markdown(f"""
                    <div style="padding: 10px; border-left: 3px solid #1E88E5; margin: 10px 0;">
                        <div style="font-size: 1.1em;">
                            {airline_name} {segment['flightNumber']}
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                            <div>
                                <div style="font-size: 1.2em; font-weight: bold;">{segment['departure']['airport']}</div>
                                <div>{format_datetime(segment['departure']['time'])}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.2em; font-weight: bold;">{segment['arrival']['airport']}</div>
                                <div>{format_datetime(segment['arrival']['time'])}</div>
                            </div>
                        </div>
                        <div style="color: #666;">
                            ⏱️ Duration: {segment['duration'] // 60}h {segment['duration'] % 60}m
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show return options
                st.markdown("### Return Options:")
                for return_option in departure['returnItineraries']:
                    with st.container():
                        st.markdown(f"""
                        <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                            <div style="font-size: 1.2em; color: #2E7D32;">
                                💰 Total price: ${return_option['totalPrice']}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        for segment in return_option['returnItinerary']:
                            airline_name = AIRLINE_CODES.get(segment['airlineName'], segment['airlineName'])
                            st.markdown(f"""
                            <div style="padding: 10px; border-left: 3px solid #2E7D32; margin: 10px 0;">
                                <div style="font-size: 1.1em;">
                                    {airline_name} {segment['flightNumber']}
                                </div>
                                <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                                    <div>
                                        <div style="font-size: 1.2em; font-weight: bold;">{segment['departure']['airport']}</div>
                                        <div>{format_datetime(segment['departure']['time'])}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 1.2em; font-weight: bold;">{segment['arrival']['airport']}</div>
                                        <div>{format_datetime(segment['arrival']['time'])}</div>
                                    </div>
                                </div>
                                <div style="color: #666;">
                                    ⏱️ Duration: {segment['duration'] // 60}h {segment['duration'] % 60}m
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.subheader("✈️ One-way Flight Options")
        for flight in results["oneWay"]["results"]:
            with st.expander(
                f"💰 ${flight['totalPrice']} - {flight['departureItinerary'][0]['departure']['airport']} → "
                f"{flight['departureItinerary'][-1]['arrival']['airport']}"
            ):
                for segment in flight['departureItinerary']:
                    airline_name = AIRLINE_CODES.get(segment['airlineName'], segment['airlineName'])
                    st.markdown(f"""
                    <div style="padding: 10px; border-left: 3px solid #1E88E5; margin: 10px 0;">
                        <div style="font-size: 1.1em; color: #1E88E5;">
                            {airline_name} {segment['flightNumber']}
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                            <div>
                                <div style="font-size: 1.2em; font-weight: bold;">{segment['departure']['airport']}</div>
                                <div>{format_datetime(segment['departure']['time'])}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.2em; font-weight: bold;">{segment['arrival']['airport']}</div>
                                <div>{format_datetime(segment['arrival']['time'])}</div>
                            </div>
                        </div>
                        <div style="color: #666;">
                            ⏱️ Duration: {segment['duration'] // 60}h {segment['duration'] % 60}m
                        </div>
                    </div>
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
            
            # Display appropriate results based on search type
            if hasattr(st.session_state.conversation_manager, '_search_completed'):
                if hasattr(st.session_state.conversation_manager, 'inspiration_results'):
                    display_inspiration_results(
                        st.session_state.conversation_manager.inspiration_results
                    )
                elif hasattr(st.session_state.conversation_manager, 'flight_results'):
                    display_direct_flight_results(
                        st.session_state.conversation_manager.flight_results
                    ) 