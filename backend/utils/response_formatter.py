# utils/response_formatter.py

from typing import Dict, Any
from models.request_models import TerminalResponse, ErrorResponse


class ResponseFormatter:
    """
    Clean response formatter for consistent API responses
    """
    
    @staticmethod
    def format_success(data: Dict[str, Any]) -> TerminalResponse:
        """
        Format successful terminal response
        
        Args:
            data: Response data dictionary
            
        Returns:
            Formatted TerminalResponse
        """
        return TerminalResponse(
            intent=data.get("intent", "unknown"),
            command=data.get("command", ""),
            explanation=data.get("explanation", ""),
            technology=data.get("technology"),
            safety=data.get("safety", "safe"),
            warnings=data.get("warnings", []),
            status=data.get("status", "success"),
            execution_result=data.get("execution_result"),
            new_cwd=data.get("new_cwd"),
            plan=data.get("plan"),
            environment_validation=data.get("environment_validation"),
            agent_state=data.get("agent_state")
        )
    
    @staticmethod
    def format_error(error: str, details: str = None) -> ErrorResponse:
        """
        Format error response
        
        Args:
            error: Error message
            details: Optional detailed error information
            
        Returns:
            Formatted ErrorResponse
        """
        return ErrorResponse(
            error=error,
            details=details,
            status="error"
        )
    
    @staticmethod
    def format_dict(response: Any) -> Dict[str, Any]:
        """
        Convert response to dictionary
        
        Args:
            response: Response object
            
        Returns:
            Dictionary representation
        """
        if hasattr(response, 'dict'):
            return response.dict()
        elif hasattr(response, 'model_dump'):
            return response.model_dump()
        return dict(response)
