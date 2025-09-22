

# Task Planner Agent

[![Production Status](https://img.shields.io/badge/Live%20Demo-Railway-green?logo=railway&style=flat-square)](https://task-planner-agent-production.up.railway.app/)

**Live Demo:** [https://task-planner-agent-production.up.railway.app/](https://task-planner-agent-production.up.railway.app/)

---

**Current Status:** ✅ Production deployed on Railway (asia-southeast1)

---

## Technology Stack

- **Backend:** Python 3.12.10
- **Framework:** Flask (API compatible with FastAPI)
- **AI:** Google Gemini AI API
- **Deployment:** Railway (asia-southeast1 region)
- **WSGI Server:** Gunicorn with Uvicorn workers
- **Process Management:** Procfile

---

## Key Features

- AI-generated vacation and task plans
- Date-based planning and scheduling
- Persistent database storage of plans
- REST API interface for programmatic access

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd task-planner-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root with:

```env
GEMINI_API_KEY=your_gemini_api_key_here
# Optional for local DB:
DATABASE_URL=sqlite:///./task_planner.db
```

---

## Usage

### Local Development

```bash
python main.py
# or for hot reload (if using FastAPI):
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit [http://localhost:8000](http://localhost:8000) in your browser.

### Production (Railway)

Deployed and live at: [https://task-planner-agent-production.up.railway.app/](https://task-planner-agent-production.up.railway.app/)

---

## API Documentation

### Base URL

```
https://task-planner-agent-production.up.railway.app/
```

### Endpoints

#### 1. Web Interface
```
GET /
```
Returns the main web interface with goal input form.

#### 2. Create Plan
```
POST /plan
Content-Type: application/json

{
    "goal": "Plan a 2-week vacation to Goa",
    "start_date": "2025-09-22",
    "save_to_db": true
}
```
**Response:**
```json
{
    "success": true,
    "message": "Plan created successfully",
    "plan_id": 1,
    "plan_data": { ... },
    "formatted_plan": "PLAN: Plan a 2-week vacation to Goa\n..."
}
```

#### 3. Get All Plans
```
GET /plans?limit=10&search=vacation
```

#### 4. Get Specific Plan
```
GET /plans/{plan_id}
```

#### 5. Delete Plan
```
DELETE /plans/{plan_id}
```

#### 6. Health Check
```
GET /health
```

---

## Environment Variables

| Variable         | Description                        |
|------------------|------------------------------------|
| GEMINI_API_KEY   | Google Gemini API key (required)   |
| DATABASE_URL     | Database URL (optional, default SQLite) |

---

## Deployment Status

- **Production:** [https://task-planner-agent-production.up.railway.app/](https://task-planner-agent-production.up.railway.app/)
- **Region:** asia-southeast1 (Railway)
- **Process:** Gunicorn + Uvicorn workers, managed by Procfile

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Google Gemini for AI-powered plan generation
- Railway for cloud deployment
- Gunicorn & Uvicorn for production serving

---

## Support & Contributing

Open to issues and pull requests. Please open an issue for bugs or feature requests.

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- API keys for external services (see setup instructions)

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd task-planner-agent
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Optional Configuration
DATABASE_URL=sqlite:///./task_planner.db
HOST=0.0.0.0
PORT=8000
```

### 5. Get API Keys

#### Google Gemini API
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file

#### Tavily API (Web Search)
1. Visit [Tavily](https://tavily.com/)
2. Sign up for an account
3. Get your API key from the dashboard
4. Copy the key to your `.env` file

#### OpenWeatherMap API (Weather)
1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Generate an API key
4. Copy the key to your `.env` file

### 6. Run the Application

```bash
python main.py
```

The application will be available at `http://localhost:8000`

## 📖 Usage

### Web Interface

1. **Open the Application**: Navigate to `http://localhost:8000`
2. **Enter Your Goal**: Describe what you want to accomplish in natural language
3. **Set Start Date**: Optionally specify when to begin (defaults to today)
4. **Generate Plan**: Click "Generate Plan" to create your personalized plan
5. **View Results**: Review the generated plan with daily breakdowns
6. **Manage Plans**: Browse, search, and delete saved plans

### Example Goals

- "Learn Python programming and build a web application"
- "Plan a 2-week vacation to Japan"
- "Start a fitness routine and lose 20 pounds"
- "Learn machine learning and build a recommendation system"
- "Organize a wedding for 100 guests"
- "Prepare for a job interview at a tech company"

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Web Interface
```http
GET /
```
Returns the main web interface with goal input form.

#### 2. Create Plan
```http
POST /plan
Content-Type: application/json

{
    "goal": "Learn Python programming",
    "start_date": "2024-01-01",
    "save_to_db": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "Plan created successfully",
    "plan_id": 1,
    "plan_data": { ... },
    "formatted_plan": "PLAN: Learn Python programming\n..."
}
```

#### 3. Get All Plans
```http
GET /plans?limit=10&search=python
```

**Response:**
```json
{
    "success": true,
    "message": "Retrieved 5 plan(s)",
    "plans": [
        {
            "id": 1,
            "goal": "Learn Python programming",
            "steps": [...],
            "created_at": "2024-01-01T10:00:00"
        }
    ],
    "total_count": 5
}
```

#### 4. Get Specific Plan
```http
GET /plans/{plan_id}
```

**Response:**
```json
{
    "success": true,
    "message": "Plan 1 retrieved successfully",
    "plan_id": 1,
    "plan_data": { ... }
}
```

#### 5. Delete Plan
```http
DELETE /plans/{plan_id}
```

**Response:**
```json
{
    "success": true,
    "message": "Plan 1 deleted successfully",
    "plan_id": 1
}
```

#### 6. Health Check
```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T10:00:00",
    "database": "connected",
    "plans_count": 5
}
```

### Error Responses

All endpoints return consistent error responses:

```json
{
    "success": false,
    "error": "Error type",
    "message": "Detailed error message"
}
```

## 🏛️ Project Structure

```
task_planner_agent/
├── main.py                  # FastAPI server and API endpoints
├── agent.py                 # AI planning agent with Gemini integration
├── models.py                # Database models and ORM operations
├── tools.py                 # External API tools (web search, weather)
├── templates/
│   └── index.html          # Web frontend template
├── requirements.txt         # Python dependencies
├── README.md               # Project documentation
├── .env                    # Environment variables (create this)
└── task_planner.db         # SQLite database (created automatically)
```

## 🔧 Development

### Running in Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Management

The application automatically creates the database and tables on startup. To reset the database:

```bash
# Delete the database file
rm task_planner.db

# Restart the application
python main.py
```

### Adding New Features

1. **New API Endpoints**: Add routes in `main.py`
2. **Database Changes**: Modify models in `models.py`
3. **AI Enhancements**: Update agent logic in `agent.py`
4. **External APIs**: Add new tools in `tools.py`

## 🧪 Testing

### Manual Testing

1. **Web Interface**: Test goal input and plan generation
2. **API Endpoints**: Use the interactive docs at `/docs`
3. **Database**: Verify plan storage and retrieval
4. **External APIs**: Test with different goal types

### API Testing with curl

```bash
# Create a plan
curl -X POST "http://localhost:8000/plan" \
     -H "Content-Type: application/json" \
     -d '{"goal": "Learn Python programming", "save_to_db": true}'

# Get all plans
curl -X GET "http://localhost:8000/plans"

# Get specific plan
curl -X GET "http://localhost:8000/plans/1"
```

## 🚨 Error Handling

The application includes comprehensive error handling for:

- **API Key Validation**: Ensures all required API keys are present
- **Input Validation**: Validates goal input and date formats
- **Network Timeouts**: Handles external API failures gracefully
- **Database Errors**: Manages database connection and query failures
- **Rate Limiting**: Handles API rate limits from external services
- **JSON Parsing**: Robust parsing of AI-generated responses

## 🔒 Security Considerations

- **API Key Protection**: Store sensitive keys in environment variables
- **Input Sanitization**: All user inputs are validated and sanitized
- **SQL Injection Prevention**: Uses SQLAlchemy ORM for safe database queries
- **CORS Configuration**: Configure CORS for production deployment
- **Rate Limiting**: Implement rate limiting for production use



## 🚀 Production Deployment (Railway)

This project is deployed and live on Railway:

**🌐 [https://task-planner-agent-production.up.railway.app/](https://task-planner-agent-production.up.railway.app/)**

You can use this link in your portfolio, resume, or share with recruiters.

### Railway Deployment Steps (for future updates)

1. Push your changes to the `main` branch on GitHub.
2. Railway will auto-deploy, or you can trigger a manual deploy from the Railway dashboard.
3. The live app will be available at the above URL.

**Python version and dependencies are pinned for reliability.**



### Production Deployment

1. **Environment Setup** (Railway Variables):
    - `GEMINI_API_KEY`: Your Gemini API key
    - `DATABASE_URL`: (Optional, defaults to SQLite if not set)

2. **Install Production Dependencies**:
    ```bash
    pip install gunicorn
    ```

3. **Run with Gunicorn**:
    ```bash
    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
    ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```


## 🤖 AI Tool Usage Disclosure

This project was developed with the assistance of **Github Copilot Agent**, an AI-powered code generation tool. The following aspects of the project were created with AI assistance:

- **Code Structure**: Initial project architecture and file organization
- **API Integration**: Implementation of external API integrations (Gemini, Tavily, OpenWeatherMap)
- **Database Models**: SQLAlchemy model definitions and database operations
- **Error Handling**: Comprehensive error handling patterns and validation
- **Frontend Development**: HTML/CSS/JavaScript for the web interface
- **Documentation**: Initial documentation structure and content

**Human Contributions**:
- Project requirements and specifications
- Code review and refinement
- Testing and debugging
- Final documentation and deployment configuration

The AI assistance was used to accelerate development and provide boilerplate code, but all code has been reviewed, tested, and customized for this specific application.

## 📄 License

This project is open source and available under the MIT License. See the [LICENSE](LICENSE) file for details.

##  Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

##  Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-repo/issues) page
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

##  Acknowledgments

**Google Gemini** for AI-powered plan generation
**Tavily** for web search capabilities
**OpenWeatherMap** for weather data
**FastAPI** for the excellent web framework
**SQLAlchemy** for database operations
**Github Copilot** for development assistance
**Railway** for cloud deployment
