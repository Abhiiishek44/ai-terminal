# AI Terminal Backend

Production-ready scalable AI Terminal backend using **FastAPI** and **Google Gemini AI**. Converts natural language commands into executable terminal commands with intelligent classification and security validation.

## 🚀 Features

- **Natural Language Processing**: Convert plain English to terminal commands
  - "install fastapi" → `pip install fastapi`
  - "create react app" → `npx create-react-app my-app`
  - "list all python files" → `ls -la *.py`

- **Command Classification**: Automatic intent detection
  - `install_package`: Package installation commands
  - `setup_project`: Project initialization
  - `run_script`: Script execution
  - `system_operation`: File/directory operations
  - `fix_error`: Error resolution suggestions

- **Security First**: Dangerous command blocking
  - Blocks `rm -rf /`, `:(){ :|:& };:`, system directory modifications
  - Safety level classification (safe, caution, danger, blocked)

- **Clean Architecture**: Service-based design with dependency injection
- **Async Support**: Full async/await implementation
- **Comprehensive Logging**: Request tracking and error monitoring

## 📋 Prerequisites

- Python 3.8+
- Google Gemini API Key (free from [Google AI Studio](https://makersuite.google.com/app/apikey))

## 🛠️ Installation

### 1. Clone and Navigate
```bash
cd "Ai Terminal/backend"
```

### 2. Install Dependencies
```bash
pip install -r ../requirements.txt
```

### 3. Configure Environment
Create/edit `.env` file in the root directory:
```bash
GEMINI_API_KEY=your_actual_api_key_here
APP_NAME=AI Terminal Backend
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

**Get your Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy and paste into `.env` file

### 4. Run the Server
```bash
# From the backend directory
python app.py

# Or using uvicorn directly
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Root**: http://localhost:8000/

## 🔌 API Endpoints

### POST /terminal/run
Generate terminal command from natural language

**Request:**
```json
{
  "command": "install fastapi",
  "context": {
    "os": "linux",
    "shell": "bash"
  }
}
```

**Response:**
```json
{
  "command": "pip install fastapi",
  "explanation": "Installs FastAPI package using pip",
  "intent": "install_package",
  "safety_level": "safe",
  "warning": null,
  "alternative_commands": ["pip3 install fastapi", "python -m pip install fastapi"]
}
```

### POST /terminal/fix
Suggest fixes for command errors

**Request:**
```json
{
  "failed_command": "pip install fastapi",
  "error_message": "command not found: pip",
  "context": {
    "os": "linux"
  }
}
```

**Response:**
```json
{
  "command": "python -m pip install fastapi",
  "explanation": "Use Python module execution when pip command is not in PATH",
  "intent": "fix_error",
  "safety_level": "safe"
}
```

### GET /terminal/health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "ai_service": "operational",
  "gemini_model": "gemini-2.0-flash-exp"
}
```

## 🏗️ Project Structure

```
backend/
├── app.py                          # FastAPI application entry point
├── core/
│   ├── __init__.py
│   └── config.py                   # Pydantic settings configuration
├── models/
│   ├── __init__.py
│   └── request_models.py           # Pydantic request/response models
├── services/
│   ├── __init__.py
│   ├── ai_service.py               # Gemini AI integration
│   ├── command_service.py          # Business logic orchestration
│   └── executor_service.py         # Command execution (optional)
├── routers/
│   ├── __init__.py
│   └── terminal_router.py          # API endpoints
└── utils/
    ├── __init__.py
    └── response_formatter.py       # Response formatting utilities
```

## 🧪 Testing

### Using curl
```bash
# Generate command
curl -X POST "http://localhost:8000/terminal/run" \
  -H "Content-Type: application/json" \
  -d '{"command": "install fastapi", "context": {"os": "linux"}}'

# Fix error
curl -X POST "http://localhost:8000/terminal/fix" \
  -H "Content-Type: application/json" \
  -d '{"failed_command": "npm install", "error_message": "command not found"}'

# Health check
curl "http://localhost:8000/terminal/health"
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/terminal/run",
    json={
        "command": "create a new react app called my-app",
        "context": {"os": "linux", "shell": "bash"}
    }
)
print(response.json())
```

## 🔒 Security Features

- **Dangerous Command Detection**: Blocks destructive operations
- **Pattern Matching**: Regex-based validation for system safety
- **Safety Classification**: 4-level system (safe/caution/danger/blocked)
- **Dry-run Mode**: Test commands without execution (ExecutorService)

## 🚧 Example Use Cases

1. **Package Installation**
   - Input: "install flask"
   - Output: `pip install flask`

2. **Project Setup**
   - Input: "create a new vue project"
   - Output: `npm create vue@latest`

3. **File Operations**
   - Input: "find all jpg images"
   - Output: `find . -name "*.jpg"`

4. **Error Fixing**
   - Input: Failed command + error message
   - Output: Corrected command with explanation

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | - | **Required** Google Gemini API key |
| `APP_NAME` | AI Terminal Backend | Application name |
| `DEBUG` | false | Debug mode |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `GEMINI_MODEL` | gemini-2.0-flash-exp | Gemini model version |
| `GEMINI_TEMPERATURE` | 0.3 | AI response randomness (0-1) |
| `MAX_REQUESTS_PER_MINUTE` | 30 | Rate limiting |


## 📄 License

MIT License - Free to use and modify

## 🆘 Troubleshooting

### "Invalid API Key" Error
- Verify `.env` file has correct `GEMINI_API_KEY`
- Check key is active at [Google AI Studio](https://makersuite.google.com/app/apikey)

### "Module not found" Error
- Ensure requirements installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

### Server Won't Start
- Check port 8000 is available: `lsof -i :8000`
- Try different port: `PORT=8001 python app.py`

## 📧 Support

For issues or questions, check:
- API Documentation: http://localhost:8000/docs
- Logs: Check console output for detailed error messages
