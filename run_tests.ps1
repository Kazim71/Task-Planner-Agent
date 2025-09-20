# Task Planner Agent Test Script
Write-Host "Starting Task Planner Agent Tests..." -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Testing Agent Directly (without server)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
python test_agent_direct.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Testing FastAPI Server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Make sure the server is running first!" -ForegroundColor Red
Write-Host "Start it with: python main.py" -ForegroundColor Red
Write-Host ""
Read-Host "Press Enter to continue with API tests"

python test_api.py

Write-Host ""
Write-Host "Tests completed!" -ForegroundColor Green
Read-Host "Press Enter to exit"
