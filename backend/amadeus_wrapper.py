from typing import Dict, List, Optional, Union, Literal
import os
from datetime import date
import httpx
from dotenv import load_dotenv
import json

load_dotenv()

TravelClass = Literal["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]
FlightResult = Dict[str, Union[Dict, List, str, int, float]]

async def get_amadeus_token() -> str:
    """Get authentication token from Amadeus API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://test.api.amadeus.com/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": os.getenv("AMADEUS_API_KEY"),
                    "client_secret": os.getenv("AMADEUS_API_SECRET")
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            return response.json()["access_token"]
    except httpx.HTTPError as error:
        print(f"Error getting Amadeus token: {error.response.json() if error.response else error}")
        raise ValueError("Failed to authenticate with Amadeus API")

async def get_flights(
    origin: str,
    destination: str,
    departure_date: Union[str, date],
    return_date: Optional[Union[str, date]] = None,
    adults: int = 1,
    travel_class: TravelClass = "ECONOMY"
) -> FlightResult:
    """Get flights from Amadeus API with specified parameters."""
    
    # Validate inputs
    if not (1 <= adults <= 9):
        raise ValueError("Adults must be between 1 and 9.")

    valid_classes = ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]
    if travel_class not in valid_classes:
        raise ValueError(f"Invalid travel class. Choose one of: {', '.join(valid_classes)}")

    # Convert dates to strings if they're date objects
    if isinstance(departure_date, date):
        departure_date = departure_date.isoformat()
    if isinstance(return_date, date):
        return_date = return_date.isoformat()

    token = await get_amadeus_token()
    skyteam_airlines = "AR,AM,UX,AF,CI,MU,OK,DL,GA,AZ,KQ,KL,KE,ME,SV,SK,RO,VN,VS,MF"
    max_results = 100 if return_date else 20

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # Set 30-second timeout
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "travelClass": travel_class,
                "includedAirlineCodes": skyteam_airlines,
                "max": max_results,
            }
            if return_date:  # Only include returnDate if it's provided
                params["returnDate"] = return_date

            response = await client.get(
                "https://test.api.amadeus.com/v2/shopping/flight-offers",
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()

        return {"flights": process_flights(data["data"], bool(return_date))}

    except httpx.TimeoutException as error:
        print(f"Request timed out: {error}")
        raise ValueError("Request timed out. Please try again later.")
    except httpx.HTTPStatusError as error:
        print(f"HTTP error occurred: {error.response.json() if error.response else error}")
        raise ValueError("Failed to fetch flights. Please try again later.")
    except httpx.HTTPError as error:
        print(f"Error fetching flight data: {error}")
        raise ValueError("Failed to fetch flights. Please try again later.")

def convert_duration_to_minutes(duration: str) -> int:
    """Convert ISO 8601 duration to minutes."""
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    return hours * 60 + minutes 

def process_flights(flights_data: List[Dict], is_round_trip: bool) -> Dict:
    """Process flight data from Amadeus API response."""
    if not is_round_trip:
        one_way_flights = [
            {
                "departureItinerary": [
                    {
                        "airlineName": segment["carrierCode"],
                        "flightNumber": segment["number"],
                        "departure": {
                            "airport": segment["departure"]["iataCode"],
                            "time": segment["departure"]["at"]
                        },
                        "arrival": {
                            "airport": segment["arrival"]["iataCode"],
                            "time": segment["arrival"]["at"]
                        },
                        "duration": convert_duration_to_minutes(segment["duration"])
                    }
                    for segment in flight["itineraries"][0]["segments"]
                ],
                "totalPrice": flight["price"]["grandTotal"],
                "currency": flight["price"]["currency"]
            }
            for flight in flights_data
        ]
        
        return {
            "oneWay": {
                "results": one_way_flights,
                "count": len(one_way_flights)
            }
        }
    
    flights_map: Dict[str, Dict] = {}
    
    for flight in flights_data:
        departure_itinerary = [
            {
                "airlineName": segment["carrierCode"],
                "flightNumber": segment["number"],
                "departure": {
                    "airport": segment["departure"]["iataCode"],
                    "time": segment["departure"]["at"]
                },
                "arrival": {
                    "airport": segment["arrival"]["iataCode"],
                    "time": segment["arrival"]["at"]
                },
                "duration": convert_duration_to_minutes(segment["duration"])
            }
            for segment in flight["itineraries"][0]["segments"]
        ]
        
        departure_key = json.dumps(departure_itinerary)
        total_price = float(flight["price"]["grandTotal"])
        
        return_itinerary = [
            {
                "airlineName": segment["carrierCode"],
                "flightNumber": segment["number"],
                "departure": {
                    "airport": segment["departure"]["iataCode"],
                    "time": segment["departure"]["at"]
                },
                "arrival": {
                    "airport": segment["arrival"]["iataCode"],
                    "time": segment["arrival"]["at"]
                },
                "duration": convert_duration_to_minutes(segment["duration"])
            }
            for segment in flight["itineraries"][1]["segments"]
        ]
        
        if departure_key in flights_map:
            flights_map[departure_key]["returnItineraries"].append({
                "returnItinerary": return_itinerary,
                "totalPrice": f"{total_price:.2f}"
            })
            if total_price < float(flights_map[departure_key]["departureMinPrice"]):
                flights_map[departure_key]["departureMinPrice"] = f"{total_price:.2f}"
        else:
            flights_map[departure_key] = {
                "departureItinerary": departure_itinerary,
                "returnItineraries": [{
                    "returnItinerary": return_itinerary,
                    "totalPrice": f"{total_price:.2f}"
                }],
                "departureMinPrice": f"{total_price:.2f}"
            }
    
    # Convert map to list and limit to 20 departure itineraries
    grouped_flights = [
        {
            "departureItinerary": flight["departureItinerary"],
            "departureMinPrice": flight["departureMinPrice"],
            "returnItineraries": flight["returnItineraries"],
            "returnCount": len(flight["returnItineraries"]),
            "currency": "EUR"
        }
        for flight in list(flights_map.values())[:20]
    ]
    
    return {
        "roundTrip": {
            "results": grouped_flights,
            "count": len(grouped_flights)
        }
    } 