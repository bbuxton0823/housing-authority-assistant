"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";

interface WeatherWidgetProps {
  weatherData: any;
  onWeatherUpdate: (data: any) => void;
}

export function WeatherWidget({ weatherData, onWeatherUpdate }: WeatherWidgetProps) {
  const [location, setLocation] = useState('');
  const [date, setDate] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleWeatherSearch = async () => {
    if (!location) return;
    
    setIsLoading(true);
    try {
      const url = `/weather/${encodeURIComponent(location)}${date ? `?date=${date}` : ''}`;
      const response = await fetch(url);
      
      if (response.ok) {
        const data = await response.json();
        onWeatherUpdate(data.weather);
      } else {
        console.error('Weather search failed');
      }
    } catch (error) {
      console.error('Weather search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getWeatherIcon = (condition: string) => {
    const iconMap: { [key: string]: string } = {
      'sunny': '☀️',
      'partly cloudy': '⛅',
      'cloudy': '☁️',
      'rainy': '🌧️',
      'snowy': '❄️',
      'stormy': '⛈️'
    };
    return iconMap[condition.toLowerCase()] || '🌤️';
  };

  const getPackingAdvice = (condition: string, temperature: string) => {
    const temp = parseInt(temperature.replace('°F', ''));
    const advice: string[] = [];

    if (temp < 40) {
      advice.push('Heavy coat', 'Warm layers', 'Gloves and hat');
    } else if (temp < 60) {
      advice.push('Light jacket', 'Long pants', 'Closed shoes');
    } else if (temp < 80) {
      advice.push('Light layers', 'Comfortable walking shoes');
    } else {
      advice.push('Light clothing', 'Sun protection', 'Sandals');
    }

    if (condition.toLowerCase().includes('rain')) {
      advice.push('Umbrella', 'Waterproof jacket');
    }

    if (condition.toLowerCase().includes('sunny')) {
      advice.push('Sunglasses', 'Sunscreen');
    }

    return advice;
  };

  return (
    <div className="space-y-4">
      {/* Weather Search */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Weather Forecast</h3>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Enter city or destination"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyPress={(e) => e.key === 'Enter' && handleWeatherSearch()}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date (Optional)
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <button
            onClick={handleWeatherSearch}
            disabled={isLoading || !location}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Getting Weather...' : 'Get Weather'}
          </button>
        </div>
      </Card>

      {/* Weather Display */}
      {weatherData && (
        <Card className="p-6">
          <div className="text-center mb-6">
            <h4 className="text-2xl font-bold text-gray-800 mb-2">
              {weatherData.location}
            </h4>
            <p className="text-gray-600">{weatherData.date}</p>
          </div>

          <div className="flex items-center justify-center mb-6">
            <div className="text-center">
              <div className="text-6xl mb-2">
                {getWeatherIcon(weatherData.condition)}
              </div>
              <div className="text-4xl font-bold text-gray-800 mb-2">
                {weatherData.temperature}
              </div>
              <div className="text-lg text-gray-600 capitalize">
                {weatherData.condition}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm text-gray-600">Humidity</div>
              <div className="text-lg font-medium">{weatherData.humidity}</div>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm text-gray-600">Wind Speed</div>
              <div className="text-lg font-medium">{weatherData.wind_speed}</div>
            </div>
          </div>

          {/* Weather Description */}
          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h5 className="font-medium text-gray-800 mb-2">Forecast</h5>
            <p className="text-gray-700">{weatherData.forecast}</p>
          </div>

          {/* Packing Advice */}
          <div className="bg-green-50 p-4 rounded-lg">
            <h5 className="font-medium text-gray-800 mb-3">
              🧳 Packing Recommendations
            </h5>
            <div className="grid grid-cols-2 gap-2">
              {getPackingAdvice(weatherData.condition, weatherData.temperature).map((item, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Quick Weather Tips */}
      <Card className="p-6">
        <h5 className="font-medium text-gray-800 mb-3">
          🌟 Travel Weather Tips
        </h5>
        <div className="space-y-2 text-sm text-gray-600">
          <p>• Check weather 24-48 hours before departure for the most accurate forecast</p>
          <p>• Pack layers for unpredictable weather conditions</p>
          <p>• Consider weather when planning outdoor activities</p>
          <p>• Check destination's seasonal weather patterns</p>
          <p>• Don't forget to check weather for your return journey</p>
        </div>
      </Card>
    </div>
  );
}