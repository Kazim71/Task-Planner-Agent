import os
import json
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from tools import tavily_web_search, get_weather
from models import save_plan, get_all_plans
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    def generate_plan(self, goal: str, start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a structured plan for the given goal.
        
        Args:
            goal (str): The natural language goal to plan for
            start_date (Optional[str]): Start date in YYYY-MM-DD format. If None, uses today.
            
        Returns:
            Dict[str, Any]: Structured plan with daily breakdown
            
        Raises:
            ValueError: If goal is empty or API key is missing
            Exception: If plan generation fails
        """
        if not goal or not goal.strip():
            raise ValueError("Goal cannot be empty")
        
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Create the prompt for Gemini
            prompt = f"""
{self.system_prompt}

Goal: {goal.strip()}
Start Date: {start_date}

Please create a detailed, actionable plan for this goal. Make sure to:
- Break it down into daily tasks
- Consider realistic timeframes
- Identify research topics that would be helpful
- Note if weather information would be relevant
- Include dependencies between tasks
- Suggest success metrics

Return only the JSON response, no additional text.
"""
            
            logger.info(f"Generating plan for goal: {goal}")
            
            # Generate response from Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise Exception("Empty response from Gemini API")
            
            # Parse JSON response
            plan_data = self._parse_json_response(response.text)
            
            # Enrich plan with web search and weather data
            enriched_plan = self._enrich_plan_with_tools(plan_data, goal)
            
            logger.info("Plan generated successfully")
            return enriched_plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise Exception(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            raise Exception(f"Plan generation failed: {e}")

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
            raise json.JSONDecodeError("No JSON object found in response", cleaned_text, 0)
        
        json_text = cleaned_text[start_idx:end_idx + 1]
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            fixed_json = self._fix_json_formatting(json_text)
            return json.loads(fixed_json)

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

    def _enrich_plan_with_tools(self, plan_data: Dict[str, Any], original_goal: str) -> Dict[str, Any]:
        """
        Enrich the plan with web search results and weather information.
        
        Args:
            plan_data (Dict[str, Any]): The base plan data
            original_goal (str): The original goal for context
            
        Returns:
            Dict[str, Any]: Enriched plan data
        """
        try:
            # Add enrichment metadata
            plan_data["enrichment"] = {
                "web_search_results": {},
                "weather_info": {},
                "enriched_at": datetime.now().isoformat()
            }
            
            # Collect all research topics
            all_research_topics = []
            for day in plan_data.get("daily_breakdown", []):
                topics = day.get("research_topics", [])
                all_research_topics.extend(topics)
            
            # Perform web searches for research topics
            if all_research_topics:
                logger.info("Enriching plan with web search results")
                for topic in all_research_topics[:3]:  # Limit to 3 topics to avoid rate limits
                    try:
                        search_results = tavily_web_search(f"{topic} {original_goal}")
                        plan_data["enrichment"]["web_search_results"][topic] = search_results
                    except Exception as e:
                        logger.warning(f"Web search failed for topic '{topic}': {e}")
                        plan_data["enrichment"]["web_search_results"][topic] = f"Search failed: {e}"
            
            # Check for weather-relevant days
            weather_days = []
            for day in plan_data.get("daily_breakdown", []):
                if day.get("weather_relevant", False):
                    weather_days.append(day)
            
            # Get weather information for relevant days
            if weather_days:
                logger.info("Enriching plan with weather information")
                # Try to extract location from goal or use a default
                location = self._extract_location_from_goal(original_goal)
                if location:
                    try:
                        weather_info = get_weather(location)
                        plan_data["enrichment"]["weather_info"]["location"] = location
                        plan_data["enrichment"]["weather_info"]["current_weather"] = weather_info
                    except Exception as e:
                        logger.warning(f"Weather lookup failed for location '{location}': {e}")
                        plan_data["enrichment"]["weather_info"]["error"] = str(e)
            
            return plan_data
            
        except Exception as e:
            logger.error(f"Error enriching plan: {e}")
            # Return original plan if enrichment fails
            plan_data["enrichment"] = {
                "error": f"Enrichment failed: {e}",
                "enriched_at": datetime.now().isoformat()
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
        try:
            goal = plan_data.get("goal", "Unknown goal")
            steps = plan_data.get("daily_breakdown", [])
            
            plan = save_plan(goal, steps)
            if plan:
                logger.info(f"Plan saved to database with ID: {plan.id}")
                return plan.id
            else:
                logger.error("Failed to save plan to database")
                return None
                
        except Exception as e:
            logger.error(f"Error saving plan to database: {e}")
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
            if enrichment and not enrichment.get('error'):
                output.append("\nENRICHMENT INFO:")
                if enrichment.get('web_search_results'):
                    output.append("  • Web search results included")
                if enrichment.get('weather_info'):
                    output.append("  • Weather information included")
            
            output.append("\n" + "=" * 60)
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error formatting plan output: {e}")
            return f"Error formatting plan: {e}"

    def create_and_save_plan(self, goal: str, start_date: Optional[str] = None, save_to_db: bool = True) -> Dict[str, Any]:
        """
        Create a plan and optionally save it to the database.
        
        Args:
            goal (str): The goal to plan for
            start_date (Optional[str]): Start date in YYYY-MM-DD format
            save_to_db (bool): Whether to save the plan to the database
            
        Returns:
            Dict[str, Any]: Complete plan data with database ID if saved
        """
        try:
            # Generate the plan
            plan_data = self.generate_plan(goal, start_date)
            
            # Save to database if requested
            if save_to_db:
                plan_id = self.save_plan_to_database(plan_data)
                plan_data["database_id"] = plan_id
            
            return plan_data
            
        except Exception as e:
            logger.error(f"Error creating and saving plan: {e}")
            raise


# Convenience functions for easy usage
def create_plan(goal: str, start_date: Optional[str] = None, save_to_db: bool = True) -> str:
    """
    Create a formatted plan for the given goal.
    
    Args:
        goal (str): The goal to plan for
        start_date (Optional[str]): Start date in YYYY-MM-DD format
        save_to_db (bool): Whether to save the plan to the database
        
    Returns:
        str: Formatted plan string
    """
    try:
        agent = TaskPlanningAgent()
        plan_data = agent.create_and_save_plan(goal, start_date, save_to_db)
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
