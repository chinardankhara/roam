const axios = require('axios');
require('dotenv').config();

// Add token generation function
async function getAmadeusToken() {
  try {
    const response = await axios.post(
      'https://test.api.amadeus.com/v1/security/oauth2/token',
      `grant_type=client_credentials&client_id=${process.env.AMADEUS_API_KEY}&client_secret=${process.env.AMADEUS_API_SECRET}`,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );
    return response.data.access_token;
  } catch (error) {
    console.error('Error getting Amadeus token:', error.response?.data || error.message);
    throw new Error('Failed to authenticate with Amadeus API');
  }
}

async function getFlights(origin, destination, departureDate, returnDate, adults = 1, travelClass = 'ECONOMY') {
  const token = await getAmadeusToken();
  
  // Validate inputs
  if (adults < 1 || adults > 9) {
    throw new Error('Adults must be between 1 and 9.');
  }

  const validClasses = ['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'];
  if (!validClasses.includes(travelClass)) {
    throw new Error(`Invalid travel class. Choose one of: ${validClasses.join(', ')}`);
  }

  const skyteamAirlines = 'AR,AM,UX,AF,CI,MU,OK,DL,GA,AZ,KQ,KL,KE,ME,SV,SK,RO,VN,VS,MF';
  const maxResults = 100;

  try {
    // API call to Amadeus
    const response = await axios.get('https://test.api.amadeus.com/v2/shopping/flight-offers', {
      params: {
        originLocationCode: origin,
        destinationLocationCode: destination,
        departureDate: departureDate,
        returnDate: returnDate || undefined,
        adults: adults,
        travelClass: travelClass,
        includedAirlineCodes: skyteamAirlines,
        max: maxResults, // Set maximum number of results to 100
      },
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const flightsMap = new Map();
    const oneWayFlights = [];

    response.data.data.forEach((flight) => {
      const departureItinerary = flight.itineraries[0].segments.map(
        (segment) => ({
          airlineName: segment.carrierCode, // Consider mapping to full names
          flightNumber: segment.number,
          departure: {
            airport: segment.departure.iataCode,
            time: segment.departure.at,
          },
          arrival: {
            airport: segment.arrival.iataCode,
            time: segment.arrival.at,
          },
          duration: convertDurationToMinutes(segment.duration),
        })
      );

      const departureKey = JSON.stringify(departureItinerary);

      if (!returnDate) {
        // One-way flight
        oneWayFlights.push({
          departureItinerary: departureItinerary,
          totalPrice: flight.price.grandTotal,
          currency: flight.price.currency,
        });
        return;
      }

      const returnItinerary = flight.itineraries[1]?.segments.map(
        (segment) => ({
          airlineName: segment.carrierCode, // Consider mapping to full names
          flightNumber: segment.number,
          departure: {
            airport: segment.departure.iataCode,
            time: segment.departure.at,
          },
          arrival: {
            airport: segment.arrival.iataCode,
            time: segment.arrival.at,
          },
          duration: convertDurationToMinutes(segment.duration),
        })
      );

      // Calculate total itinerary price
      const totalItineraryPrice = parseFloat(flight.price.grandTotal);

      if (flightsMap.has(departureKey)) {
        flightsMap.get(departureKey).returnItineraries.push({
          returnItinerary: returnItinerary,
          totalPrice: totalItineraryPrice,
        });
      } else {
        flightsMap.set(departureKey, {
          departureItinerary: departureItinerary,
          returnItineraries: [
            {
              returnItinerary: returnItinerary,
              totalPrice: totalItineraryPrice,
            },
          ],
          departureMinPrice: totalItineraryPrice, // Initially set to the first price
        });
      }

      // Update departureMinPrice if a lower price is found
      const currentMin = flightsMap.get(departureKey).departureMinPrice;
      if (totalItineraryPrice < currentMin) {
        flightsMap.get(departureKey).departureMinPrice = totalItineraryPrice;
      }
    });

    // Convert map to array
    const groupedFlights = Array.from(flightsMap.values()).map((flight) => ({
      departureItinerary: flight.departureItinerary,
      departureMinPrice: flight.departureMinPrice.toFixed(2),
      returnItineraries: flight.returnItineraries.map((ret) => ({
        returnItinerary: ret.returnItinerary,
        totalPrice: ret.totalPrice.toFixed(2),
      })),
      currency: "EUR", // Assuming all prices are in EUR
    }));

    return {
      flights: {
        roundTrip: groupedFlights,
        oneWay: oneWayFlights,
      },
    };
  } catch (error) {
    console.error('Error fetching flight data:', JSON.stringify(error.response?.data, null, 2));
    throw new Error('Failed to fetch flights. Please try again later.');
  }
}

// Helper function to convert ISO 8601 durations to minutes
function convertDurationToMinutes(duration) {
  const match = /PT(?:(\d+)H)?(?:(\d+)M)?/.exec(duration);
  const hours = parseInt(match[1] || '0', 10);
  const minutes = parseInt(match[2] || '0', 10);
  return hours * 60 + minutes;
}

//export getFlights
module.exports = {
  getFlights,
};
