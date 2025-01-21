from typing import Dict, Any
from datetime import datetime

def format_datetime(dt_str: str) -> str:
    """Format datetime string to more readable format."""
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime("%I:%M %p, %b %d")  # e.g., "5:30 PM, Mar 02"

def get_flight_segment_html(segment: Dict[str, Any], airline_name: str, color: str = "#1E88E5") -> str:
    """Generate HTML for a flight segment."""
    return f"""
    <div style="padding: 10px; border-left: 3px solid {color}; margin: 10px 0;">
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
    """

def get_inspiration_card_html(flight: Dict[str, Any]) -> str:
    """Generate HTML for an inspiration result card."""
    return f"""
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
    """ 