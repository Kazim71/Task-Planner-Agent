from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import json
import os

# Database configuration

# Read DATABASE_URL and validate
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing. Please set it in your deployment environment (e.g., Vercel dashboard). Example: postgresql://user:password@host:port/dbname")

# Optionally, auto-convert postgres:// to postgresql:// for compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Validate the URL format (basic check)
if not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("sqlite://")):
    raise RuntimeError(f"DATABASE_URL is invalid or unsupported: {DATABASE_URL}\nIt must start with postgresql:// or sqlite://")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


class Plan(Base):
    """
    Plan model to store task planning data.
    
    Attributes:
        id (int): Primary key, auto-incrementing
        goal (str): The main goal or objective of the plan
        steps (JSON): JSON field containing the generated plan steps
        created_at (datetime): Timestamp when the plan was created
    """
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    goal = Column(String, nullable=False, index=True)
    steps = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Plan(id={self.id}, goal='{self.goal}', created_at='{self.created_at}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Plan instance to dictionary."""
        return {
            "id": self.id,
            "goal": self.goal,
            "steps": self.steps,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def create_tables():
    """Create all tables in the database."""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    except SQLAlchemyError as e:
        print(f"Error creating database tables: {e}")
        raise


def get_db() -> Session:
    """
    Get database session.
    
    Returns:
        Session: SQLAlchemy database session
        
    Yields:
        Session: Database session that will be automatically closed
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_plan(goal: str, steps: List[Dict[str, Any]], db: Optional[Session] = None) -> Optional[Plan]:
    """
    Save a new plan to the database.
    
    Args:
        goal (str): The main goal or objective
        steps (List[Dict[str, Any]]): List of plan steps as dictionaries
        db (Optional[Session]): Database session. If None, creates a new session.
        
    Returns:
        Optional[Plan]: The created Plan object or None if error occurred
        
    Raises:
        ValueError: If goal is empty or steps is not a valid list
        SQLAlchemyError: If database operation fails
    """
    # Validate input
    if not goal or not goal.strip():
        raise ValueError("Goal cannot be empty")
    
    if not isinstance(steps, list):
        raise ValueError("Steps must be a list")
    
    if not steps:
        raise ValueError("Steps list cannot be empty")
    
    # Validate that all steps are dictionaries
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"Step {i} must be a dictionary")
    
    # Use provided session or create new one
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    
    try:
        # Create new plan
        plan = Plan(
            goal=goal.strip(),
            steps=steps
        )
        
        # Add to database
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        print(f"Plan saved successfully with ID: {plan.id}")
        return plan
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error saving plan: {e}")
        raise
    except Exception as e:
        db.rollback()
        print(f"Unexpected error saving plan: {e}")
        raise
    finally:
        if should_close_db:
            db.close()


def get_all_plans(db: Optional[Session] = None, limit: Optional[int] = None) -> List[Plan]:
    """
    Retrieve all plans from the database.
    
    Args:
        db (Optional[Session]): Database session. If None, creates a new session.
        limit (Optional[int]): Maximum number of plans to retrieve. If None, retrieves all.
        
    Returns:
        List[Plan]: List of Plan objects
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    # Use provided session or create new one
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    
    try:
        # Query all plans, ordered by creation date (newest first)
        query = db.query(Plan).order_by(Plan.created_at.desc())
        
        if limit is not None:
            query = query.limit(limit)
        
        plans = query.all()
        
        print(f"Retrieved {len(plans)} plan(s) from database")
        return plans
        
    except SQLAlchemyError as e:
        print(f"Error retrieving plans: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error retrieving plans: {e}")
        raise
    finally:
        if should_close_db:
            db.close()


def get_plan_by_id(plan_id: int, db: Optional[Session] = None) -> Optional[Plan]:
    """
    Retrieve a specific plan by ID.
    
    Args:
        plan_id (int): The ID of the plan to retrieve
        db (Optional[Session]): Database session. If None, creates a new session.
        
    Returns:
        Optional[Plan]: The Plan object if found, None otherwise
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    # Use provided session or create new one
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        
        if plan:
            print(f"Plan with ID {plan_id} found")
        else:
            print(f"Plan with ID {plan_id} not found")
        
        return plan
        
    except SQLAlchemyError as e:
        print(f"Error retrieving plan by ID: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error retrieving plan by ID: {e}")
        raise
    finally:
        if should_close_db:
            db.close()


def delete_plan(plan_id: int, db: Optional[Session] = None) -> bool:
    """
    Delete a plan by ID.
    
    Args:
        plan_id (int): The ID of the plan to delete
        db (Optional[Session]): Database session. If None, creates a new session.
        
    Returns:
        bool: True if plan was deleted, False if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    # Use provided session or create new one
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        
        if not plan:
            print(f"Plan with ID {plan_id} not found")
            return False
        
        db.delete(plan)
        db.commit()
        
        print(f"Plan with ID {plan_id} deleted successfully")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error deleting plan: {e}")
        raise
    except Exception as e:
        db.rollback()
        print(f"Unexpected error deleting plan: {e}")
        raise
    finally:
        if should_close_db:
            db.close()


def search_plans_by_goal(goal_keyword: str, db: Optional[Session] = None) -> List[Plan]:
    """
    Search plans by goal keyword.
    
    Args:
        goal_keyword (str): Keyword to search for in plan goals
        db (Optional[Session]): Database session. If None, creates a new session.
        
    Returns:
        List[Plan]: List of matching Plan objects
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    # Use provided session or create new one
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    
    try:
        if not goal_keyword or not goal_keyword.strip():
            return []
        
        # Search for plans containing the keyword in the goal
        plans = db.query(Plan).filter(
            Plan.goal.contains(goal_keyword.strip())
        ).order_by(Plan.created_at.desc()).all()
        
        print(f"Found {len(plans)} plan(s) matching keyword '{goal_keyword}'")
        return plans
        
    except SQLAlchemyError as e:
        print(f"Error searching plans: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error searching plans: {e}")
        raise
    finally:
        if should_close_db:
            db.close()


# Example usage and testing functions
def test_plan_operations():
    """Test function for plan operations"""
    try:
        # Create tables
        create_tables()
        
        # Example plan steps
        example_steps = [
            {
                "step_number": 1,
                "title": "Research and Planning",
                "description": "Gather information about the project requirements",
                "estimated_time": "2 hours",
                "priority": "high"
            },
            {
                "step_number": 2,
                "title": "Design Phase",
                "description": "Create wireframes and mockups",
                "estimated_time": "4 hours",
                "priority": "high"
            },
            {
                "step_number": 3,
                "title": "Implementation",
                "description": "Code the application",
                "estimated_time": "8 hours",
                "priority": "medium"
            }
        ]
        
        # Test saving a plan
        print("Testing plan save...")
        plan = save_plan("Build a web application", example_steps)
        if plan:
            print(f"Saved plan: {plan}")
        
        # Test retrieving all plans
        print("\nTesting plan retrieval...")
        all_plans = get_all_plans()
        for p in all_plans:
            print(f"Retrieved plan: {p}")
        
        # Test searching plans
        print("\nTesting plan search...")
        search_results = search_plans_by_goal("web")
        for p in search_results:
            print(f"Search result: {p}")
        
    except Exception as e:
        print(f"Test error: {e}")


if __name__ == "__main__":
    print("Testing models.py functions...")
    print("=" * 50)
    test_plan_operations()
