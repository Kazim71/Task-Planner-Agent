# Minimal dependency test endpoint for plan generation
@app.get("/test-plan")
async def test_plan_minimal():
    import traceback
    from agent import TaskPlanningAgent
    import logging
    logger = logging.getLogger("plan_test_minimal")
    result = {"success": False, "steps": []}
    try:
        logger.info("Instantiating TaskPlanningAgent (minimal test)...")
        result["steps"].append("Instantiating TaskPlanningAgent (minimal test)...")
        agent = TaskPlanningAgent()
        # Patch agent to mock enrichment (bypass web search and weather)
        async def mock_enrich(plan_data, goal, logger=None):
            if logger:
                logger.info("[MOCK] Skipping web search and weather enrichment.")
            result["steps"].append("[MOCK] Skipping web search and weather enrichment.")
            return plan_data
        agent._enrich_plan_with_tools = mock_enrich
        logger.info("Calling generate_plan with goal: 'Plan a morning routine' (minimal dependencies)")
        result["steps"].append("Calling generate_plan with goal: 'Plan a morning routine' (minimal dependencies)")
        plan = await agent.generate_plan("Plan a morning routine")
        logger.info("Plan generated successfully (minimal test).")
        result["steps"].append("Plan generated successfully (minimal test).")
        result["plan"] = plan
        result["success"] = True
    except Exception as e:
        logger.error(f"Plan generation failed (minimal test): {e}\n{traceback.format_exc()}")
        result["steps"].append(f"Plan generation failed (minimal test): {e}")
        result["error"] = str(e)
        result["trace"] = traceback.format_exc()
    return result
# Simple backend test endpoint for plan generation
@app.get("/test-plan-generation")
async def test_plan_generation():
    import traceback
    from agent import TaskPlanningAgent
    import logging
    logger = logging.getLogger("plan_test")
    result = {"success": False, "steps": []}
    try:
        logger.info("Instantiating TaskPlanningAgent...")
        result["steps"].append("Instantiating TaskPlanningAgent...")
        agent = TaskPlanningAgent()
        logger.info("Calling generate_plan with goal: 'Plan a morning routine'")
        result["steps"].append("Calling generate_plan with goal: 'Plan a morning routine'")
        plan = await agent.generate_plan("Plan a morning routine")
        logger.info("Plan generated successfully.")
        result["steps"].append("Plan generated successfully.")
        result["plan"] = plan
        result["success"] = True
    except Exception as e:
        logger.error(f"Plan generation failed: {e}\n{traceback.format_exc()}")
        result["steps"].append(f"Plan generation failed: {e}")
        result["error"] = str(e)
        result["trace"] = traceback.format_exc()
    return result
# Debug endpoint for service connectivity
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import sqlite3
import traceback
from agent import TaskPlanningAgent
import tools

@app.get("/debug")
async def debug_connectivity():
    statuses = {}
    # Gemini API
    try:
        agent = TaskPlanningAgent()
        # Minimal Gemini API call: check model exists and can generate a trivial response
        result = agent.model.generate_content("Say hello.")
        text = getattr(result, 'text', None) or (getattr(result, 'parts', [None])[0] if hasattr(result, 'parts') else None)
        if text:
            statuses['gemini'] = {"success": True}
        else:
            statuses['gemini'] = {"success": False, "error": "No response text from Gemini."}
    except Exception as e:
        statuses['gemini'] = {"success": False, "error": str(e), "trace": traceback.format_exc()}

    # Tavily API
    try:
        tavily_result = tools.tavily_web_search("test connectivity", max_results=1)
        if tavily_result and isinstance(tavily_result, (list, str)) and len(tavily_result) > 0:
            statuses['tavily'] = {"success": True}
        else:
            statuses['tavily'] = {"success": False, "error": "No results from Tavily."}
    except Exception as e:
        statuses['tavily'] = {"success": False, "error": str(e), "trace": traceback.format_exc()}

    # OpenWeatherMap API
    try:
        weather_result = tools.get_weather("London")
        if weather_result and (isinstance(weather_result, dict) or isinstance(weather_result, str)):
            statuses['openweathermap'] = {"success": True}
        else:
            statuses['openweathermap'] = {"success": False, "error": "No weather data returned."}
    except Exception as e:
        statuses['openweathermap'] = {"success": False, "error": str(e), "trace": traceback.format_exc()}

    # Database connectivity
    try:
        db_path = os.getenv('DB_PATH', 'task_planner.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
        _ = cursor.fetchone()
        conn.close()
        statuses['database'] = {"success": True}
    except Exception as e:
        statuses['database'] = {"success": False, "error": str(e), "trace": traceback.format_exc()}

    return JSONResponse(content={"services": statuses})
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime
import traceback

# Import our modules
from agent import TaskPlanningAgent, create_plan, get_all_saved_plans
from models import create_tables, get_plan_by_id, delete_plan, search_plans_by_goal, get_all_plans
from exceptions import (
    TaskPlannerException, ValidationError, AuthenticationError, 
    ResourceNotFoundError, ExternalServiceError, DatabaseError,
    ConfigurationError, handle_exception, create_error_response
)
from validators import InputValidator, validate_api_key

# Configure logging
from logging_config import setup_logging, get_logger, log_api_request, log_database_operation, log_security_event, sanitize_log_data

# Set up comprehensive logging
logger = setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    log_file=os.getenv('LOG_FILE')
)

