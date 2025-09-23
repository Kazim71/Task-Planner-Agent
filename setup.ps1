# setup.ps1 - Set environment variables for Task Planner Agent

$env:GEMINI_API_KEY = "<your-gemini-api-key>"
$env:TAVILY_API_KEY = "<your-tavily-api-key>"
$env:OPENWEATHER_API_KEY = "<your-openweather-api-key>"

Write-Host "Environment variables set for this session."
