# routers/terminal_router.py

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict
import logging
from pydantic import BaseModel

from models.request_models import TerminalRequest, TerminalResponse, ErrorResponse
from services.ai_service import AIService
from services.command_service import CommandService
from services.executor_service import ExecutorService
from utils.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/terminal", tags=["Terminal"])


# Direct execution request model
class DirectExecuteRequest(BaseModel):
    command: str
    cwd: str = None


# Dependency injection
def get_ai_service() -> AIService:
    """Get AI service instance"""
    return AIService()


def get_command_service(ai_service: AIService = Depends(get_ai_service)) -> CommandService:
    """Get command service with AI service dependency"""
    return CommandService(ai_service)


def get_executor_service() -> ExecutorService:
    """Get executor service instance"""
    return ExecutorService()


@router.post(
    "/run",
    response_model=TerminalResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate and optionally execute terminal command",
    description="Convert natural language input to terminal command using AI"
)
async def run_command(
    request: TerminalRequest,
    command_service: CommandService = Depends(get_command_service)
) -> TerminalResponse:
    """
    Main endpoint for AI Terminal
    
    Args:
        request: Terminal request with natural language input
        command_service: Injected command service
        
    Returns:
        Terminal response with generated command
        
    Raises:
        HTTPException: If command generation fails
    """
    try:
        logger.info(f"Processing command: {request.input}")
        
        # Process command
        result = await command_service.process_command(
            user_input=request.input,
            execute=request.execute,
            context=request.context
        )
        
        # Format response
        response = ResponseFormatter.format_success(result)
        
        logger.info(f"Command processed successfully: {response.command}")
        return response
        
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process command: {str(e)}"
        )


@router.post(
    "/execute",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Execute command directly without AI processing",
    description="Execute ls, cd, pwd commands directly for instant response"
)
async def execute_direct(
    request: DirectExecuteRequest,
    executor_service: ExecutorService = Depends(get_executor_service)
) -> Dict:
    """
    Execute commands directly without AI processing
    
    Args:
        request: Direct execution request with command and cwd
        executor_service: Injected executor service
        
    Returns:
        Execution result with stdout, stderr, and new_cwd
        
    Raises:
        HTTPException: If command execution fails
    """
    try:
        logger.info(f"Executing direct command: {request.command} in {request.cwd}")
        
        # Execute command directly
        result = executor_service.execute(
            command=request.command,
            cwd=request.cwd
        )
        
        logger.info(f"Direct command executed successfully")
        
        return {
            "command": request.command,
            "execution_result": {
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "return_code": result.get("exit_code", 0)
            },
            "new_cwd": result.get("new_cwd", request.cwd),
            "is_safe": result.get("error") != "blocked",
            "requires_confirmation": result.get("error") == "blocked"
        }
        
    except Exception as e:
        logger.error(f"Error executing direct command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute command: {str(e)}"
        )


@router.post(
    "/fix",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Suggest fix for failed command",
    description="Get AI suggestions to fix a failed command"
)
async def suggest_fix(
    failed_command: str,
    error_message: str,
    command_service: CommandService = Depends(get_command_service)
) -> Dict:
    """
    Suggest fix for failed command
    
    Args:
        failed_command: The command that failed
        error_message: Error message from the failed command
        command_service: Injected command service
        
    Returns:
        Fix suggestion with corrected command
    """
    try:
        logger.info(f"Generating fix for command: {failed_command}")
        
        result = await command_service.suggest_fix(error_message, failed_command)
        
        logger.info("Fix suggestion generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error generating fix: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate fix: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the terminal service is running"
)
async def health_check() -> Dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Terminal",
        "version": "1.0.0"
    }