# Initialize FastAPI app
app = FastAPI(
    title="Task Planner Agent",
    description="AI-powered task planning with Google Gemini",
    version="1.0.0"
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing and response details."""
    import time
    start_time = time.time()
    
    # Get client information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Log request start
    logger.info(f"Request started - {request.method} {request.url.path} from {client_ip}")
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log API request details
        log_api_request(
            logger=logger,
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            response_time=process_time,
            user_agent=user_agent,
            ip_address=client_ip
        )
        
        # Log security events for suspicious requests
        if response.status_code >= 400:
            log_security_event(
                logger=logger,
                event_type="HTTP_ERROR",
                details=f"{request.method} {request.url.path} returned {response.status_code}",
                severity="WARNING",
                ip_address=client_ip,
                user_agent=user_agent
            )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed - {request.method} {request.url.path} - Error: {str(e)}")
        
        # Log security event for request failures
        log_security_event(
            logger=logger,
            event_type="REQUEST_FAILURE",
            details=f"{request.method} {request.url.path} failed with exception: {str(e)}",
            severity="ERROR",
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        raise

# Setup templates
templates = Jinja2Templates(directory="templates")

# Pydantic models for request/response
class PlanRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=500, description="The goal to plan for")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    save_to_db: bool = Field(True, description="Whether to save the plan to database")

class PlanResponse(BaseModel):
    success: bool
    message: str
    plan_id: Optional[int] = None
    plan_data: Optional[Dict[str, Any]] = None
    formatted_plan: Optional[str] = None

class PlanListResponse(BaseModel):
    success: bool
    message: str
    plans: List[Dict[str, Any]]
    total_count: int

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    try:
        create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Root endpoint - serves the HTML frontend
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serve the main HTML frontend with goal input form.
    
    Returns:
        HTMLResponse: Rendered HTML template
    """
    try:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "title": "Task Planner Agent",
            "current_year": datetime.now().year
        })
    except Exception as e:
        logger.error(f"Error serving frontend: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error</title></head>
                <body>
                    <h1>Error</h1>
                    <p>Failed to load the application: {e}</p>
                </body>
            </html>
            """,
            status_code=500
        )

# Create a new plan
@app.post("/plan", response_model=PlanResponse)
async def create_plan_endpoint(plan_request: PlanRequest):
    """
    Create a new plan for the given goal.
    
    Args:
        plan_request (PlanRequest): The plan request data
        
    Returns:
        PlanResponse: The created plan data or error information
    """
    try:
        logger.info(f"Creating plan for goal: {plan_request.goal}")
        
        # Validate input using the validator
        try:
            validated_data = InputValidator.validate_plan_request({
                "goal": plan_request.goal,
                "start_date": plan_request.start_date,
                "save_to_db": plan_request.save_to_db
            })
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return PlanResponse(
                success=False,
                message=e.message,
                plan_id=None,
                plan_data=None,
                formatted_plan=None
            )
        
        # Check for required API key
        try:
            gemini_key = os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                raise ConfigurationError("GEMINI_API_KEY environment variable is not set", "GEMINI_API_KEY")
            validate_api_key(gemini_key, "Gemini")
        except (ConfigurationError, ValidationError) as e:
            logger.error(f"API key validation failed: {e.message}")
            return PlanResponse(
                success=False,
                message=e.message,
                plan_id=None,
                plan_data=None,
                formatted_plan=None
            )
        
        # Create the planning agent
        try:
            agent = TaskPlanningAgent()
            logger.info("TaskPlanningAgent initialized successfully")
        except Exception as e:
            error = handle_exception(e)
            logger.error(f"Failed to initialize TaskPlanningAgent: {error.message}")
            return PlanResponse(
                success=False,
                message=error.message,
                plan_id=None,
                plan_data=None,
                formatted_plan=None
            )
        
        # Generate the plan
        try:
            plan_data = await agent.generate_plan(
                goal=validated_data["goal"],
                start_date=validated_data["start_date"]
            )
            logger.info("Plan generated successfully")
        except Exception as e:
            error = handle_exception(e)
            logger.error(f"Failed to generate plan: {error.message}")
            return PlanResponse(
                success=False,
                message=error.message,
                plan_id=None,
                plan_data=None,
                formatted_plan=None
            )
        
        # Save to database if requested
        plan_id = None
        if validated_data["save_to_db"]:
            try:
                plan_id = agent.save_plan_to_database(plan_data)
                if plan_id:
                    logger.info(f"Plan saved to database with ID: {plan_id}")
                else:
                    logger.warning("Failed to save plan to database - no ID returned")
            except Exception as e:
                error = handle_exception(e)
                logger.error(f"Database save error: {error.message}")
                # Continue without failing - plan was generated successfully
                logger.info("Continuing without database save due to error")
        
        # Format the plan for display
        try:
            formatted_plan = agent.format_plan_output(plan_data)
            logger.info("Plan formatted successfully")
        except Exception as e:
            error = handle_exception(e)
            logger.error(f"Failed to format plan: {error.message}")
            formatted_plan = f"Plan generated but formatting failed: {error.message}"
        
        return PlanResponse(
            success=True,
            message="Plan created successfully",
            plan_id=plan_id,
            plan_data=plan_data,
            formatted_plan=formatted_plan
        )
        
    except TaskPlannerException as e:
        logger.error(f"TaskPlannerException in create_plan_endpoint: {e.message}")
        return PlanResponse(
            success=False,
            message=e.message,
            plan_id=None,
            plan_data=None,
            formatted_plan=None
        )
    except Exception as e:
        error = handle_exception(e)
        logger.error(f"Unexpected error in create_plan_endpoint: {error.message}")
        return PlanResponse(
            success=False,
            message=error.message,
            plan_id=None,
            plan_data=None,
            formatted_plan=None
        )

# Get all plans
@app.get("/plans", response_model=PlanListResponse)
async def get_plans_endpoint(limit: Optional[int] = None, search: Optional[str] = None):
    """
    Retrieve all saved plans from the database.
    
    Args:
        limit (Optional[int]): Maximum number of plans to return
        search (Optional[str]): Search term to filter plans by goal
        
    Returns:
        PlanListResponse: List of all saved plans
    """
    try:
        logger.info(f"Retrieving plans - limit: {limit}, search: {search}")
        
        # Validate query parameters
        try:
            validated_params = InputValidator.validate_plans_query_params(limit, search)
            limit = validated_params["limit"]
            search = validated_params["search"]
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return PlanListResponse(
                success=False,
                message=e.message,
                plans=[],
                total_count=0
            )
        
        # Query database
        try:
            if search:
                # Search plans by goal keyword
                logger.info(f"Searching plans with keyword: {search}")
                plans = search_plans_by_goal(search)
            else:
                # Get all plans
                logger.info("Retrieving all plans")
                plans = get_all_plans(limit=limit)
        except Exception as e:
            error = handle_exception(e)
            logger.error(f"Database query failed: {error.message}")
            return PlanListResponse(
                success=False,
                message=error.message,
                plans=[],
                total_count=0
            )
        
        # Convert to dictionaries
        try:
            plan_dicts = [plan.to_dict() for plan in plans]
            logger.info(f"Successfully converted {len(plan_dicts)} plans to dictionaries")
        except Exception as e:
            error = handle_exception(e)
            logger.error(f"Failed to convert plans to dictionaries: {error.message}")
            return PlanListResponse(
                success=False,
                message=error.message,
                plans=[],
                total_count=0
            )
        
        return PlanListResponse(
            success=True,
            message=f"Retrieved {len(plan_dicts)} plan(s)",
            plans=plan_dicts,
            total_count=len(plan_dicts)
        )
        
    except TaskPlannerException as e:
        logger.error(f"TaskPlannerException in get_plans_endpoint: {e.message}")
        return PlanListResponse(
            success=False,
            message=e.message,
            plans=[],
            total_count=0
        )
    except Exception as e:
        error = handle_exception(e)
        logger.error(f"Unexpected error in get_plans_endpoint: {error.message}")
        return PlanListResponse(
            success=False,
            message=error.message,
            plans=[],
            total_count=0
        )

# Get a specific plan by ID
@app.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan_endpoint(plan_id: int):
    """
    Retrieve a specific plan by its ID.
    
    Args:
        plan_id (int): The ID of the plan to retrieve
        
    Returns:
        PlanResponse: The requested plan data or error information
    """
    try:
        logger.info(f"Retrieving plan with ID: {plan_id}")
        
        # Validate plan_id
        try:
            validated_plan_id = InputValidator.validate_plan_id(plan_id)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return PlanResponse(
                success=False,
                message=e.message,
                plan_id=plan_id,
                plan_data=None,
                formatted_plan=None
            )
        
        # Get the plan from database
        try:
            plan = get_plan_by_id(validated_plan_id)
        except Exception as e:
            error = handle_exception(e)
            logger.error(f"Database query failed for plan ID {validated_plan_id}: {error.message}")
            return PlanResponse(
                success=False,
                message=error.message,
                plan_id=validated_plan_id,
                plan_data=None,
                formatted_plan=None
            )
        
        if not plan:
            logger.warning(f"Plan with ID {validated_plan_id} not found")
            return PlanResponse(
                success=False,
                message=f"Plan with ID {validated_plan_id} not found",
                plan_id=validated_plan_id,
                plan_data=None,
                formatted_plan=None
            )
        
        # Convert to dictionary
        try:
            plan_dict = plan.to_dict()
            logger.info(f"Successfully retrieved plan {validated_plan_id}")
        except Exception as e:
            error = handle_exception(e)
            logger.error(f"Failed to convert plan {validated_plan_id} to dictionary: {error.message}")
            return PlanResponse(
                success=False,
                message=error.message,
                plan_id=validated_plan_id,
                plan_data=None,
                formatted_plan=None
            )
        
        return PlanResponse(
            success=True,
            message=f"Plan {validated_plan_id} retrieved successfully",
            plan_id=validated_plan_id,
            plan_data=plan_dict,
            formatted_plan=None  # Raw data, not formatted
        )
        
    except TaskPlannerException as e:
        logger.error(f"TaskPlannerException in get_plan_endpoint: {e.message}")
        return PlanResponse(
            success=False,
            message=e.message,
            plan_id=plan_id,
            plan_data=None,
            formatted_plan=None
        )
    except Exception as e:
        error = handle_exception(e)
        logger.error(f"Unexpected error in get_plan_endpoint: {error.message}")
        return PlanResponse(
            success=False,
            message=error.message,
            plan_id=plan_id,
            plan_data=None,
            formatted_plan=None
        )

# Delete a plan
@app.delete("/plans/{plan_id}", response_model=PlanResponse)
async def delete_plan_endpoint(plan_id: int):
    """
    Delete a specific plan by its ID.
    
    Args:
        plan_id (int): The ID of the plan to delete
        
    Returns:
        PlanResponse: Deletion confirmation or error information
    """
    try:
        logger.info(f"Deleting plan with ID: {plan_id}")
        
        # Validate plan_id
        try:
            validated_plan_id = InputValidator.validate_plan_id(plan_id)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return PlanResponse(
                success=False,
                message=e.message,
                plan_id=plan_id,
                plan_data=None,
                formatted_plan=None
            )
        
        # Delete the plan
        try:
            success = delete_plan(validated_plan_id)
        except Exception as e:
            error = handle_exception(e)
            logger.error(f"Database delete operation failed for plan ID {validated_plan_id}: {error.message}")
            return PlanResponse(
                success=False,
                message=error.message,
                plan_id=validated_plan_id,
                plan_data=None,
                formatted_plan=None
            )
        
        if not success:
            logger.warning(f"Plan with ID {validated_plan_id} not found for deletion")
            return PlanResponse(
                success=False,
                message=f"Plan with ID {validated_plan_id} not found",
                plan_id=validated_plan_id,
                plan_data=None,
                formatted_plan=None
            )
        
        logger.info(f"Successfully deleted plan {validated_plan_id}")
        return PlanResponse(
            success=True,
            message=f"Plan {validated_plan_id} deleted successfully",
            plan_id=validated_plan_id,
            plan_data=None,
            formatted_plan=None
        )
        
    except TaskPlannerException as e:
        logger.error(f"TaskPlannerException in delete_plan_endpoint: {e.message}")
        return PlanResponse(
            success=False,
            message=e.message,
            plan_id=plan_id,
            plan_data=None,
            formatted_plan=None
        )
    except Exception as e:
        error = handle_exception(e)
        logger.error(f"Unexpected error in delete_plan_endpoint: {error.message}")
        return PlanResponse(
            success=False,
            message=error.message,
            plan_id=plan_id,
            plan_data=None,
            formatted_plan=None
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint to verify all services are working.
    
    Returns:
        Dict: Detailed health status information for all services
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "environment": {},
        "errors": []
    }
    
    try:
        logger.info("Performing comprehensive health check")
        
        # Check environment variables
        logger.info("Checking environment variables...")
        env_vars = {
            "GEMINI_API_KEY": os.getenv('GEMINI_API_KEY'),
            "TAVILY_API_KEY": os.getenv('TAVILY_API_KEY'),
            "OPENWEATHER_API_KEY": os.getenv('OPENWEATHER_API_KEY'),
            "DATABASE_URL": os.getenv('DATABASE_URL', 'sqlite:///./task_planner.db')
        }
        
        for var, value in env_vars.items():
            if value:
                health_data["environment"][var] = "configured"
            else:
                health_data["environment"][var] = "missing"
                if var == "GEMINI_API_KEY":
                    health_data["errors"].append(f"Required environment variable {var} is not set")
        
        # Check database connection
        logger.info("Checking database connection...")
        try:
            plans = get_all_plans(limit=1)
            health_data["services"]["database"] = {
                "status": "connected",
                "type": "SQLite",
                "plans_count": len(plans),
                "message": "Database connection successful"
            }
            logger.info(f"Database health check passed - {len(plans)} plans found")
        except Exception as e:
            health_data["services"]["database"] = {
                "status": "disconnected",
                "type": "SQLite",
                "error": str(e),
                "message": "Database connection failed"
            }
            health_data["errors"].append(f"Database error: {str(e)}")
            logger.error(f"Database health check failed: {e}")
        
        # Check Gemini API connectivity
        logger.info("Checking Gemini API connectivity...")
        try:
            if env_vars["GEMINI_API_KEY"]:
                # Try to initialize the agent to test API connectivity
                agent = TaskPlanningAgent()
                health_data["services"]["gemini_api"] = {
                    "status": "connected",
                    "type": "Google Gemini 2.5 Pro",
                    "message": "API key valid and agent initialized successfully"
                }
                logger.info("Gemini API health check passed")
            else:
                health_data["services"]["gemini_api"] = {
                    "status": "not_configured",
                    "type": "Google Gemini 2.5 Pro",
                    "message": "API key not provided"
                }
        except Exception as e:
            health_data["services"]["gemini_api"] = {
                "status": "error",
                "type": "Google Gemini 2.5 Pro",
                "error": str(e),
                "message": "API connection failed"
            }
            health_data["errors"].append(f"Gemini API error: {str(e)}")
            logger.error(f"Gemini API health check failed: {e}")
        
        # Check external APIs (optional)
        logger.info("Checking external APIs...")
        
        # Check Tavily API
        if env_vars["TAVILY_API_KEY"]:
            health_data["services"]["tavily_api"] = {
                "status": "configured",
                "type": "Tavily Web Search",
                "message": "API key configured (not tested for connectivity)"
            }
        else:
            health_data["services"]["tavily_api"] = {
                "status": "not_configured",
                "type": "Tavily Web Search",
                "message": "API key not provided (optional)"
            }
        
        # Check OpenWeatherMap API
        if env_vars["OPENWEATHER_API_KEY"]:
            health_data["services"]["openweather_api"] = {
                "status": "configured",
                "type": "OpenWeatherMap",
                "message": "API key configured (not tested for connectivity)"
            }
        else:
            health_data["services"]["openweather_api"] = {
                "status": "not_configured",
                "type": "OpenWeatherMap",
                "message": "API key not provided (optional)"
            }
        
        # Check FastAPI server status
        health_data["services"]["fastapi_server"] = {
            "status": "running",
            "type": "FastAPI",
            "version": "0.104.1",
            "message": "Server is running and responding"
        }
        
        # Determine overall health status
        critical_services = ["database", "gemini_api"]
        degraded_services = ["tavily_api", "openweather_api"]
        
        critical_failed = any(
            health_data["services"].get(service, {}).get("status") not in ["connected", "running"]
            for service in critical_services
        )
        
        if critical_failed:
            health_data["status"] = "unhealthy"
        elif any(
            health_data["services"].get(service, {}).get("status") == "not_configured"
            for service in degraded_services
        ):
            health_data["status"] = "degraded"
        else:
            health_data["status"] = "healthy"
        
        # Add summary
        health_data["summary"] = {
            "total_services": len(health_data["services"]),
            "healthy_services": len([
                s for s in health_data["services"].values()
                if s.get("status") in ["connected", "running", "configured"]
            ]),
            "error_count": len(health_data["errors"]),
            "recommendations": []
        }
        
        # Add recommendations
        if health_data["environment"].get("GEMINI_API_KEY") == "missing":
            health_data["summary"]["recommendations"].append("Set GEMINI_API_KEY environment variable")
        if health_data["services"].get("database", {}).get("status") != "connected":
            health_data["summary"]["recommendations"].append("Check database connection and configuration")
        if health_data["environment"].get("TAVILY_API_KEY") == "missing":
            health_data["summary"]["recommendations"].append("Set TAVILY_API_KEY for web search enrichment (optional)")
        if health_data["environment"].get("OPENWEATHER_API_KEY") == "missing":
            health_data["summary"]["recommendations"].append("Set OPENWEATHER_API_KEY for weather information (optional)")
        
        logger.info(f"Health check completed - Status: {health_data['status']}")
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        logger.error(traceback.format_exc())
        
        health_data.update({
            "status": "unhealthy",
            "error": str(e),
            "services": {
                "fastapi_server": {
                    "status": "error",
                    "type": "FastAPI",
                    "error": str(e),
                    "message": "Health check itself failed"
                }
            }
        })
        
        return health_data

# API documentation endpoint
@app.get("/docs")
async def api_docs():
    """
    Redirect to the interactive API documentation.
    
    Returns:
        RedirectResponse: Redirect to /docs
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with proper logging and JSON response."""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now().isoformat()
        }
    )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors with custom response."""
    logger.warning(f"404 error: {exc.detail}")
    return JSONResponse(
        status_code=404,
        content=create_error_response(
            ResourceNotFoundError(
                message="The requested resource was not found",
                resource_type="endpoint",
                resource_id=request.url.path
            )
        )
    )

@app.exception_handler(422)
async def validation_error_handler(request: Request, exc: Exception):
    """Handle validation errors with detailed information."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            ValidationError(
                message="Invalid request data. Please check your input.",
                details={"validation_errors": str(exc)}
            )
        )
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors with custom response."""
    logger.error(f"Internal server error: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            TaskPlannerException(
                message="An unexpected error occurred. Please try again later.",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                details={"original_error": str(exc)}
            )
        )
    )

@app.exception_handler(TaskPlannerException)
async def task_planner_exception_handler(request: Request, exc: TaskPlannerException):
    """Handle TaskPlannerException."""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc)
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    error = handle_exception(exc)
    logger.error(f"Unhandled exception: {error.message}")
    return JSONResponse(
        status_code=error.status_code,
        content=create_error_response(error)
    )

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
