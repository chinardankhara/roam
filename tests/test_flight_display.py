import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any

# Airline codes mapping
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
        
        # Display departure options first
        for departure in results["roundTrip"]["results"]:
            with st.expander(
                f"💰 ${departure['departureMinPrice']} - {departure['departureItinerary'][0]['departure']['airport']} → "
                f"{departure['departureItinerary'][-1]['arrival']['airport']}"
            ):
                st.markdown("### Outbound Flight")
                for segment in departure['departureItinerary']:
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
                
                st.markdown(f"### Return Options ({departure['returnCount']} flights)")
                for return_option in departure['returnItineraries']:
                    st.markdown(f"#### 💰 ${return_option['totalPrice']}")
                    for segment in return_option['returnItinerary']:
                        airline_name = AIRLINE_CODES.get(segment['airlineName'], segment['airlineName'])
                        st.markdown(f"""
                        <div style="padding: 10px; border-left: 3px solid #2E7D32; margin: 10px 0;">
                            <div style="font-size: 1.1em; color: #2E7D32;">
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

# Sample data for testing
one_way_data = {
    "oneWay": {
        "results": [
            {
                "totalPrice": "399.52",
                "departureItinerary": [
                    {
                        "airlineName": "VS",
                        "flightNumber": "22",
                        "departure": {
                            "airport": "IAD",
                            "time": "2025-03-02T18:25:00"
                        },
                        "arrival": {
                            "airport": "LHR",
                            "time": "2025-03-03T06:55:00"
                        },
                        "duration": 450
                    }
                ]
            },
            {
                "totalPrice": "404.58",
                "departureItinerary": [
                    {
                        "airlineName": "VS",
                        "flightNumber": "7120",
                        "departure": {
                            "airport": "IAD",
                            "time": "2025-03-02T17:35:00"
                        },
                        "arrival": {
                            "airport": "AMS",
                            "time": "2025-03-03T07:05:00"
                        },
                        "duration": 450
                    },
                    {
                        "airlineName": "VS",
                        "flightNumber": "7064",
                        "departure": {
                            "airport": "AMS",
                            "time": "2025-03-03T16:40:00"
                        },
                        "arrival": {
                            "airport": "LHR",
                            "time": "2025-03-03T17:00:00"
                        },
                        "duration": 80
                    }
                ]
            }
        ]
    }
}

round_trip_data = {
    "roundTrip": {
        "results": [
            {
                "departureMinPrice": "399.52",
                "departureItinerary": [
                    {
                        "airlineName": "VS",
                        "flightNumber": "22",
                        "departure": {
                            "airport": "IAD",
                            "time": "2025-03-02T18:25:00"
                        },
                        "arrival": {
                            "airport": "LHR",
                            "time": "2025-03-03T06:55:00"
                        },
                        "duration": 450
                    }
                ],
                "returnCount": 2,
                "returnItineraries": [
                    {
                        "totalPrice": "799.04",
                        "returnItinerary": [
                            {
                                "airlineName": "VS",
                                "flightNumber": "21",
                                "departure": {
                                    "airport": "LHR",
                                    "time": "2025-03-10T11:35:00"
                                },
                                "arrival": {
                                    "airport": "IAD",
                                    "time": "2025-03-10T15:35:00"
                                },
                                "duration": 480
                            }
                        ]
                    },
                    {
                        "totalPrice": "809.16",
                        "returnItinerary": [
                            {
                                "airlineName": "VS",
                                "flightNumber": "25",
                                "departure": {
                                    "airport": "LHR",
                                    "time": "2025-03-10T17:35:00"
                                },
                                "arrival": {
                                    "airport": "IAD",
                                    "time": "2025-03-10T21:35:00"
                                },
                                "duration": 480
                            }
                        ]
                    }
                ]
            }
        ]
    }
}

st.title("Flight Display Test")

tab1, tab2 = st.tabs(["One-way Flights", "Round-trip Flights"])

with tab1:
    display_direct_flight_results(one_way_data)
    
with tab2:
    display_direct_flight_results(round_trip_data)