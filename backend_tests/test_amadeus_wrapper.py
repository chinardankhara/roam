import asyncio
import json
from pathlib import Path
import pytest
from datetime import date
from backend.amadeus_wrapper import get_flights

@pytest.mark.asyncio
async def test_case1():
    """Test Case 1: Valid one-way search"""
    print("Test Case 1: Valid one-way search")
    result = await get_flights("ATL", "LHR", "2025-05-02")
    
    assert result and "flights" in result
    
    # Save results to JSON file
    output_path = Path(__file__).parent / "results" / "test1_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to {output_path}")
    return True

@pytest.mark.asyncio
async def test_case2():
    """Test Case 2: Invalid number of adults"""
    print("Test Case 2: Invalid number of adults")
    with pytest.raises(ValueError) as exc_info:
        await get_flights("ATL", "JFK", "2025-05-01", adults=0)
    assert "Adults must be between 1 and 9" in str(exc_info.value)
    print(f"Test Case 2 Passed: {exc_info.value}")
    return True

@pytest.mark.asyncio
async def test_case3():
    """Test Case 3: Invalid travel class"""
    print("Test Case 3: Invalid travel class")
    with pytest.raises(ValueError) as exc_info:
        await get_flights("ATL", "JFK", "2025-05-01", travel_class="LUXURY")  # type: ignore
    assert "Invalid travel class" in str(exc_info.value)
    print(f"Test Case 3 Passed: {exc_info.value}")
    return True

@pytest.mark.asyncio
async def test_case4():
    """Test Case 4: Valid round-trip search"""
    print("Test Case 4: Valid round-trip search")
    result = await get_flights(
        "ATL", 
        "CDG", 
        date(2025, 5, 2),
        date(2025, 5, 10)
    )
    
    assert result and "flights" in result
    
    output_path = Path(__file__).parent / "results" / "test4_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to {output_path}")
    return True

@pytest.mark.asyncio
async def test_case5():
    """Test Case 5: Missing required fields"""
    print("Test Case 5: Missing required fields")
    with pytest.raises(TypeError) as exc_info:
        await get_flights()  # type: ignore
    print(f"Test Case 5 Passed: {exc_info.value}")
    return True

async def run_tests(selected_tests: list[str] = None) -> None:
    """Run selected test cases or all tests if none specified."""
    print("Running selected test cases...\n")
    
    test_cases = {
        "test_case1": test_case1,
        "test_case2": test_case2,
        "test_case3": test_case3,
        "test_case4": test_case4,
        "test_case5": test_case5,
    }
    
    try:
        tests_to_run = selected_tests or list(test_cases.keys())
        
        for test_name in tests_to_run:
            if test_name in test_cases:
                print(f"\nExecuting {test_name}...")
                try:
                    await test_cases[test_name]()
                except Exception as e:
                    print(f"{test_name} failed with error: {e}")
            else:
                print(f"Test case '{test_name}' not found")
    
    except Exception as e:
        print(f"Test execution failed: {e}")
    
    print("\nTests complete.")

if __name__ == "__main__":
    import sys
    
    # Get command line arguments, skipping script name
    args = sys.argv[1:]
    
    # Run specific tests if provided, otherwise run all tests
    asyncio.run(run_tests(args if args else None)) 