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
    AI-powered agent that uses Google Gemini to create structured task plans.
    """
    def __init__(self, api_key: str):
        """
        Initializes the agent, configures the API key, and sets up the model and system prompt.
        """
        try:
            if not api_key:
                raise ValueError("API key is required to initialize the TaskPlanningAgent.")
            
            self.api_key = api_key
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
            self.system_prompt = """You are an expert career and learning advisor, combined with a world-class project manager. Your goal is to take a user's request and provide a direct, actionable, and detailed plan or roadmap to achieve it.

**Crucially, you must not create a plan about how to create a plan. You must provide the expert plan itself.** Leverage your extensive knowledge of topics like software engineering, data science, and project management to create expert-level roadmaps.

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
      "focus": "A brief theme for the day or week (e.g., 'Python Fundamentals', 'SQL for Data Analysis').",
      "tasks": [
        {
          "task": "A specific, actionable task, like 'Complete the Python for Everybody course on Coursera' or 'Build a web scraper for a simple site'.",
          "estimated_time": "A string for the time needed (e.g., '2 weeks', '40 hours').",
          "priority": "high"
        }
      ]
    }
  ],
  "success_metrics": ["Two or three clear metrics to define success, like 'Build 3 portfolio projects' or 'Pass a certification exam'."],
  "potential_challenges": ["Possible issues the user might face, like 'Staying motivated during difficult topics' or 'Finding clean datasets for projects'."]
}"""
            logger.info("TaskPlanningAgent initialized successfully.")

        except Exception as e:
            logger.error(f"FATAL: Failed to initialize TaskPlanningAgent: {e}")
            raise

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parses the JSON response from the AI, cleaning it if necessary."""
        logger.info("Attempting to parse AI response.")
        try:
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3]
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}\nRaw response was: {response_text}")
            raise ValueError("The AI returned a malformed plan. Could not parse JSON.")

    async def generate_plan(self, goal: str, start_date: Optional[str] = None) -> Dict[str, Any]:
        """Generates a structured plan by calling the Gemini API."""
        if not goal or not goal.strip():
            raise ValueError("Goal cannot be empty.")

        # --- NEW DATE LOGIC START ---
        today = date.today()
        effective_start_date = today + timedelta(days=1) # Default to tomorrow

        if start_date:
            try:
                user_date = date.fromisoformat(start_date)
                # If user provides a past date, use tomorrow instead
                if user_date > today:
                    effective_start_date = user_date
            except (ValueError, TypeError):
                # If date is invalid format, ignore it and use tomorrow's date
                logger.warning(f"Invalid start_date format '{start_date}'. Defaulting to tomorrow.")
                pass
        
        start_date_str = effective_start_date.strftime("%Y-%m-%d")
        # --- NEW DATE LOGIC END ---
        
        logger.info(f"Generating plan for goal: {goal} starting on {start_date_str}")
        
        full_prompt = f"{self.system_prompt}\n\nHere is the user's goal:\nGoal: {goal}\nStart Date: {start_date_str}"

        try:
            response = self.model.generate_content(full_prompt)
            parsed_plan = self._parse_json_response(response.text)
            logger.info("Successfully generated and parsed plan from AI.")
            return parsed_plan
        except Exception as e:
            logger.error(f"Error during Gemini API call or parsing: {e}\n{traceback.format_exc()}")
            raise

    def save_plan_to_database(self, plan_data: Dict[str, Any]) -> Optional[int]:
        """Saves the generated plan to the database using the function from models.py."""
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
        return json.dumps(plan_data, indent=2)