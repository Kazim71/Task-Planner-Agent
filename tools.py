import os
import requests
from typing import Optional


def tavily_web_search(query: str) -> str:
    """
    Search the web using Tavily API and return results.
    
    Args:
        query (str): The search query string
        
    Returns:
        str: Formatted search results or error message
        
    Raises:
        ValueError: If API key is not found or query is invalid
        requests.RequestException: If API request fails
    """
    # Validate input
    if not query or not query.strip():
        return "Web search unavailable: Query cannot be empty."
    # Get API key from environment
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        return "Web search unavailable: TAVILY_API_KEY environment variable not found."
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query.strip(),
        "search_depth": "basic",
        "include_answer": True,
        "include_raw_content": False,
        "max_results": 5
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'results' in data and data['results']:
            results = []
            for i, result in enumerate(data['results'], 1):
                title = result.get('title', 'No title')
                url = result.get('url', 'No URL')
                content = result.get('content', 'No content')
                results.append(f"{i}. {title}\n   URL: {url}\n   Content: {content}\n")
            answer = data.get('answer', '')
            if answer:
                results.insert(0, f"Answer: {answer}\n\n")
            return "".join(results)
        else:
            return "No search results found"
    except requests.exceptions.Timeout:
        return "Web search timeout. Please try again later."
    except requests.exceptions.ConnectionError:
        return "Web search unavailable: Unable to connect to Tavily API."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "Web search unavailable: Invalid API key."
        elif e.response.status_code == 429:
            return "Web search unavailable: Rate limit exceeded."
        else:
            return f"Web search unavailable: HTTP {e.response.status_code} - {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Web search unavailable: Request failed - {str(e)}"
    except Exception as e:
        return "Web search unavailable: Unexpected error."


def get_weather(city: str) -> str:
    """
    Get current weather information for a city using OpenWeatherMap API.
    
    Args:
        city (str): The city name to get weather for
        
    Returns:
        str: Formatted weather information or error message
        
    Raises:
        ValueError: If API key is not found or city is invalid
        requests.RequestException: If API request fails
    """
    # Validate input
    if not city or not city.strip():
        raise ValueError("City name cannot be empty")
    
    # Get API key from environment
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY environment variable not found")
    
    # OpenWeatherMap API endpoint
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    # Request parameters
    params = {
        "q": city.strip(),
        "appid": api_key,
        "units": "metric"  # Use metric units (Celsius)
    }
    
    try:
        # Make API request
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Extract weather information
        city_name = data.get('name', 'Unknown')
        country = data.get('sys', {}).get('country', 'Unknown')
        temp = data.get('main', {}).get('temp', 0)
        feels_like = data.get('main', {}).get('feels_like', 0)
        humidity = data.get('main', {}).get('humidity', 0)
        pressure = data.get('main', {}).get('pressure', 0)
        wind_speed = data.get('wind', {}).get('speed', 0)
        wind_direction = data.get('wind', {}).get('deg', 0)
        description = data.get('weather', [{}])[0].get('description', 'Unknown')
        
        # Format weather information
        weather_info = f"""Weather for {city_name}, {country}:
Temperature: {temp:.1f}°C (feels like {feels_like:.1f}°C)
Description: {description.title()}
Humidity: {humidity}%
Pressure: {pressure} hPa
Wind: {wind_speed} m/s at {wind_direction}°"""
        
        return weather_info
        
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "Error: Unable to connect to OpenWeatherMap API. Please check your internet connection."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "Error: Invalid API key. Please check your OPENWEATHER_API_KEY."
        elif e.response.status_code == 404:
            return f"Error: City '{city}' not found. Please check the spelling and try again."
        elif e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
        else:
            return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error occurred - {str(e)}"


# Example usage and testing functions
def test_tavily_search():
    """Test function for Tavily web search"""
    try:
        result = tavily_web_search("Python programming")
        print("Tavily Search Test:")
        print(result)
    except Exception as e:
        print(f"Tavily Search Test Error: {e}")


def test_weather():
    """Test function for weather API"""
    try:
        result = get_weather("London")
        print("Weather Test:")
        print(result)
    except Exception as e:
        print(f"Weather Test Error: {e}")


if __name__ == "__main__":
    print("Testing tools.py functions...")
    print("=" * 50)
    test_tavily_search()
    print("\n" + "=" * 50)
    test_weather()
