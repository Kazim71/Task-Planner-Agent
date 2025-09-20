@echo off
echo Starting Task Planner Agent Tests...
echo.

echo ========================================
echo Testing Agent Directly (without server)
echo ========================================
python test_agent_direct.py

echo.
echo ========================================
echo Testing FastAPI Server
echo ========================================
echo Make sure the server is running first!
echo Start it with: python main.py
echo.
pause

python test_api.py

echo.
echo Tests completed!
pause
