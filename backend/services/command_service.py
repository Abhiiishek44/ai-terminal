# services/command_service.py

import logging
from typing import Dict, Optional
from models.request_models import CommandIntent, SafetyLevel
from services.ai_service import AIService
from services.executor_service import ExecutorService
logger = logging.getLogger(__name__)


class CommandService:
    """
    Business logic layer for command processing
    Orchestrates AI service and applies business rules
    """
    
    def __init__(self, ai_service: AIService):
        """
        Initialize with AI service dependency
        
        Args:
            ai_service: Injected AI service instance
        """
        self.ai_service = ai_service
        logger.info("CommandService initialized")
    
    async def process_command(self, user_input: str, execute: bool = False, context: Optional[Dict] = None) -> Dict:
        """
        Process natural language input and generate terminal command
        
        Args:
            user_input: Natural language command
            execute: Whether to execute the command
            context: Optional context information (including cwd)
            
        Returns:
            Processed command result with new_cwd if directory changed
        """
        try:
            # Generate command using AI
            result = await self.ai_service.generate_command(user_input, context)
            print(f"AI generated result: {result}")
            
            # Apply business rules
            result = self._apply_business_rules(result)
            
            # Get current working directory from context
            current_cwd = context.get('cwd', '~') if context else '~'
            
            # Execute command to get real CWD changes
            executor = ExecutorService(dry_run=False)  # Enable actual execution
            execution_result = executor.execute(result["command"], cwd=current_cwd)
            result["execution_result"] = execution_result
            
            # Update new_cwd from execution result (handles cd commands)
            if execution_result.get("new_cwd"):
                result["new_cwd"] = execution_result["new_cwd"]
            elif not result.get("new_cwd"):
                result["new_cwd"] = current_cwd  # Keep current if no change
            
            result["status"] = "success"
            logger.info(f"Processed command successfully: {user_input}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            raise
    
    def _apply_business_rules(self, result: Dict) -> Dict:
        """Apply business rules and validations"""
        
        # Ensure command is not empty
        if not result.get("command") or result["command"] == "BLOCKED":
            result["safety"] = "danger"
            result.setdefault("warnings", []).append("Command blocked by safety filter")
        
        # Additional validation
        command = result.get("command", "")
        
        # Check command length
        if len(command) > 500:
            result["warnings"] = result.get("warnings", []) + ["Command is unusually long"]
        
        # Normalize intent
        intent_str = result.get("intent", "unknown")
        try:
            result["intent"] = CommandIntent(intent_str)
        except ValueError:
            result["intent"] = CommandIntent.UNKNOWN
        
        # Normalize safety
        safety_str = result.get("safety", "safe")
        try:
            result["safety"] = SafetyLevel(safety_str)
        except ValueError:
            result["safety"] = SafetyLevel.CAUTION
        
        return result
    
    async def _execute_command(self, command: str) -> Dict:
        """
        Execute command safely (placeholder for executor service)
        
        Args:
            command: Terminal command to execute
            
        Returns:
            Execution result
        """
        # This would call ExecutorService in production
        # For now, return dry-run result
        return {
            "executed": False,
            "mode": "dry_run",
            "command": command,
            "note": "Execution is disabled in current mode"
        }
    
    async def suggest_fix(self, error_message: str, failed_command: str) -> Dict:
        """
        Suggest fix for failed command
        
        Args:
            error_message: Error message from failed command
            failed_command: The command that failed
            
        Returns:
            Fix suggestion
        """
        try:
            result = await self.ai_service.suggest_fix(error_message, failed_command)
            result["status"] = "success"
            return result
        except Exception as e:
            logger.error(f"Error suggesting fix: {str(e)}")
            raise
