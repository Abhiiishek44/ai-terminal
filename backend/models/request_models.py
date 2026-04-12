# models/request_models.py

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum


class CommandIntent(str, Enum):
    """Command intent classification"""
    INSTALL_PACKAGE = "install_package"
    SETUP_PROJECT = "setup_project"
    RUN_COMMAND = "run_command"
    FIX_ERROR = "fix_error"
    GIT_OPERATION = "git_operation"
    DOCKER_OPERATION = "docker_operation"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"
    UNKNOWN = "unknown"


class SafetyLevel(str, Enum):
    """Command safety classification"""
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"
    BLOCKED = "blocked"


class TerminalRequest(BaseModel):
    """Request model for terminal command generation"""
    input: str = Field(..., description="Natural language command input", min_length=1, max_length=500)
    execute: bool = Field(default=False, description="Whether to execute the command")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    
    @validator('input')
    def validate_input(cls, v):
        """Validate input is not empty or just whitespace"""
        if not v or not v.strip():
            raise ValueError("Input cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "input": "install fastapi",
                "execute": False,
                "context": {"working_dir": "/home/user/project"}
            }
        }


class TerminalResponse(BaseModel):
    """Response model for terminal command"""
    intent: CommandIntent = Field(..., description="Classified command intent")
    command: str = Field(..., description="Generated terminal command")
    explanation: str = Field(..., description="Human-readable explanation")
    technology: Optional[str] = Field(None, description="Detected technology stack")
    safety: SafetyLevel = Field(..., description="Safety classification")
    warnings: list[str] = Field(default_factory=list, description="Safety warnings")
    status: str = Field(default="success", description="Operation status")
    execution_result: Optional[Dict[str, Any]] = Field(None, description="Execution result if executed")
    new_cwd: Optional[str] = Field(None, description="Updated current working directory")
    plan: Optional[list[Dict[str, Any]]] = Field(None, description="Generated step-by-step execution plan")
    environment_validation: Optional[Dict[str, str]] = Field(None, description="Detected tool validation status")
    agent_state: Optional[Dict[str, Any]] = Field(None, description="Session state snapshot")
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent": "install_package",
                "command": "pip install fastapi",
                "explanation": "Install FastAPI Python web framework",
                "technology": "python",
                "safety": "safe",
                "warnings": [],
                "status": "success"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error information")
    status: str = Field(default="error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid API key",
                "details": "Gemini API key is not configured",
                "status": "error"
            }
        }
