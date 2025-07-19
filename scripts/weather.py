#!/usr/bin/env python3
"""
Weather fetcher script for GitHub profile README
Fetches current weather data and updates the README.md
"""

import os
import requests
import json
from datetime import datetime

def fetch_weather(api_key, city):
    """Fetch weather data for a given city"""
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return {
            'city': city,
            'temperature': data['current']['temp_c'],
            'condition': data['current']['condition']['text'],
            'icon': data['current']['condition']['icon'],
            'humidity': data['current']['humidity'],
            'wind_speed': data['current']['wind_kph']
        }
    except Exception as e:
        print(f"Error fetching weather for {city}: {e}")
        return None

def get_fallback_weather():
    """Get fallback weather data when API is unavailable"""
    from datetime import datetime
    return [
        {'city': 'Valsad', 'temperature': 28, 'condition': 'Partly Cloudy', 'icon': '', 'humidity': 75, 'wind_speed': 12},
        {'city': 'Boston', 'temperature': 18, 'condition': 'Clear', 'icon': '', 'humidity': 60, 'wind_speed': 8},
        {'city': 'London', 'temperature': 15, 'condition': 'Overcast', 'icon': '', 'humidity': 80, 'wind_speed': 15},
        {'city': 'Tokyo', 'temperature': 22, 'condition': 'Sunny', 'icon': '', 'humidity': 65, 'wind_speed': 10}
    ]

def generate_weather_table(weather_data):
    """Generate HTML table for weather data"""
    if not weather_data:
        weather_data = get_fallback_weather()
    
    table = """## 🌤️ Current Weather

<table>
<tr>
    <th>🌍 City</th>
    <th>🌡️ Temperature</th>
    <th>☁️ Condition</th>
    <th>💧 Humidity</th>
    <th>💨 Wind Speed</th>
</tr>"""
    
    for weather in weather_data:
        if weather:
            table += f"""
<tr>
    <td>{weather['city']}</td>
    <td>{weather['temperature']}°C</td>
    <td>{weather['condition']}</td>
    <td>{weather['humidity']}%</td>
    <td>{weather['wind_speed']} km/h</td>
</tr>"""
    
    table += "\n</table>"
    return table

def main():
    """Main function to fetch weather and generate output"""
    api_key = os.getenv('WEATHER_API_KEY', 'b3c68b2c9eb541e0836135303242011')
    cities = ['Valsad', 'Boston', 'London', 'Tokyo']
    
    weather_data = []
    for city in cities:
        weather = fetch_weather(api_key, city)
        if weather:
            weather_data.append(weather)
    
    # If no weather data was fetched (API unavailable), use fallback
    if not weather_data:
        weather_data = get_fallback_weather()
        print("Using fallback weather data (API unavailable)")
    
    # Generate table
    weather_table = generate_weather_table(weather_data)
    
    # Save to file for use in README update
    with open('weather_data.html', 'w') as f:
        f.write(weather_table)
    
    print("Weather data generated successfully!")
    return weather_table

if __name__ == "__main__":
    main()