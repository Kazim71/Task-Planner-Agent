def safe_tavily_search(query: str) -> str:
    """
    Safe Tavily web search with error handling and API key check.
    """
    import os
    try:
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            return "Web search unavailable: TAVILY_API_KEY not set."
        # Call the actual Tavily search function (imported from tools)
        from tools import tavily_web_search
        return tavily_web_search(query)
    except Exception as e:
        return f"Web search unavailable: {e}"

async def safe_get_weather(city: str, date_str: str) -> str:
    """
    Safe weather forecast with error handling and API key check.
    """
    import os
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return "Weather unavailable: OPENWEATHER_API_KEY not set."
        # Call the actual weather forecast function (imported from tools)
        from tools import get_weather_forecast
        return await get_weather_forecast(city, date_str)
    except Exception as e:
        return f"Weather unavailable: {e}"
import os
import logging

# Startup API key validation and fallback mode
FALLBACK_MODE = False
missing_keys = []
available_services = []

TAVILY_KEY = os.getenv('TAVILY_API_KEY')
OPENWEATHER_KEY = os.getenv('OPENWEATHER_API_KEY')

if TAVILY_KEY and len(TAVILY_KEY) >= 10:
    available_services.append('Web Search (Tavily)')
else:
    logging.warning('TAVILY_API_KEY is missing or too short. Web search will use fallback mode.')
    missing_keys.append('TAVILY_API_KEY')

if OPENWEATHER_KEY and len(OPENWEATHER_KEY) >= 10:
    available_services.append('Weather (OpenWeather)')
else:
    logging.warning('OPENWEATHER_API_KEY is missing or too short. Weather will use fallback mode.')
    missing_keys.append('OPENWEATHER_API_KEY')

if missing_keys:
    FALLBACK_MODE = True
    logging.info(f"Running in fallback mode. Missing keys: {', '.join(missing_keys)}")
else:
    logging.info("All required API keys are present. Full service mode enabled.")

def debug_print_api_keys():
    tavily = TAVILY_KEY
    openweather = OPENWEATHER_KEY
    print(f"TAVILY_API_KEY present: {bool(tavily)}, length: {len(tavily) if tavily else 0}")
    print(f"OPENWEATHER_API_KEY present: {bool(openweather)}, length: {len(openweather) if openweather else 0}")
    if available_services:
        print(f"Available services: {', '.join(available_services)}")
    if missing_keys:
        print(f"Fallback mode enabled. Missing: {', '.join(missing_keys)}")

debug_print_api_keys()
import time
import logging

def timing_decorator(func):
    """Decorator to log execution time of functions."""
    import functools
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logging.getLogger(__name__).info(f"[TIMER] {func.__name__} executed in {elapsed:.3f}s")
        return result
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logging.getLogger(__name__).info(f"[TIMER] {func.__name__} executed in {elapsed:.3f}s (async)")
        return result
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

import requests
# Simple in-memory cache for weather data
_weather_cache = {}

def validate_user_preferences(prefs: dict) -> dict:
    """
    Validate user preferences and provide defaults if needed.
    Args:
        prefs (dict): User preferences
    Returns:
        dict: Validated preferences
    """
    valid = {}
    valid['interests'] = str(prefs.get('interests', '')).strip() or 'sightseeing, local cuisine, culture'
    valid['citizenship'] = str(prefs.get('citizenship', '')).strip() or 'Unknown'
    valid['budget'] = str(prefs.get('budget', '')).strip() or 'Moderate'
    return valid

def replace_destination_placeholders(text, itinerary):
    """
    Replace placeholders like [city 1], [country 1] with actual destination names from the itinerary.
    Args:
        text (str): Text with placeholders
        itinerary (list): List of dicts with 'city' and 'country' keys
    Returns:
        str: Text with placeholders replaced
    """
    import re
    if not isinstance(text, str):
        return text
    for i, day in enumerate(itinerary, 1):
        if 'city' in day:
            text = re.sub(rf'\[city {i}\]', day['city'], text)
        if 'country' in day:
            text = re.sub(rf'\[country {i}\]', day['country'], text)
    return text

def collect_user_preferences(interests: str = None, citizenship: str = None, budget: str = None) -> dict:
    """
    Collect user preferences for travel planning.
    Args:
        interests (str): User's travel interests
        citizenship (str): User's nationality/citizenship
        budget (str): User's travel budget
    Returns:
        dict: Dictionary with keys 'interests', 'citizenship', 'budget'
    """
    prefs = {
        'interests': interests,
        'citizenship': citizenship,
        'budget': budget,
    }
    return validate_user_preferences(prefs)

