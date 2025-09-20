"""
Input validation utilities for the Task Planner Agent.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from exceptions import ValidationError, ErrorCode


class InputValidator:
    """Comprehensive input validation for all API endpoints."""
    
    # Constants
    MIN_GOAL_LENGTH = 3
    MAX_GOAL_LENGTH = 1000
    MAX_SEARCH_LENGTH = 100
    MAX_LIMIT = 1000
    DATE_FORMAT = "%Y-%m-%d"
    
    @staticmethod
    def validate_goal(goal: Any) -> str:
        """
        Validate goal input.
        
        Args:
            goal: The goal to validate
            
        Returns:
            str: Validated and cleaned goal
            
        Raises:
            ValidationError: If goal is invalid
        """
        if goal is None:
            raise ValidationError(
                "Goal is required",
                field="goal",
                value=goal
            )
        
        if not isinstance(goal, str):
            raise ValidationError(
                "Goal must be a string",
                field="goal",
                value=type(goal).__name__
            )
        
        goal = goal.strip()
        
        if not goal:
            raise ValidationError(
                "Goal cannot be empty",
                field="goal",
                value=goal
            )
        
        if len(goal) < InputValidator.MIN_GOAL_LENGTH:
            raise ValidationError(
                f"Goal must be at least {InputValidator.MIN_GOAL_LENGTH} characters long",
                field="goal",
                value=goal
            )
        
        if len(goal) > InputValidator.MAX_GOAL_LENGTH:
            raise ValidationError(
                f"Goal must be no more than {InputValidator.MAX_GOAL_LENGTH} characters long",
                field="goal",
                value=goal
            )
        
        # Check for potentially malicious content
        if InputValidator._contains_suspicious_content(goal):
            raise ValidationError(
                "Goal contains potentially inappropriate content",
                field="goal",
                value=goal
            )
        
        return goal
    
    @staticmethod
    def validate_start_date(start_date: Any) -> Optional[str]:
        """
        Validate start date input.
        
        Args:
            start_date: The start date to validate
            
        Returns:
            Optional[str]: Validated date string or None
            
        Raises:
            ValidationError: If start date is invalid
        """
        if start_date is None:
            return None
        
        if not isinstance(start_date, str):
            raise ValidationError(
                "Start date must be a string",
                field="start_date",
                value=type(start_date).__name__
            )
        
        start_date = start_date.strip()
        
        if not start_date:
            return None
        
        try:
            # Validate date format
            parsed_date = datetime.strptime(start_date, InputValidator.DATE_FORMAT)
            
            # Check if date is not too far in the past
            today = datetime.now().date()
            if parsed_date.date() < today:
                raise ValidationError(
                    "Start date cannot be in the past",
                    field="start_date",
                    value=start_date
                )
            
            # Check if date is not too far in the future (1 year)
            max_future_date = datetime.now().replace(year=datetime.now().year + 1).date()
            if parsed_date.date() > max_future_date:
                raise ValidationError(
                    "Start date cannot be more than 1 year in the future",
                    field="start_date",
                    value=start_date
                )
            
            return start_date
            
        except ValueError as e:
            raise ValidationError(
                f"Invalid date format. Use {InputValidator.DATE_FORMAT}",
                field="start_date",
                value=start_date
            )
    
    @staticmethod
    def validate_save_to_db(save_to_db: Any) -> bool:
        """
        Validate save_to_db input.
        
        Args:
            save_to_db: The save_to_db value to validate
            
        Returns:
            bool: Validated boolean value
            
        Raises:
            ValidationError: If save_to_db is invalid
        """
        if save_to_db is None:
            return True  # Default to True
        
        if isinstance(save_to_db, bool):
            return save_to_db
        
        if isinstance(save_to_db, str):
            lower_val = save_to_db.lower()
            if lower_val in ['true', '1', 'yes', 'on']:
                return True
            elif lower_val in ['false', '0', 'no', 'off']:
                return False
            else:
                raise ValidationError(
                    "save_to_db must be a boolean or valid string representation",
                    field="save_to_db",
                    value=save_to_db
                )
        
        raise ValidationError(
            "save_to_db must be a boolean",
            field="save_to_db",
            value=type(save_to_db).__name__
        )
    
    @staticmethod
    def validate_plan_id(plan_id: Any) -> int:
        """
        Validate plan ID input.
        
        Args:
            plan_id: The plan ID to validate
            
        Returns:
            int: Validated plan ID
            
        Raises:
            ValidationError: If plan ID is invalid
        """
        if plan_id is None:
            raise ValidationError(
                "Plan ID is required",
                field="plan_id",
                value=plan_id
            )
        
        try:
            plan_id = int(plan_id)
        except (ValueError, TypeError):
            raise ValidationError(
                "Plan ID must be a valid integer",
                field="plan_id",
                value=plan_id
            )
        
        if plan_id < 1:
            raise ValidationError(
                "Plan ID must be a positive integer",
                field="plan_id",
                value=plan_id
            )
        
        if plan_id > 2**31 - 1:  # Max 32-bit signed integer
            raise ValidationError(
                "Plan ID is too large",
                field="plan_id",
                value=plan_id
            )
        
        return plan_id
    
    @staticmethod
    def validate_limit(limit: Any) -> Optional[int]:
        """
        Validate limit parameter.
        
        Args:
            limit: The limit to validate
            
        Returns:
            Optional[int]: Validated limit or None
            
        Raises:
            ValidationError: If limit is invalid
        """
        if limit is None:
            return None
        
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            raise ValidationError(
                "Limit must be a valid integer",
                field="limit",
                value=limit
            )
        
        if limit < 1:
            raise ValidationError(
                "Limit must be at least 1",
                field="limit",
                value=limit
            )
        
        if limit > InputValidator.MAX_LIMIT:
            raise ValidationError(
                f"Limit cannot exceed {InputValidator.MAX_LIMIT}",
                field="limit",
                value=limit
            )
        
        return limit
    
    @staticmethod
    def validate_search_term(search: Any) -> Optional[str]:
        """
        Validate search term input.
        
        Args:
            search: The search term to validate
            
        Returns:
            Optional[str]: Validated search term or None
            
        Raises:
            ValidationError: If search term is invalid
        """
        if search is None:
            return None
        
        if not isinstance(search, str):
            raise ValidationError(
                "Search term must be a string",
                field="search",
                value=type(search).__name__
            )
        
        search = search.strip()
        
        if not search:
            return None
        
        if len(search) > InputValidator.MAX_SEARCH_LENGTH:
            raise ValidationError(
                f"Search term must be no more than {InputValidator.MAX_SEARCH_LENGTH} characters long",
                field="search",
                value=search
            )
        
        # Check for potentially malicious content
        if InputValidator._contains_suspicious_content(search):
            raise ValidationError(
                "Search term contains potentially inappropriate content",
                field="search",
                value=search
            )
        
        return search
    
    @staticmethod
    def validate_plan_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete plan request data.
        
        Args:
            data: The request data to validate
            
        Returns:
            Dict[str, Any]: Validated and cleaned data
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError(
                "Request data must be a dictionary",
                field="data",
                value=type(data).__name__
            )
        
        validated_data = {}
        
        # Validate goal (required)
        if "goal" not in data:
            raise ValidationError(
                "Goal is required",
                field="goal"
            )
        validated_data["goal"] = InputValidator.validate_goal(data["goal"])
        
        # Validate start_date (optional)
        validated_data["start_date"] = InputValidator.validate_start_date(
            data.get("start_date")
        )
        
        # Validate save_to_db (optional, defaults to True)
        validated_data["save_to_db"] = InputValidator.validate_save_to_db(
            data.get("save_to_db", True)
        )
        
        return validated_data
    
    @staticmethod
    def validate_plans_query_params(limit: Any = None, search: Any = None) -> Dict[str, Any]:
        """
        Validate plans query parameters.
        
        Args:
            limit: The limit parameter
            search: The search parameter
            
        Returns:
            Dict[str, Any]: Validated parameters
            
        Raises:
            ValidationError: If validation fails
        """
        return {
            "limit": InputValidator.validate_limit(limit),
            "search": InputValidator.validate_search_term(search)
        }
    
    @staticmethod
    def _contains_suspicious_content(text: str) -> bool:
        """
        Check if text contains potentially suspicious content.
        
        Args:
            text: The text to check
            
        Returns:
            bool: True if suspicious content is found
        """
        # Basic patterns for potentially malicious content
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:text/html',  # Data URLs
            r'vbscript:',  # VBScript URLs
            r'on\w+\s*=',  # Event handlers
            r'<iframe[^>]*>',  # Iframe tags
            r'<object[^>]*>',  # Object tags
            r'<embed[^>]*>',  # Embed tags
        ]
        
        text_lower = text.lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True
        
        # Check for excessive special characters (potential injection)
        special_char_count = sum(1 for c in text if not c.isalnum() and not c.isspace() and c not in '.,!?-()[]{}')
        if special_char_count > len(text) * 0.3:  # More than 30% special characters
            return True
        
        return False


def validate_api_key(api_key: str, service_name: str) -> None:
    """
    Validate API key format.
    
    Args:
        api_key: The API key to validate
        service_name: The name of the service
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key:
        raise ValidationError(
            f"{service_name} API key is required",
            field=f"{service_name.lower()}_api_key"
        )
    
    if not isinstance(api_key, str):
        raise ValidationError(
            f"{service_name} API key must be a string",
            field=f"{service_name.lower()}_api_key",
            value=type(api_key).__name__
        )
    
    api_key = api_key.strip()
    
    if not api_key:
        raise ValidationError(
            f"{service_name} API key cannot be empty",
            field=f"{service_name.lower()}_api_key"
        )
    
    # Basic format validation based on service
    if service_name.lower() == "gemini":
        if not api_key.startswith("AIza"):
            raise ValidationError(
                "Gemini API key appears to be invalid (should start with 'AIza')",
                field="gemini_api_key"
            )
    elif service_name.lower() == "tavily":
        if len(api_key) < 20:
            raise ValidationError(
                "Tavily API key appears to be too short",
                field="tavily_api_key"
            )
    elif service_name.lower() == "openweather":
        if len(api_key) < 20:
            raise ValidationError(
                "OpenWeatherMap API key appears to be too short",
                field="openweather_api_key"
            )
