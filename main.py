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
from models import create_tables, get_plan_by_id, delete_plan, search_plans_by_goal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Task Planner Agent",
    description="AI-powered task planning with Google Gemini",
    version="1.0.0"
)

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
        
        # Validate start_date if provided
        if plan_request.start_date:
            try:
                datetime.strptime(plan_request.start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        # Create the planning agent
        agent = TaskPlanningAgent()
        
        # Generate the plan
        plan_data = agent.generate_plan(
            goal=plan_request.goal,
            start_date=plan_request.start_date
        )
        
        # Save to database if requested
        plan_id = None
        if plan_request.save_to_db:
            plan_id = agent.save_plan_to_database(plan_data)
            if not plan_id:
                logger.warning("Failed to save plan to database")
        
        # Format the plan for display
        formatted_plan = agent.format_plan_output(plan_data)
        
        return PlanResponse(
            success=True,
            message="Plan created successfully",
            plan_id=plan_id,
            plan_data=plan_data,
            formatted_plan=formatted_plan
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create plan: {str(e)}"
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
        logger.info("Retrieving all plans")
        
        if search:
            # Search plans by goal keyword
            plans = search_plans_by_goal(search)
        else:
            # Get all plans
            plans = get_all_plans(limit=limit)
        
        # Convert to dictionaries
        plan_dicts = [plan.to_dict() for plan in plans]
        
        return PlanListResponse(
            success=True,
            message=f"Retrieved {len(plan_dicts)} plan(s)",
            plans=plan_dicts,
            total_count=len(plan_dicts)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving plans: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve plans: {str(e)}"
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
        
        # Get the plan from database
        plan = get_plan_by_id(plan_id)
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail=f"Plan with ID {plan_id} not found"
            )
        
        # Convert to dictionary
        plan_dict = plan.to_dict()
        
        return PlanResponse(
            success=True,
            message=f"Plan {plan_id} retrieved successfully",
            plan_id=plan_id,
            plan_data=plan_dict,
            formatted_plan=None  # Raw data, not formatted
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving plan {plan_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve plan: {str(e)}"
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
        
        # Delete the plan
        success = delete_plan(plan_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Plan with ID {plan_id} not found"
            )
        
        return PlanResponse(
            success=True,
            message=f"Plan {plan_id} deleted successfully",
            plan_id=plan_id,
            plan_data=None,
            formatted_plan=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plan {plan_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete plan: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    
    Returns:
        Dict: Health status information
    """
    try:
        # Check if we can connect to the database
        plans = get_all_plans(limit=1)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "plans_count": len(plans)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

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

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors with custom response."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Not Found",
            "message": "The requested resource was not found"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors with custom response."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
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
