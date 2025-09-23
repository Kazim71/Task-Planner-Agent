Task Planner Agent 🚀

AI-powered agent that transforms high-level goals into structured, actionable plans — from learning a skill to planning a trip.






Live Demo: Task Planner Agent on Railway
 (API usage limits apply)

📌 Overview

This is a full-stack web application built with Python + FastAPI, powered by Google Gemini AI.
The agent takes a natural language goal, breaks it into steps, enriches with real-time web search (Tavily) and weather forecasts (OpenWeatherMap), then outputs a structured daily plan. Plans are stored in a database for later access.

Designed for flexibility: it can generate learning roadmaps, travel itineraries, fitness routines, or any structured plan you throw at it.

✨ Key Features

Two-pass planning: picks tools first, then composes the plan.

Dynamic personas: act as travel agent, study coach, project manager, etc.

External integrations:

🌐 Tavily Web Search

🌦️ OpenWeatherMap

Persistence: SQLite for dev, PostgreSQL in production.

Simple Web UI: input new goals, view plan, browse history.

Continuous deployment: auto-deploys to Railway on push.

📝 Examples
Example 1: Data Science Roadmap

Goal: “Make a Roadmap to Learn Data Science in 6 months”

<details> <summary>Generated Plan (JSON excerpt)</summary>
{
  "goal": "Make a Roadmap to Learn Data Science in 6 months",
  "overview": "6-month roadmap covering Python, math, ML, SQL, projects, and portfolio.",
  "success_metrics": [
    "Two end-to-end projects",
    "Portfolio website",
    "Core ML understanding"
  ],
  "potential_challenges": [
    "Overwhelming field",
    "Finding datasets",
    "Maintaining motivation"
  ]
}

</details>
Example 2: London Photography Trip

Goal: “Plan a 4-day photography trip to London next week”

<details> <summary>Generated Plan (JSON excerpt)</summary>
{
  "goal": "Plan a 4-day photography trip to London",
  "overview": "A photography-focused itinerary covering landmarks, hidden gems, and street life.",
  "success_metrics": [
    "20 portfolio-quality images",
    "5 iconic landmarks",
    "Smooth navigation"
  ],
  "potential_challenges": [
    "Unpredictable weather",
    "Tourist crowds",
    "Underground travel"
  ]
}

</details>
🏗 Architecture
flowchart TD
    User([Browser])
    UI[Frontend - index.html]
    API[FastAPI Backend]
    DB[(Database: SQLite/Postgres)]
    Agent[Task Planner Agent]
    Gemini[Google Gemini AI]
    Tavily[Tavily Search API]
    Weather[OpenWeatherMap API]

    User --> UI --> API
    API --> Agent
    Agent --> Gemini
    Agent --> Tavily
    Agent --> Weather
    Agent --> DB
    DB --> API --> UI --> User

⚙️ Tech Stack

Backend: FastAPI, Uvicorn, Gunicorn

AI: Google Gemini

Database: SQLAlchemy ORM, SQLite (dev), PostgreSQL (prod)

Frontend: HTML, CSS, vanilla JavaScript

Deployment: Railway (CI/CD via GitHub)

External APIs: Tavily (search), OpenWeatherMap (weather)

🔧 Local Setup

Prerequisites: Python 3.10+, Git

# Clone repo
git clone https://github.com/YourUsername/Task-Planner-Agent.git
cd Task-Planner-Agent

# Create venv
python -m venv venv
source venv/bin/activate   # macOS/Linux
.\venv\Scripts\Activate.ps1 # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env
echo GEMINI_API_KEY="your-key" >> .env
echo TAVILY_API_KEY="your-key" >> .env
echo OPENWEATHER_API_KEY="your-key" >> .env

# Run locally
uvicorn main:app --reload


App runs at: http://localhost:8000

🤖 AI Usage Disclosure

This project was developed with assistance from GitHub Copilot and other AI coding tools for:

Boilerplate generation

API integration (Gemini, Tavily, Weather)

Error handling templates

Documentation drafts

All generated code was reviewed, tested, and customized to meet project requirements.