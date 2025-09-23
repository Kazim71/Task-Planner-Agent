# Task Planner Agent 🚀

**A smart, AI-powered agent that creates detailed, actionable plans for any goal, from learning a new skill to planning a vacation.**

---

[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Deployment](https://img.shields.io/badge/Deployed%20on-Railway-lightgrey.svg)](https://railway.app/)

**Live Demo:** A live demo can be provided upon request. *(Note: Public API keys have usage limits.)*

## Overview

This project is a full-stack web application built with Python and FastAPI that leverages the power of Google's Gemini AI to function as an intelligent task planner. Users can input a high-level goal, and the agent will use a sophisticated "two-pass" system to generate a structured, day-by-day plan.

The agent is designed to be versatile, capable of creating everything from technical learning roadmaps to detailed travel itineraries. It intelligently decides when to use external tools like web search (Tavily) and weather forecasting (OpenWeatherMap) to enrich its plans with real-time, relevant data.

## Key Features

* **Intelligent AI Agent:** Uses a "two-pass" thinking process to first select the right tools and then generate an informed plan.
* **Dynamic AI Personas:** The agent's instructions (system prompt) can be easily modified to make it an expert in any domain (e.g., a travel agent, a fitness coach, a career advisor).
* **Tool Integration:** Seamlessly integrates with external APIs for web search and weather to create fact-based, relevant plans.
Tool Integration:

🌐 Tavily Web Search

🌦️ OpenWeatherMap

* **Full-Stack Application:** Built with a robust FastAPI backend and a clean, responsive HTML/JavaScript frontend.
* **Database Persistence:** Saves all generated plans to a database (SQLite locally, PostgreSQL in production) for later viewing.
* **CI/CD Pipeline:** Deployed on Railway with a continuous deployment pipeline triggered by pushes to the main GitHub branch.

---
📝 Examples in Action
Example 1: Learning Roadmap

Goal: “Make a Roadmap to Learn Data Science in 6 months”

<details> <summary>Generated Plan</summary>

<details>
<summary>Click to see the Generated Plan</summary>

{
  "goal": "Make a Roadmap to Learn Data Science in 6 months",
  "overview": "A comprehensive 6-month roadmap progressing from fundamentals to advanced projects.",
  "estimated_duration": "6 months",
  "daily_breakdown": [
    {
      "day": 1,
      "focus": "Month 1: Python & Math",
      "tasks": [
        {
          "task": "Complete a Python fundamentals course",
          "estimated_time": "3 weeks",
          "priority": "high"
        },
        {
          "task": "Review Linear Algebra and Statistics basics",
          "estimated_time": "1 week",
          "priority": "high"
        }
      ]
    },
    {
      "day": 61,
      "focus": "Month 3: Machine Learning",
      "tasks": [
        {
          "task": "Learn supervised vs unsupervised learning with Scikit-learn",
          "estimated_time": "4 weeks",
          "priority": "high"
        }
      ]
    }
  ],
  "success_metrics": [
    "2 end-to-end projects",
    "Portfolio site with projects",
    "Core ML understanding"
  ],
  "potential_challenges": [
    "Finding good datasets",
    "Motivation dips",
    "Overwhelming scope"
  ]
}
</details>


Example 2: Travel Itinerary

Goal: “Plan a 4-day photography trip to London next week”

<details> <summary>Generated Plan</summary>

{
  "goal": "Plan a 4-day photography trip to London",
  "overview": "Photography-focused itinerary covering landmarks, hidden gems, and street life.",
  "estimated_duration": "4 days",
  "daily_breakdown": [
    {
      "day": 1,
      "focus": "Iconic Landmarks",
      "tasks": [
        {
          "task": "Shoot St. Paul’s Cathedral from Millennium Bridge",
          "estimated_time": "3 hours",
          "priority": "high"
        }
      ]
    }
  ],
  "success_metrics": [
    "20 portfolio-quality images",
    "5 iconic landmarks"
  ],
  "potential_challenges": [
    "London weather",
    "Tourist crowds"
  ]
}
</details>

🏗 Architecture
Code snippet

flowchart TD
    subgraph "User's Browser"
        A[Frontend - index.html]
    end

    subgraph "Railway.app Cloud Platform"
        B[FastAPI Backend - main.py]
        C[Database - PostgreSQL/SQLite]
    end
    
    subgraph "AI & Tools"
        D[AI Agent - agent.py]
        E[Google Gemini API]
        F[External Tools - tools.py]
        G[Tavily Web Search API]
        H[OpenWeatherMap API]
    end

    A --> B
    B --> D
    B --> C
    D --> E
    D --> F
    F --> G
    F --> H
    D --> B
    B --> A


⚙️ Tech Stack

Backend: Python, FastAPI, Uvicorn, Gunicorn

AI: Google Gemini

Database: SQLAlchemy ORM, SQLite (local), PostgreSQL (prod)

Frontend: HTML, CSS, Vanilla JavaScript

Deployment: Railway (auto-deploy from GitHub)

External APIs: Tavily (search), OpenWeatherMap (weather)

🔧 Local Setup
Prerequisites: Python 3.10+, Git

# 1. Clone
git clone https://github.com/YourUsername/Task-Planner-Agent.git
cd Task-Planner-Agent

# 2. Create & activate virtual env
python -m venv venv
source venv/bin/activate   # macOS/Linux
.\venv\Scripts\Activate.ps1 # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Environment variables (.env)
GEMINI_API_KEY="your_key"
TAVILY_API_KEY="your_key"
OPENWEATHER_API_KEY="your_key"

# 5. Run locally
uvicorn main:app --reload

Runs at: http://localhost:8000

🤖 AI Usage Disclosure

This project was developed with help from GitHub Copilot and other AI tools for:
Initial scaffolding & boilerplate
API integrations (Gemini, Tavily, Weather)
Error handling templates
Documentation drafts
All code was reviewed, tested, and customized for project needs.