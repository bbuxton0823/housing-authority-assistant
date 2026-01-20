"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";

interface TravelSearchProps {
  onSearchResults: (results: any[]) => void;
  searchResults: any[];
}

export function TravelSearch({ onSearchResults, searchResults }: TravelSearchProps) {
  const [searchType, setSearchType] = useState<'flights' | 'trains'>('flights');
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [departureDate, setDepartureDate] = useState('');
  const [returnDate, setReturnDate] = useState('');
  const [passengers, setPassengers] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    setIsLoading(true);
    try {
      const endpoint = searchType === 'flights' ? '/search/flights' : '/search/trains';
      const searchData = {
        origin,
        destination,
        departure_date: departureDate,
        return_date: returnDate,
        passengers,
        ...(searchType === 'flights' ? { flight_class: 'economy' } : { train_class: 'standard' })
      };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchData),
      });

      if (response.ok) {
        const data = await response.json();
        onSearchResults(data.results[searchType] || []);
      } else {
        console.error('Search failed');
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Form */}
      <Card className="p-6">
        <div className="space-y-4">
          {/* Search Type Toggle */}
          <div className="flex space-x-4">
            <button
              onClick={() => setSearchType('flights')}
              className={`px-4 py-2 rounded-lg ${
                searchType === 'flights' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              ✈️ Flights
            </button>
            <button
              onClick={() => setSearchType('trains')}
              className={`px-4 py-2 rounded-lg ${
                searchType === 'trains' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              🚂 Trains
            </button>
          </div>

          {/* Search Fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                From
              </label>
              <input
                type="text"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="Origin city"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                To
              </label>
              <input
                type="text"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="Destination city"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Departure Date
              </label>
              <input
                type="date"
                value={departureDate}
                onChange={(e) => setDepartureDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Return Date (Optional)
              </label>
              <input
                type="date"
                value={returnDate}
                onChange={(e) => setReturnDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Passengers
              </label>
              <input
                type="number"
                value={passengers}
                onChange={(e) => setPassengers(parseInt(e.target.value))}
                min="1"
                max="9"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <button
            onClick={handleSearch}
            disabled={isLoading || !origin || !destination || !departureDate}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Searching...' : `Search ${searchType === 'flights' ? 'Flights' : 'Trains'}`}
          </button>
        </div>
      </Card>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            {searchType === 'flights' ? 'Flight' : 'Train'} Results
          </h3>
          <div className="space-y-3">
            {searchResults.map((result, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4">
                      <div className="text-lg font-medium">
                        {searchType === 'flights' ? result.airline : result.operator}
                      </div>
                      <div className="text-sm text-gray-500">
                        {searchType === 'flights' ? result.flight_id : result.train_id}
                      </div>
                    </div>
                    <div className="flex items-center space-x-6 mt-2">
                      <div>
                        <div className="font-medium">{result.departure_time}</div>
                        <div className="text-sm text-gray-500">{origin}</div>
                      </div>
                      <div className="flex-1 text-center">
                        <div className="text-sm text-gray-500">{result.duration}</div>
                        <div className="text-xs text-gray-400">
                          {searchType === 'flights' 
                            ? result.stops === 0 ? 'Direct' : `${result.stops} stop${result.stops > 1 ? 's' : ''}`
                            : `${result.stops} stops`
                          }
                        </div>
                      </div>
                      <div>
                        <div className="font-medium">{result.arrival_time}</div>
                        <div className="text-sm text-gray-500">{destination}</div>
                      </div>
                    </div>
                    {searchType === 'trains' && result.amenities && (
                      <div className="mt-2 text-sm text-gray-600">
                        Amenities: {result.amenities.join(', ')}
                      </div>
                    )}
                  </div>
                  <div className="ml-6 text-right">
                    <div className="text-2xl font-bold text-green-600">
                      ${result.price}
                    </div>
                    <button className="mt-2 bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600">
                      Select
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}