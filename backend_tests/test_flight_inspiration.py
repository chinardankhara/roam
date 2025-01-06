from datetime import date, timedelta
import json
from pathlib import Path
import pytest
from backend.amadeus_wrapper import get_flight_inspiration

@pytest.mark.asyncio
async def test_valid_single_date():
    """Test with valid single date"""
    print("Test Case 1: Valid single date search")
    future_date = date.today() + timedelta(days=30)
    result = await get_flight_inspiration(
        origin="ATL",
        departure_date=future_date,
        duration=7
    )
    
    assert isinstance(result, list)
    if result:  # If API returns results
        assert all(isinstance(item, dict) for item in result)
        assert all(
            all(key in item for key in [
                "origin", "destination", "departureDate",
                "returnDate", "price", "flightOffersLink"
            ])
            for item in result
        )
    
    # Save results to JSON file
    output_path = Path(__file__).parent / "results" / "inspiration_test1.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

@pytest.mark.asyncio
async def test_valid_date_range():
    """Test with valid date range"""
    print("Test Case 2: Valid date range search")
    start_date = date.today() + timedelta(days=30)
    end_date = start_date + timedelta(days=10)
    result = await get_flight_inspiration(
        origin="ATL",
        departure_date=(start_date, end_date),
        duration=(5, 7),
        max_price=1000
    )
    
    assert isinstance(result, list)
    # Save results
    output_path = Path(__file__).parent / "results" / "inspiration_test2.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

@pytest.mark.asyncio
async def test_invalid_inputs():
    """Test various invalid inputs"""
    future_date = date.today() + timedelta(days=30)
    
    # Test invalid date
    with pytest.raises(ValueError, match="180 days"):
        await get_flight_inspiration(
            origin="ATL",
            departure_date=date.today() + timedelta(days=200),
            duration=7
        )
    
    # Test invalid duration
    with pytest.raises(ValueError, match="between 1 and 14 days"):
        await get_flight_inspiration(
            origin="ATL",
            departure_date=future_date,
            duration=20
        )
    
    # Test invalid airport code
    with pytest.raises(ValueError, match="IATA airport code"):
        await get_flight_inspiration(
            origin="INVALID",
            departure_date=future_date,
            duration=7
        ) 