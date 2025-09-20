#!/usr/bin/env python3
"""
Direct test script for the Task Planning Agent.
This script tests the agent directly without the FastAPI server.
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_direct():
    """Test the agent directly without FastAPI."""
    print("🤖 Testing Task Planning Agent Directly")
    print("=" * 50)
    
    # Check environment variables
    print("🔍 Checking environment variables...")
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print(f"✅ GEMINI_API_KEY: {'*' * (len(gemini_key) - 4) + gemini_key[-4:]}")
    else:
        print("❌ GEMINI_API_KEY: Not set")
        print("   Set it with: export GEMINI_API_KEY='your_key_here'")
        return False
    
    tavily_key = os.getenv('TAVILY_API_KEY')
    if tavily_key:
        print(f"✅ TAVILY_API_KEY: {'*' * (len(tavily_key) - 4) + tavily_key[-4:]}")
    else:
        print("⚠️  TAVILY_API_KEY: Not set (optional)")
    
    weather_key = os.getenv('OPENWEATHER_API_KEY')
    if weather_key:
        print(f"✅ OPENWEATHER_API_KEY: {'*' * (len(weather_key) - 4) + weather_key[-4:]}")
    else:
        print("⚠️  OPENWEATHER_API_KEY: Not set (optional)")
    
    print()
    
    # Test agent import
    print("📦 Testing agent import...")
    try:
        from agent import TaskPlanningAgent, create_plan
        print("✅ Agent imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected import error: {e}")
        return False
    
    # Test agent initialization
    print("\n🔧 Testing agent initialization...")
    try:
        agent = TaskPlanningAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test plan generation
    print("\n🎯 Testing plan generation...")
    test_goal = "Learn Python programming and build a web application"
    print(f"Goal: {test_goal}")
    
    try:
        plan_data = agent.generate_plan(test_goal)
        print("✅ Plan generated successfully!")
        print(f"Plan keys: {list(plan_data.keys())}")
        
        if 'goal' in plan_data:
            print(f"Generated goal: {plan_data['goal']}")
        
        if 'daily_breakdown' in plan_data:
            print(f"Daily breakdown days: {len(plan_data['daily_breakdown'])}")
            for i, day in enumerate(plan_data['daily_breakdown'][:3]):  # Show first 3 days
                print(f"  Day {i+1}: {day.get('focus', 'No focus')}")
        
        if 'enrichment' in plan_data:
            enrichment = plan_data['enrichment']
            print(f"Enrichment status: {enrichment.get('note', 'No note')}")
        
    except Exception as e:
        print(f"❌ Plan generation failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    
    # Test plan formatting
    print("\n📝 Testing plan formatting...")
    try:
        formatted_plan = agent.format_plan_output(plan_data)
        print("✅ Plan formatted successfully!")
        print(f"Formatted plan length: {len(formatted_plan)} characters")
        print("Formatted plan preview:")
        print("-" * 40)
        print(formatted_plan[:500] + "..." if len(formatted_plan) > 500 else formatted_plan)
        print("-" * 40)
    except Exception as e:
        print(f"❌ Plan formatting failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    
    # Test convenience function
    print("\n🚀 Testing convenience function...")
    try:
        result = create_plan(test_goal, save_to_db=False)
        print("✅ Convenience function worked!")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)} characters")
    except Exception as e:
        print(f"❌ Convenience function failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    
    print("\n✅ All direct tests passed!")
    return True

def main():
    """Main test function."""
    success = test_agent_direct()
    
    if success:
        print("\n🎉 Agent is working correctly!")
        print("If the FastAPI server still shows 'Error: undefined', the issue is likely:")
        print("1. Server not running")
        print("2. CORS issues")
        print("3. Frontend JavaScript errors")
        print("4. Network connectivity issues")
    else:
        print("\n❌ Agent has issues that need to be fixed first")
        print("Fix the agent issues before testing the FastAPI server")

if __name__ == "__main__":
    main()