import asyncio
async def get_weather_forecast(city: str, date_str: str, api_key: str = None) -> str:
    """
    Async get weather forecast for a city and date using OpenWeather API.
    """
    import os
    import datetime
    api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return "Weather unavailable (API key not set)."
    cache_key = f"{city.lower()}_{date_str}"
    if cache_key in _weather_cache:
        return _weather_cache[cache_key]
    def fetch():
        url = f"https://api.openweathermap.org/data/2.5/forecast"
        params = {"q": city, "appid": api_key, "units": "metric"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    try:
        data = await asyncio.wait_for(asyncio.to_thread(fetch), timeout=12)
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        best = None
        min_diff = None
        for entry in data.get("list", []):
            dt = datetime.datetime.fromtimestamp(entry["dt"])
            if dt.date() == target_date:
                diff = abs(dt.hour - 12)
                if min_diff is None or diff < min_diff:
                    min_diff = diff
                    best = entry
        if best:
            main = best["weather"][0]["main"]
            desc = best["weather"][0]["description"]
            temp = best["main"]["temp"]
            result = f"Weather: {main} ({desc}), {temp}°C"
        else:
            result = "No forecast available for this date."
        _weather_cache[cache_key] = result
        return result
    except asyncio.TimeoutError:
        return "Weather service timeout. Please try again later."
    except requests.RequestException as e:
        return f"Weather service error: {e}"
    except Exception as e:
        return "Weather service unavailable. Using fallback: Weather data not available."
        _weather_cache[cache_key] = result
        return result
def collect_user_preferences(interests: str = None, citizenship: str = None, budget: str = None) -> dict:
    """
    Collect user preferences for travel planning.
    Args:
        interests (str): User's travel interests
        citizenship (str): User's nationality/citizenship
        budget (str): User's travel budget
    Returns:
        dict: Dictionary with keys 'interests', 'citizenship', 'budget'
    """
    prefs = {
        'interests': interests or 'sightseeing, local cuisine, culture',
        'citizenship': citizenship or 'Unknown',
        'budget': budget or 'Moderate',
    }
    return prefs
from typing import Dict, List, Any, Optional
def fix_json_response(json_string: str) -> Dict[str, Any]:
    """
    Attempt to fix common JSON formatting issues in AI responses.
    Handles trailing commas, missing quotes, single quotes, markdown code blocks, and unescaped quotes.
    Tries multiple fix strategies recursively.
    """
    def _strip_markdown(text: str) -> str:
        # Remove all code block markers and leading/trailing whitespace
        text = re.sub(r'^```[a-zA-Z]*', '', text.strip(), flags=re.MULTILINE)
        text = re.sub(r'```$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\n', '', text)
        return text.strip()

    def _fix_quotes(text: str) -> str:
        # Replace single quotes with double quotes, but not in numbers or true/false/null
        text = re.sub(r"'([^']*?)'", r'"\1"', text)
        # Escape unescaped double quotes inside values
        text = re.sub(r':\s*"([^"]*?)"([,}\]])', lambda m: ': "' + m.group(1).replace('"', '\\"') + '"' + m.group(2), text)
        return text

    def _remove_trailing_commas(text: str) -> str:
        text = re.sub(r',\s*([}\]])', r'\1', text)
        return text

    def _recursive_attempts(text: str, depth: int = 0) -> Dict[str, Any]:
        if depth > 3:
            raise ValueError("Unable to repair and parse JSON response after multiple attempts.")
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try stripping markdown
        stripped = _strip_markdown(text)
        if stripped != text:
            try:
                return _recursive_attempts(stripped, depth + 1)
            except Exception:
                pass
        # Try fixing quotes
        fixed_quotes = _fix_quotes(stripped)
        if fixed_quotes != stripped:
            try:
                return _recursive_attempts(fixed_quotes, depth + 1)
            except Exception:
                pass
        # Try removing trailing commas
        no_trailing = _remove_trailing_commas(fixed_quotes)
        if no_trailing != fixed_quotes:
            try:
                return _recursive_attempts(no_trailing, depth + 1)
            except Exception:
                pass
        # Try extracting JSON object
        match = re.search(r'({.*})', no_trailing, re.DOTALL)
        if match:
            try:
                return _recursive_attempts(match.group(1), depth + 1)
            except Exception:
                pass
        raise ValueError("Unable to repair and parse JSON response.")

    return _recursive_attempts(json_string)
import os
import json
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date

def get_itinerary_dates(start_date: date, num_days: int) -> list[date]:
    """
    Generate a list of date objects for each day of the itinerary.
    Args:
        start_date (date): The first day of the itinerary
        num_days (int): Number of days in the itinerary
    Returns:
        list[date]: List of date objects, one for each day
    """
    return [start_date + timedelta(days=i) for i in range(num_days)]
import re
import time
# from tools import tavily_web_search, get_weather  # Commented out - APIs not available
from models import save_plan, get_all_plans
from logging_config import get_logger, log_external_api_call, log_database_operation, sanitize_log_data

# Configure logging
logger = get_logger(__name__)


class TaskPlanningAgent:
    """
    AI-powered task planning agent using Google Gemini 2.5 Pro.
    
    This agent takes natural language goals and breaks them down into
    structured, actionable plans with day-by-day breakdowns.
    """
    
    def __init__(self):
        """Initialize the agent with Gemini API configuration."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not found")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # System prompt for the agent
        self.system_prompt = """You are an expert task planning assistant. Your role is to break down complex goals into actionable, day-by-day plans.

When given a goal, you should:
1. Analyze the goal and identify key components
2. Create a structured plan with daily tasks
3. Estimate realistic timeframes
4. Consider dependencies between tasks
5. Suggest relevant research topics for web search
6. Identify if weather information would be helpful

Always return your response in the following JSON format:
{
    "goal": "The original goal",
    "overview": "Brief overview of the plan",
    "estimated_duration": "Total estimated time (e.g., '2 weeks', '5 days')",
    "daily_breakdown": [
        {
            "day": 1,
            "date": "YYYY-MM-DD",
            "focus": "Main focus for this day",
            "tasks": [
                {
                    "task": "Specific task description",
                    "estimated_time": "Time estimate (e.g., '2 hours', '30 minutes')",
                    "priority": "high/medium/low",
                    "dependencies": ["List of tasks this depends on"]
                }
            ],
            "research_topics": ["Topics to research for this day"],
            "weather_relevant": false
        }
    ],
    "success_metrics": ["How to measure success"],
    "potential_challenges": ["Potential obstacles and solutions"]
}

Be specific, realistic, and actionable in your planning."""

    @timing_decorator
    async def generate_plan(self, goal: str, start_date: Optional[str] = None, num_days: int = 15, user_prefs: dict = None) -> Dict[str, Any]:
        """
        Generate a structured plan for the given goal.
        Args:
            goal (str): The natural language goal to plan for
            start_date (Optional[str]): Start date in YYYY-MM-DD format. If None, uses tomorrow.
            num_days (int): Number of days in the itinerary (default 15)
        Returns:
            Dict[str, Any]: Structured plan with daily breakdown
        Raises:
            ValueError: If goal is empty or API key is missing
            Exception: If plan generation fails
        """
        import re
        import json
        from typing import Any, Dict
        if not goal or not goal.strip():
            raise ValueError("Goal cannot be empty")
        # Use tomorrow as default start date if not provided
        if not start_date:
            start_dt = date.today() + timedelta(days=1)
            start_date = start_dt.strftime("%Y-%m-%d")
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        # Generate itinerary dates
        itinerary_dates = get_itinerary_dates(start_dt, num_days)
        
        start_time = time.time()
        logger.info(f"Starting plan generation for goal: {goal[:100]}{'...' if len(goal) > 100 else ''}")
        
        from exceptions import ExternalServiceError
        import time as _time
        max_attempts = 3
        delay_seconds = 5
        last_exception = None
        # Prepare user preferences for prompt
        if user_prefs is None:
            user_prefs = collect_user_preferences()
        interests = user_prefs.get('interests', 'sightseeing, local cuisine, culture')
        citizenship = user_prefs.get('citizenship', 'Unknown')
        budget = user_prefs.get('budget', 'Moderate')
        prompts = [
            f"""{self.system_prompt}\n\nGoal: {goal.strip()}\nStart Date: {start_date}\nItinerary Dates: {[d.strftime('%Y-%m-%d') for d in itinerary_dates]}\nUser Interests: {interests}\nUser Citizenship: {citizenship}\nUser Budget: {budget}\n\nPlease create a detailed, actionable plan for this goal. Make sure to:\n- Break it down into daily tasks, using the provided itinerary dates\n- Personalize recommendations for the user's interests, citizenship, and budget\n- Replace all [placeholders] in the plan with actual user data\n- Consider realistic timeframes\n- Identify research topics that would be helpful\n- Note if weather information would be relevant\n- Include dependencies between tasks\n- Suggest success metrics\n\nReturn only the JSON response, no additional text.""",
            f"""{self.system_prompt}\n\nGoal: {goal.strip()}\nStart Date: {start_date}\nItinerary Dates: {[d.strftime('%Y-%m-%d') for d in itinerary_dates]}\nUser Interests: {interests}\nUser Citizenship: {citizenship}\nUser Budget: {budget}\n\nReturn only the JSON response, no additional text."""
        ]
        import asyncio
        for attempt in range(max_attempts):
            prompt = prompts[0] if attempt == 0 else prompts[1]
            logger.debug(f"Prompt length: {len(prompt)} characters (attempt {attempt+1})")
            logger.info(f"Sending request to Gemini API (attempt {attempt+1})")
            api_start_time = time.time()
            try:
                try:
                    response = await asyncio.wait_for(self.model.generate_content(prompt), timeout=60)
                except asyncio.TimeoutError:
                    logger.error(f"Gemini API call timed out after 60 seconds on attempt {attempt+1}")
                    last_exception = Exception("Gemini API call timed out after 60 seconds")
                    if attempt < max_attempts - 1:
                        backoff = delay_seconds * (2 ** attempt)
                        logger.info(f"Retrying Gemini API call after {backoff} seconds (exponential backoff)...")
                        time.sleep(backoff)
                    continue
                except (ConnectionError, OSError) as e:
                    logger.error(f"Connection error on Gemini API attempt {attempt+1}: {e}")
                    last_exception = e
                    if attempt < max_attempts - 1:
                        backoff = delay_seconds * (2 ** attempt)
                        logger.info(f"Retrying Gemini API call after {backoff} seconds (exponential backoff)...")
                        time.sleep(backoff)
                    continue
                except Exception as e:
                    logger.error(f"Gemini API call failed on attempt {attempt+1}: {e}")
                    last_exception = e
                    if attempt < max_attempts - 1:
                        backoff = delay_seconds * (2 ** attempt)
                        logger.info(f"Retrying Gemini API call after {backoff} seconds (exponential backoff)...")
                        time.sleep(backoff)
                    continue
                api_response_time = time.time() - api_start_time
                log_external_api_call(
                    logger=logger,
                    service="Gemini",
                    endpoint="generate_content",
                    method="POST",
                    status_code=200,
                    response_time=api_response_time,
                    request_data=sanitize_log_data({"prompt_length": len(prompt), "goal_length": len(goal)})
                )
                logger.info(f"Received response from Gemini API in {api_response_time:.3f}s")
                if not response.text:
                    raise Exception("Empty response from Gemini API")
                logger.info(f"Response text length: {len(response.text)} characters")
                logger.debug("Parsing JSON response from Gemini")
                logger.debug(f"Raw Gemini response: {response.text}")
                try:
                    logger.info(f"JSON parsing for Gemini response (API attempt {attempt+1})")
                    plan_data = self._parse_json_response(response.text)
                    logger.info("Successfully parsed plan data from Gemini response")
                    logger.info("Enriching plan with external tools")
                    enrichment_start = time.time()
                    enriched_plan = await self._enrich_plan_with_tools(plan_data, goal)
                    enrichment_time = time.time() - enrichment_start
                    logger.info(f"Plan enrichment completed in {enrichment_time:.3f}s")
                    total_time = time.time() - start_time
                    logger.info(f"Plan generation completed successfully in {total_time:.3f}s")
                    logger.info(f"Generated plan with {len(enriched_plan.get('steps', []))} steps")
                    return enriched_plan
                except Exception as e:
                    logger.error(f"JSON parsing failed (API attempt {attempt+1}): {e}")
                    last_exception = e
                    # Do not retry JSON parsing, only retry API call
            except Exception as e:
                api_response_time = time.time() - api_start_time
                logger.error(f"Gemini API call failed after {api_response_time:.3f}s: {e}")
                log_external_api_call(
                    logger=logger,
                    service="Gemini",
                    endpoint="generate_content",
                    method="POST",
                    error=str(e),
                    response_time=api_response_time,
                    request_data=sanitize_log_data({"prompt_length": len(prompt), "goal_length": len(goal)})
                )
                last_exception = e
            if attempt < max_attempts - 1:
                backoff = delay_seconds * (2 ** attempt)
                logger.info(f"Retrying Gemini API call after {backoff} seconds (exponential backoff)...")
                time.sleep(backoff)
        logger.error(f"All attempts to parse Gemini response failed. Last error: {last_exception}")
        raise ExternalServiceError(
            message=f"Failed to parse Gemini response after {max_attempts} attempts: {last_exception}",
            service="Gemini",
            original_error=last_exception
        )

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from Gemini, handling potential formatting issues.
        
        Args:
            response_text (str): Raw response text from Gemini
            
        Returns:
            Dict[str, Any]: Parsed JSON data
            
        Raises:
            json.JSONDecodeError: If JSON parsing fails
        """
        # Clean the response text
        cleaned_text = response_text.strip()
        # Remove any markdown code blocks
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        # Find JSON object boundaries
        start_idx = cleaned_text.find('{')
        end_idx = cleaned_text.rfind('}')
        if start_idx == -1 or end_idx == -1:
            logger.error(f"Malformed Gemini response (no JSON object found): {cleaned_text}")
            from exceptions import ExternalServiceError, ErrorCode
            raise ExternalServiceError(
                message="No JSON object found in Gemini response.",
                service="Gemini",
                original_error=None
            )
        json_text = cleaned_text[start_idx:end_idx + 1]
        try:
            return fix_json_response(json_text)
        except Exception as e:
            logger.error(f"Malformed Gemini response: {json_text}\nError: {e}")
            from exceptions import ExternalServiceError, ErrorCode
            raise ExternalServiceError(
                message=f"Malformed JSON from Gemini could not be repaired: {e}",
                service="Gemini",
                original_error=e
            )

    def _fix_json_formatting(self, json_text: str) -> str:
        """
        Attempt to fix common JSON formatting issues.
        
        Args:
            json_text (str): Potentially malformed JSON
            
        Returns:
            str: Fixed JSON string
        """
        # Fix common issues
        fixed = json_text
        
        # Fix single quotes to double quotes
        fixed = re.sub(r"'([^']*)':", r'"\1":', fixed)
        fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)
        
        # Fix trailing commas
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        
        return fixed

    @timing_decorator
    async def _enrich_plan_with_tools(self, plan_data: Dict[str, Any], original_goal: str) -> Dict[str, Any]:
        """
        Enrich the plan with placeholder messages for missing APIs.
        This method provides graceful handling when external APIs are not available.
        """
        try:
            # Add enrichment metadata with helpful messages
            plan_data["enrichment"] = {
                "web_search_results": {
                    "status": "unavailable",
                    "message": "Web search requires Tavily API key",
                    "suggestion": "Add TAVILY_API_KEY to your .env file to enable web search enrichment"
                },
                "weather_info": {
                    "status": "partial", 
                    "message": "Weather information is included for each day if available.",
                    "suggestion": "Add OPENWEATHER_API_KEY to your .env file to enable weather data"
                },
                "enriched_at": datetime.now().isoformat(),
                "note": "Using Gemini AI only - external APIs not configured"
            }
            
            # Collect research topics for display (even though we won't search them)
            all_research_topics = []
            for day in plan_data.get("daily_breakdown", []):
                topics = day.get("research_topics", [])
                all_research_topics.extend(topics)
                # Add weather info for each day if city and date are available
                city = day.get("location") or plan_data.get("goal", "").split()[-1]  # crude guess if not present
                date_str = day.get("date")
                if city and date_str:
                    weather = await safe_get_weather(city, date_str)
                    day["weather_forecast"] = weather
                else:
                    day["weather_forecast"] = "No city/date info for weather."
            if all_research_topics:
                plan_data["enrichment"]["research_topics_found"] = all_research_topics[:5]  # Show first 5 topics
                plan_data["enrichment"]["web_search_results"]["topics_to_research"] = all_research_topics[:5]
            return plan_data
            
        except Exception as e:
            logger.error(f"Error in plan enrichment: {e}")
            # Return basic enrichment info even if something goes wrong
            plan_data["enrichment"] = {
                "error": f"Enrichment failed: {e}",
                "enriched_at": datetime.now().isoformat(),
                "note": "Using Gemini AI only"
            }
            return plan_data

    def _extract_location_from_goal(self, goal: str) -> Optional[str]:
        """
        Extract potential location from goal text.
        
        Args:
            goal (str): The goal text
            
        Returns:
            Optional[str]: Extracted location or None
        """
        # Simple location extraction - look for common city/country patterns
        location_patterns = [
            r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, goal, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def save_plan_to_database(self, plan_data: Dict[str, Any]) -> Optional[int]:
        """
        Save the generated plan to the database.
        
        Args:
            plan_data (Dict[str, Any]): The plan data to save
            
        Returns:
            Optional[int]: The ID of the saved plan, or None if failed
        """
        start_time = time.time()
        logger.info("Starting database save operation")
        
        try:
            goal = plan_data.get("goal", "Unknown goal")
            steps = plan_data.get("daily_breakdown", [])
            
            # Log database operation start
            log_database_operation(
                logger=logger,
                operation="INSERT",
                table="plans",
                success=True,
                execution_time=0  # Will be updated after operation
            )
            
            plan = save_plan(goal, steps)
            execution_time = time.time() - start_time
            
            if plan:
                logger.info(f"Plan saved successfully with ID: {plan.id} in {execution_time:.3f}s")
                
                # Log successful database operation
                log_database_operation(
                    logger=logger,
                    operation="INSERT",
                    table="plans",
                    record_id=str(plan.id),
                    success=True,
                    execution_time=execution_time
                )
                return plan.id
            else:
                logger.warning(f"Failed to save plan - no plan object returned after {execution_time:.3f}s")
                
                # Log failed database operation
                log_database_operation(
                    logger=logger,
                    operation="INSERT",
                    table="plans",
                    success=False,
                    error="No plan object returned from save operation",
                    execution_time=execution_time
                )
                return None
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error saving plan to database after {execution_time:.3f}s: {e}")
            
            # Log failed database operation
            log_database_operation(
                logger=logger,
                operation="INSERT",
                table="plans",
                success=False,
                error=str(e),
                execution_time=execution_time
            )
            return None

    def format_plan_output(self, plan_data: Dict[str, Any]) -> str:
        """
        Format the plan data into a readable string.
        
        Args:
            plan_data (Dict[str, Any]): The plan data to format
            
        Returns:
            str: Formatted plan string
        """
        try:
            output = []
            output.append("=" * 60)
            output.append(f"PLAN: {plan_data.get('goal', 'Unknown Goal')}")
            output.append("=" * 60)
            
            # Overview
            overview = plan_data.get('overview', 'No overview available')
            output.append(f"\nOVERVIEW: {overview}")
            
            # Duration
            duration = plan_data.get('estimated_duration', 'Unknown')
            output.append(f"ESTIMATED DURATION: {duration}")
            
            # Daily breakdown
            daily_breakdown = plan_data.get('daily_breakdown', [])
            if daily_breakdown:
                output.append("\nDAILY BREAKDOWN:")
                output.append("-" * 40)
                
                for day in daily_breakdown:
                    day_num = day.get('day', '?')
                    date = day.get('date', 'Unknown date')
                    focus = day.get('focus', 'No focus specified')
                    
                    output.append(f"\nDay {day_num} - {date}")
                    output.append(f"Focus: {focus}")
                    
                    tasks = day.get('tasks', [])
                    if tasks:
                        output.append("Tasks:")
                        for task in tasks:
                            task_desc = task.get('task', 'Unknown task')
                            time_est = task.get('estimated_time', 'Unknown time')
                            priority = task.get('priority', 'Unknown priority')
                            output.append(f"  • {task_desc} ({time_est}, {priority})")
                    
                    research_topics = day.get('research_topics', [])
                    if research_topics:
                        output.append(f"Research: {', '.join(research_topics)}")
                    
                    if day.get('weather_relevant', False):
                        output.append("🌤️  Weather information relevant")
            
            # Success metrics
            success_metrics = plan_data.get('success_metrics', [])
            if success_metrics:
                output.append("\nSUCCESS METRICS:")
                for metric in success_metrics:
                    output.append(f"  • {metric}")
            
            # Challenges
            challenges = plan_data.get('potential_challenges', [])
            if challenges:
                output.append("\nPOTENTIAL CHALLENGES:")
                for challenge in challenges:
                    output.append(f"  • {challenge}")
            
            # Enrichment info
            enrichment = plan_data.get('enrichment', {})
            if enrichment:
                output.append("\nENRICHMENT INFO:")
                if enrichment.get('error'):
                    output.append(f"  • Error: {enrichment['error']}")
                else:
                    # Web search info
                    web_info = enrichment.get('web_search_results', {})
                    if web_info.get('status') == 'unavailable':
                        output.append(f"  • Web Search: {web_info.get('message', 'Not available')}")
                        if web_info.get('topics_to_research'):
                            topics = ', '.join(web_info['topics_to_research'])
                            output.append(f"    Topics to research: {topics}")
                    else:
                        output.append("  • Web search results included")
                    
                    # Weather info
                    weather_info = enrichment.get('weather_info', {})
                    if weather_info.get('status') == 'unavailable':
                        output.append(f"  • Weather: {weather_info.get('message', 'Not available')}")
                    else:
                        output.append("  • Weather information included")
                    
                    # Show suggestions
                    if web_info.get('suggestion'):
                        output.append(f"  • Suggestion: {web_info['suggestion']}")
                    if weather_info.get('suggestion'):
                        output.append(f"  • Suggestion: {weather_info['suggestion']}")
            
            output.append("\n" + "=" * 60)
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error formatting plan output: {e}")
            return f"Error formatting plan: {e}"

    @timing_decorator
    async def create_and_save_plan(self, goal: str, start_date: Optional[str] = None, save_to_db: bool = True, num_days: int = 15, user_prefs: dict = None) -> Dict[str, Any]:
        """
        Create a plan and optionally save it to the database.
        
        Args:
            goal (str): The goal to plan for
            start_date (Optional[str]): Start date in YYYY-MM-DD format
            save_to_db (bool): Whether to save the plan to the database
            num_days (int): Number of days in the itinerary (default 15)
            user_prefs (dict): User preferences for personalization
            
        Returns:
            Dict[str, Any]: Complete plan data with database ID if saved
        """
        try:
            # Generate the plan
            plan_data = await self.generate_plan(goal, start_date, num_days=num_days, user_prefs=user_prefs)
            # Save to database if requested
            if save_to_db:
                plan_id = self.save_plan_to_database(plan_data)
                plan_data["database_id"] = plan_id
            return plan_data
        except Exception as e:
            logger.error(f"Error creating and saving plan: {e}")
            raise


# Convenience functions for easy usage
async def create_plan(goal: str, start_date: Optional[str] = None, save_to_db: bool = True, num_days: int = 15, user_prefs: dict = None) -> str:
    """
    Create a formatted plan for the given goal.
    
    Args:
        goal (str): The goal to plan for
        start_date (Optional[str]): Start date in YYYY-MM-DD format
        save_to_db (bool): Whether to save the plan to the database
        num_days (int): Number of days in the itinerary (default 15)
        user_prefs (dict): User preferences for personalization
        
    Returns:
        str: Formatted plan string
    """
    try:
        agent = TaskPlanningAgent()
        plan_data = await agent.create_and_save_plan(goal, start_date, save_to_db, num_days=num_days, user_prefs=user_prefs)
        return agent.format_plan_output(plan_data)
    except Exception as e:
        return f"Error creating plan: {e}"


def get_all_saved_plans() -> List[Dict[str, Any]]:
    """
    Retrieve all saved plans from the database.
    
    Returns:
        List[Dict[str, Any]]: List of saved plans
    """
    try:
        plans = get_all_plans()
        return [plan.to_dict() for plan in plans]
    except Exception as e:
        logger.error(f"Error retrieving plans: {e}")
        return []


# Example usage and testing
def test_agent():
    """Test function for the planning agent"""
    try:
        print("Testing Task Planning Agent...")
        print("=" * 50)
        
        # Test goal
        test_goal = "Learn Python programming and build a web application"
        
        # Create agent
        agent = TaskPlanningAgent()
        
        # Generate plan
        plan_data = agent.generate_plan(test_goal)
        
        # Format and display
        formatted_plan = agent.format_plan_output(plan_data)
        print(formatted_plan)
        
        # Save to database
        plan_id = agent.save_plan_to_database(plan_data)
        if plan_id:
            print(f"\nPlan saved with ID: {plan_id}")
        
    except Exception as e:
        print(f"Test error: {e}")


if __name__ == "__main__":
    test_agent()
