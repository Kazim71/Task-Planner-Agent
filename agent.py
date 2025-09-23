# ==============================================================================
# 1. IMPORTS
# ==============================================================================
import os
import json
import logging
import traceback
import google.generativeai as genai
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

# Import functions from your other project files
from models import save_plan
from tools import tavily_web_search, get_weather

# ==============================================================================
# 2. SETUP
# ==============================================================================
logger = logging.getLogger(__name__)

# ==============================================================================
# 3. TASK PLANNING AGENT CLASS
# ==============================================================================
class TaskPlanningAgent:
    """
    AI-powered agent that uses a two-pass approach with Google Gemini to create tool-enriched task plans.
    """
    def __init__(self, api_key: str):
        """
        Initializes the agent, configures the API key, and sets up the model and system prompts.
        """
        try:
            if not api_key:
                raise ValueError("API key is required to initialize the TaskPlanningAgent.")
            
            self.api_key = api_key
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
            self.tool_selection_prompt = """You are a tool-selection assistant. Based on the user's goal, decide which of the following tools, if any, are necessary. Return your answer as a JSON list of objects.

Available Tools:
1. `web_search`: Useful for finding real-time information, locations, facts, or ideas.
2. `weather`: Useful for getting the weather forecast for a specific city.

Your response MUST be a JSON list, even if it's empty. Each object in the list should have a "tool_name" and necessary "parameters".

Example 1:
Goal: "Plan a 3-day hiking trip in the Swiss Alps"
Response:
[
  {"tool_name": "web_search", "parameters": {"query": "Best 3-day hiking trails in Swiss Alps"}},
  {"tool_name": "weather", "parameters": {"city": "Interlaken, Switzerland"}}
]

Example 2:
Goal: "Learn Python in 1 month"
Response:
[
  {"tool_name": "web_search", "parameters": {"query": "Best resources to learn Python in one month"}}
]

Example 3:
Goal: "Write a short story"
Response:
[]
"""
            
            self.final_plan_prompt = """You are an expert career and learning advisor, combined with a world-class project manager. Your goal is to take a user's request and provide a direct, actionable, and detailed plan or roadmap to achieve it.

**Crucially, you must not create a plan about how to create a plan. You must provide the expert plan itself.**

You have been provided with context from external tools. You MUST use this information to make your plan more accurate and helpful.

You MUST return the plan as a single JSON object. Do not include any text, conversational filler, or markdown formatting like ```json before or after the JSON object.

The JSON object must follow this exact structure:
{
  "goal": "The user's original goal",
  "overview": "A brief, one-sentence summary of the plan.",
  "estimated_duration": "A string describing the total time (e.g., '3 months', '1 year').",
  "daily_breakdown": [
    {
      "day": 1,
      "date": "YYYY-MM-DD",
      "focus": "A brief theme for the day or week (e.g., 'Cultural Highlights', 'Python Fundamentals').",
      "tasks": [
        {
          "task": "A specific, actionable task, like 'Complete the Python for Everybody course on Coursera' or 'Build a web scraper for a simple site'.",
          "estimated_time": "A string for the time needed (e.g., '2 weeks', '40 hours').",
          "priority": "high"
        }
      ]
    }
  ],
  "success_metrics": ["Two or three clear metrics to define success."],
  "potential_challenges": ["Possible issues the user might face."]
}"""
            logger.info("TaskPlanningAgent initialized successfully.")

        except Exception as e:
            logger.error(f"FATAL: Failed to initialize TaskPlanningAgent: {e}")
            raise

    def _parse_json_response(self, response_text: str, context: str = "plan") -> Any:
        """Parses the JSON response from the AI, cleaning it if necessary."""
        logger.info(f"Attempting to parse AI response for {context}.")
        try:
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3]
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for {context}: {e}\nRaw response was: {response_text}")
            raise ValueError(f"The AI returned a malformed response for {context}. Could not parse JSON.")

    async def _select_tools(self, goal: str) -> List[Dict[str, Any]]:
        """Pass 1: Decide which tools to use based on the user's goal."""
        logger.info("Starting Pass 1: Tool Selection")
        prompt = f"{self.tool_selection_prompt}\n\nGoal: \"{goal}\"\nResponse:"
        try:
            response = self.model.generate_content(prompt)
            tools_to_use = self._parse_json_response(response.text, context="tool selection")
            if isinstance(tools_to_use, list):
                logger.info(f"Selected tools: {[tool.get('tool_name') for tool in tools_to_use]}")
                return tools_to_use
            return []
        except Exception as e:
            logger.error(f"Failed to select tools: {e}")
            return [] # Return an empty list on failure to proceed without tools

    async def generate_plan(self, goal: str, start_date: Optional[str] = None) -> Dict[str, Any]:
        """Generates a structured plan by calling the Gemini API, using a two-pass approach with tools."""
        if not goal or not goal.strip():
            raise ValueError("Goal cannot be empty.")

        # --- PASS 1: Select and Execute Tools ---
        tools_to_use = await self._select_tools(goal)
        tool_results = []
        if tools_to_use:
            for tool in tools_to_use:
                tool_name = tool.get("tool_name")
                params = tool.get("parameters", {})
                if tool_name == "web_search":
                    result = tavily_web_search(query=params.get("query", ""))
                    tool_results.append(f"Web Search Results for '{params.get('query')}':\n{result}")
                elif tool_name == "weather":
                    result = get_weather(city=params.get("city", ""))
                    tool_results.append(f"Weather Forecast for '{params.get('city')}':\n{result}")
        
        tool_context = "\n\n".join(tool_results) if tool_results else "No tools were used."

        # --- PASS 2: Generate the Final Plan ---
        logger.info("Starting Pass 2: Final Plan Generation")
        
        # Date Logic
        today = date.today()
        effective_start_date = today + timedelta(days=1)
        if start_date:
            try:
                user_date = date.fromisoformat(start_date)
                if user_date > today:
                    effective_start_date = user_date
            except (ValueError, TypeError):
                logger.warning(f"Invalid start_date format '{start_date}'. Defaulting to tomorrow.")
        start_date_str = effective_start_date.strftime("%Y-%m-%d")
        
        logger.info(f"Generating plan for goal: {goal} starting on {start_date_str}")
        
        full_prompt = (
            f"{self.final_plan_prompt}\n\n"
            f"CONTEXT FROM EXTERNAL TOOLS:\n---\n{tool_context}\n---\n\n"
            f"Here is the user's goal:\nGoal: {goal}\nStart Date: {start_date_str}"
        )

        try:
            response = self.model.generate_content(full_prompt)
            parsed_plan = self._parse_json_response(response.text, context="final plan")
            logger.info("Successfully generated and parsed final plan from AI.")
            return parsed_plan
        except Exception as e:
            logger.error(f"Error during final plan generation: {e}\n{traceback.format_exc()}")
            raise

    def save_plan_to_database(self, plan_data: Dict[str, Any]) -> Optional[int]:
        """Saves the generated plan to the database using the function from models.py."""
        # This method remains the same
        logger.info("Saving plan to database...")
        try:
            goal = plan_data.get("goal")
            steps = plan_data.get("daily_breakdown")
            if not goal or not steps:
                logger.warning("Plan data is missing 'goal' or 'daily_breakdown', cannot save.")
                return None
            plan_record = save_plan(goal=goal, steps=steps)
            if plan_record:
                logger.info(f"Plan saved with ID: {plan_record.id}")
                return plan_record.id
            return None
        except Exception as e:
            logger.error(f"Error saving plan to database: {e}\n{traceback.format_exc()}")
            return None

    def format_plan_output(self, plan_data: Dict[str, Any]) -> str:
        """Formats the plan data into a JSON string for the frontend."""
        # This method remains the same
        return json.dumps(plan_data, indent=2)