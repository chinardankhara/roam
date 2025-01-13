from typing import Dict, List, Optional, Union, Literal, Any
import os
from datetime import date, datetime, timedelta
import httpx
from dotenv import load_dotenv
import json
import re
from dateutil.parser import parse as parse_date

load_dotenv()

TravelClass = Literal["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]
FlightResult = Dict[str, Union[Dict, List, str, int, float]]

class AmadeusTokenManager:
    _instance = None
    _token_cache: Optional[str] = None
    _token_expiration: Optional[datetime] = None
    _token_expiration_time = 1800  # Token expiration time in seconds (30 minutes)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AmadeusTokenManager, cls).__new__(cls)
        return cls._instance

    async def get_token(self) -> str:
        """Get authentication token from Amadeus API, using cached token if valid."""
        if self._token_cache and self._token_expiration and datetime.now() < self._token_expiration:
            return self._token_cache

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
                data = response.json()
                self._token_cache = data["access_token"]
                self._token_expiration = datetime.now() + timedelta(seconds=self._token_expiration_time)
                return self._token_cache
        except httpx.HTTPError as error:
            print(f"Error getting Amadeus token: {error.response.json() if error.response else error}")
            raise ValueError("Failed to authenticate with Amadeus API")

async def get_amadeus_token() -> str:
    token_manager = AmadeusTokenManager()
    return await token_manager.get_token()

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
    max_results = 150 if return_date else 20

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

async def get_flight_inspiration(
    origin: str,
    departure_date: Union[str, date, tuple, list],
    duration: Union[int, tuple, list],
    max_price: Optional[int] = None,
) -> List[Dict[str, str]]:
    """
    Get flight inspiration search results from Amadeus API.
    
    Returns:
        List of dictionaries containing flight information:
        - origin: Origin airport code
        - destination: Destination airport code
        - departureDate: Departure date
        - returnDate: Return date
        - price: Total price
        - flightOffersLink: Link to flight offers
    """
    
    # Validate origin airport code
    if not isinstance(origin, str) or len(origin) != 3:
        raise ValueError("Origin must be a valid 3-letter IATA airport code")
    
    # Process and validate dates
    def _validate_single_date(d: Union[str, date]) -> str:
        if isinstance(d, str):
            try:
                d = parse_date(d).date()
            except ValueError:
                raise ValueError(f"Invalid date format: {d}. Use YYYY-MM-DD format")
        
        today = date.today()
        max_future_date = today + timedelta(days=180)
        
        if d < today:
            raise ValueError("Departure date cannot be in the past")
        if d > max_future_date:
            raise ValueError("Departure date cannot be more than 180 days in the future")
            
        return d.isoformat()
    
    # Process departure date(s)
    if isinstance(departure_date, (tuple, list)):
        if len(departure_date) != 2:
            raise ValueError("Date range must contain exactly two dates")
        
        start_date = _validate_single_date(departure_date[0])
        end_date = _validate_single_date(departure_date[1])
        
        if parse_date(start_date).date() >= parse_date(end_date).date():
            raise ValueError("End date must be after start date")
            
        departure_date_param = f"{start_date},{end_date}"
    else:
        departure_date_param = _validate_single_date(departure_date)
    
    # Process and validate duration
    if isinstance(duration, (tuple, list)):
        if len(duration) != 2:
            raise ValueError("Duration range must contain exactly two values")
        
        min_duration, max_duration = duration
        if min_duration >= max_duration:
            raise ValueError("Maximum duration must be greater than minimum duration")
        if min_duration < 1 or max_duration > 14:
            raise ValueError("Duration must be between 1 and 14 days")
            
        duration_param = f"{min_duration},{max_duration}"
    else:
        if not isinstance(duration, int):
            raise ValueError("Duration must be specified in whole days")
        if duration < 1 or duration > 14:
            raise ValueError("Duration must be between 1 and 14 days")
        duration_param = str(duration)
    
    # Validate max price if provided
    if max_price is not None:
        if not isinstance(max_price, int) or max_price <= 0:
            raise ValueError("Max price must be a positive integer")
    
    # Get authentication token
    token = await get_amadeus_token()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "origin": origin,
                "departureDate": departure_date_param,
                "duration": duration_param,
                "oneWay": "false",
                "viewBy": "DESTINATION"
            }
            
            if max_price:
                params["maxPrice"] = max_price
            
            response = await client.get(
                "https://test.api.amadeus.com/v1/shopping/flight-destinations",
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 400:
                error_data = response.json()
                if any(error.get("code") == "6003" for error in error_data.get("errors", [])):
                    raise ValueError("No flights found for the specified criteria")
            
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "origin": item["origin"],
                    "destination": item["destination"],
                    "departureDate": item["departureDate"],
                    "returnDate": item["returnDate"],
                    "price": item["price"]["total"],
                    "flightOffersLink": item["links"]["flightOffers"]
                }
                for item in data["data"]
            ]
            
    except httpx.TimeoutException as error:
        print(f"Request timed out: {error}")
        raise ValueError("Request timed out. Please try again later.")
    except httpx.HTTPStatusError as error:
        print(f"HTTP error occurred: {error.response.json() if error.response else error}")
        raise ValueError("Failed to fetch flight inspiration. Please try again later.")
    except httpx.HTTPError as error:
        print(f"Error fetching flight data: {error}")
        raise ValueError("Failed to fetch flight inspiration. Please try again later.")