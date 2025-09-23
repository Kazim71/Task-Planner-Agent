# ==============================================================================
# 1. IMPORTS
# ==============================================================================
import os
import traceback
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Load environment variables from .env file FIRST
load_dotenv()

# Import our custom modules
from agent import TaskPlanningAgent
from models import create_tables, get_all_plans, delete_plan # <-- Added delete_plan
from exceptions import TaskPlannerException, handle_exception
from logging_config import setup_logging

# ==============================================================================
# 2. INITIAL SETUP (App, Logging, Templates)
# ==============================================================================
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("Application starting up...")
    try:
        create_tables()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"FATAL: Failed to initialize database on startup: {e}")
    yield
    logger.info("Application shutting down...")

app = FastAPI(
    title="Task Planner Agent",
    description="AI-powered task planning with Google Gemini",
    version="1.0.0",
    lifespan=lifespan
)

templates = Jinja2Templates(directory="templates")

# ==============================================================================
# 3. PYDANTIC MODELS (Request/Response Schemas)
# ==============================================================================
class PlanRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=500, description="The goal to plan for")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    save_to_db: bool = Field(True, description="Whether to save the plan to the database")

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

# ==============================================================================
# 4. API ENDPOINTS (Routes)
# ==============================================================================

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def read_root(request: Request):
    """Serve the main HTML frontend."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/plan", response_model=PlanResponse, tags=["Core"])
async def create_plan_endpoint(plan_request: PlanRequest):
    """Create a new plan for a given goal."""
    logger.info(f"Received request to create plan for goal: '{plan_request.goal}'")
    try:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            logger.error("FATAL ERROR: GEMINI_API_KEY not found in environment.")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Server is not configured with an API key."}
            )
        
        agent = TaskPlanningAgent(api_key=api_key)
        logger.info("TaskPlanningAgent initialized successfully.")

        plan_data = await agent.generate_plan(goal=plan_request.goal, start_date=plan_request.start_date)
        
        plan_id = None
        if plan_request.save_to_db:
            plan_id = agent.save_plan_to_database(plan_data)
            if plan_id:
                logger.info(f"Plan saved to database with ID: {plan_id}")

        formatted_plan = agent.format_plan_output(plan_data)

        return PlanResponse(
            success=True,
            message="Plan created successfully",
            plan_id=plan_id,
            plan_data=plan_data,
            formatted_plan=formatted_plan
        )

    except Exception as e:
        error = handle_exception(e)
        logger.error(f"Failed to create plan: {error.message}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to generate plan: {error.message}"}
        )

@app.get("/plans", response_model=PlanListResponse, tags=["Core"])
async def get_plans_endpoint():
    """Retrieve all saved plans."""
    try:
        plans = get_all_plans()
        plan_dicts = [plan.to_dict() for plan in plans]
        return PlanListResponse(
            success=True,
            message=f"Retrieved {len(plan_dicts)} plan(s)",
            plans=plan_dicts,
            total_count=len(plan_dicts)
        )
    except Exception as e:
        error = handle_exception(e)
        logger.error(f"Failed to retrieve plans: {error.message}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Failed to retrieve saved plans."}
        )

# --- NEW ENDPOINT ADDED HERE ---
@app.delete("/plans/{plan_id}", tags=["Core"])
async def delete_plan_endpoint(plan_id: int):
    """Delete a specific plan by its ID."""
    try:
        logger.info(f"Received request to delete plan with ID: {plan_id}")
        
        success = delete_plan(plan_id)
        
        if success:
            return {"success": True, "message": f"Plan {plan_id} deleted successfully."}
        else:
            raise HTTPException(status_code=404, detail=f"Plan with ID {plan_id} not found.")

    except Exception as e:
        error = handle_exception(e)
        logger.error(f"Failed to delete plan {plan_id}: {error.message}")
        raise HTTPException(status_code=500, detail="Failed to delete the plan due to a server error.")

# ==============================================================================
# 5. HEALTH ENDPOINT
# ==============================================================================

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Provides a simple health check of the service."""
    return {"status": "healthy"}