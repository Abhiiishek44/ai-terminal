# services/command_service.py

import logging
import re
import shlex
from typing import Dict, Optional
from models.request_models import CommandIntent, SafetyLevel
from core.config import get_settings
from services.ai_service import AIService
from services.executor_service import ExecutorService
from services.dependency_detector import DependencyDetector
from services.planner_service import PlannerService
from services.state_service import StateService
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
        settings = get_settings()
        self.ai_service = ai_service
        self.detector = DependencyDetector()
        self.planner = PlannerService(self.detector)
        self.state = StateService(base_directory=settings.execution_base_dir)
        self.executor = ExecutorService(dry_run=False, base_directory=settings.execution_base_dir)
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
            context = context or {}
            session_id = context.get("session_id", "default")
            requested_cwd = context.get("cwd")
            session = self.state.get_or_create_session(session_id=session_id, cwd=requested_cwd)
            normalized_input = self._normalize_shell_command(user_input)

            # Central dangerous-command check helper using ExecutorService patterns
            def _blocked_response_for(command: str):
                return {
                    "intent": CommandIntent.RUN_COMMAND,
                    "command": command,
                    "explanation": "Command blocked by safety policy",
                    "technology": "shell",
                    "safety": SafetyLevel.DANGER,
                    "warnings": ["Command blocked by safety policy"],
                    "status": "blocked",
                    "execution_result": {
                        "success": False,
                        "executed": False,
                        "command": command,
                        "stdout": "",
                        "stderr": "Command blocked by safety policy",
                        "exit_code": 126,
                        "new_cwd": session.cwd,
                    },
                    "new_cwd": session.cwd,
                    "plan": [],
                    "environment_validation": {},
                    "agent_state": self.state.get_state_snapshot(session_id),
                }


            if self._is_smalltalk(normalized_input):
                return {
                    "intent": CommandIntent.RUN_COMMAND,
                    "command": "echo 'Hello! I am ready. Try commands like ls, pwd, cd .., or install pandas'",
                    "explanation": "Handled greeting directly without AI request",
                    "technology": "system",
                    "safety": SafetyLevel.SAFE,
                    "warnings": [],
                    "status": "success",
                    "execution_result": {
                        "success": True,
                        "executed": True,
                        "command": normalized_input,
                        "stdout": "Hello! I am ready. Try commands like ls, pwd, cd .., or install pandas",
                        "stderr": "",
                        "exit_code": 0,
                        "new_cwd": session.cwd,
                    },
                    "new_cwd": session.cwd,
                    "plan": [
                        {
                            "id": 1,
                            "kind": "action",
                            "command": normalized_input,
                            "description": "Small-talk fast-path response",
                            "requires": [],
                        }
                    ],
                    "environment_validation": {},
                    "agent_state": self.state.get_state_snapshot(session_id),
                }

            if self._is_direct_shell_command(normalized_input):
                # Pre-check dangerous patterns before executing
                if self.executor._is_dangerous(normalized_input):
                    return _blocked_response_for(normalized_input)

                direct_execution = self.executor.execute(command=normalized_input, cwd=session.cwd)
                new_cwd = direct_execution.get("new_cwd", session.cwd)
                self.state.update_cwd(session_id, new_cwd)
                return {
                    "intent": CommandIntent.RUN_COMMAND,
                    "command": normalized_input,
                    "explanation": "Executed shell command directly without AI planning",
                    "technology": "shell",
                    "safety": SafetyLevel.SAFE if direct_execution.get("success") else SafetyLevel.CAUTION,
                    "warnings": [],
                    "status": "blocked" if direct_execution.get("error") == "blocked" else ("success" if direct_execution.get("success") else "error"),
                    "execution_result": direct_execution,
                    "new_cwd": new_cwd,
                    "plan": [
                        {
                            "id": 1,
                            "kind": "action",
                            "command": normalized_input,
                            "description": "Direct shell command execution",
                            "requires": [],
                        }
                    ],
                    "environment_validation": {},
                    "agent_state": self.state.get_state_snapshot(session_id),
                }

            if self._is_python_env_pandas_request(normalized_input):
                folder_name = self._extract_folder_name_for_setup(normalized_input)
                plan_payload = [
                    {
                        "id": 1,
                        "kind": "precheck",
                        "command": "which python3 || python3 --version",
                        "description": "Check Python3 availability",
                        "requires": ["python3"],
                    },
                    {
                        "id": 2,
                        "kind": "filesystem",
                        "command": f"mkdir -p {folder_name}",
                        "description": f"Create folder '{folder_name}'",
                        "requires": [],
                    },
                    {
                        "id": 3,
                        "kind": "navigation",
                        "command": f"cd {folder_name}",
                        "description": f"Enter folder '{folder_name}'",
                        "requires": [],
                    },
                    {
                        "id": 4,
                        "kind": "setup",
                        "command": "python3 -m venv .venv",
                        "description": "Create Python virtual environment",
                        "requires": ["python3"],
                    },
                    {
                        "id": 5,
                        "kind": "install",
                        "command": "python -m pip install pandas",
                        "description": "Install pandas using virtual environment interpreter",
                        "requires": ["python3", "pip"],
                    },
                ]

                # Pre-check plan steps for dangerous commands
                for step in plan_payload:
                    if self.executor._is_dangerous(step.get("command", "")):
                        return _blocked_response_for(step.get("command", ""))

                execution_result = self.executor.execute_plan(plan_payload, cwd=session.cwd)
                new_cwd = execution_result.get("new_cwd", session.cwd)
                self.state.update_cwd(session_id, new_cwd)

                return {
                    "intent": CommandIntent.SETUP_PROJECT,
                    "command": "python -m pip install pandas",
                    "explanation": "Created folder, created virtual environment, and installed pandas using the venv Python interpreter",
                    "technology": "python",
                    "safety": SafetyLevel.SAFE,
                    "warnings": [],
                    "status": "success" if execution_result.get("success") else "error",
                    "execution_result": execution_result,
                    "new_cwd": new_cwd,
                    "plan": plan_payload,
                    "environment_validation": {
                        "python3": "available",
                        "pip": "checked",
                    },
                    "agent_state": self.state.get_state_snapshot(session_id),
                }

            # Generate command using AI
            import os
            has_venv = os.path.exists(os.path.join(session.cwd, ".venv"))
            ai_context = {**context, "cwd": session.cwd, "has_venv": has_venv}
            result = await self.ai_service.generate_command(normalized_input, ai_context)
            print(f"AI generated result: {result}")
            
            # Apply business rules
            result = self._apply_business_rules(result)

            ai_command = result.get("command", "")

            # If AI returned a command, pre-check it for dangerous patterns before building a plan
            if ai_command and self.executor._is_dangerous(ai_command):
                return _blocked_response_for(ai_command)

            # Build execution plan and validate deps in advance
            plan_steps = self.planner.build_plan(user_input=normalized_input, ai_command=result.get("command", ""))
            plan_payload = [
                {
                    "id": step.id,
                    "kind": step.kind,
                    "command": step.command,
                    "description": step.description,
                    "requires": step.requires,
                }
                for step in plan_steps
            ]

            # Pre-check generated plan steps for dangerous commands
            for step in plan_payload:
                if self.executor._is_dangerous(step.get("command", "")):
                    return _blocked_response_for(step.get("command", ""))

            execution_result = self.executor.execute_plan(plan_payload, cwd=session.cwd)
            result["execution_result"] = execution_result
            result["plan"] = plan_payload

            # Update session cwd and tool availability cache
            new_cwd = execution_result.get("new_cwd", session.cwd)
            self.state.update_cwd(session_id, new_cwd)

            detected = self.detector.detect(f"{normalized_input} {result.get('command', '')}")
            env_status = {}
            for dep in sorted(detected.dependencies):
                status = "available" if any(
                    r.get("step_kind") == "precheck" and dep in r.get("command", "") and r.get("success")
                    for r in execution_result.get("results", [])
                ) else "unknown"
                self.state.mark_tool(session_id, dep, status=status)
                env_status[dep] = status

            result["new_cwd"] = new_cwd
            result["agent_state"] = self.state.get_state_snapshot(session_id)
            result["environment_validation"] = env_status
            
            if execution_result.get("error") == "blocked":
                result["status"] = "blocked"
                result["safety"] = SafetyLevel.DANGER
                result.setdefault("warnings", []).append("Command blocked by safety policy")
            else:
                result["status"] = "success" if execution_result.get("success") else "error"
            logger.info(f"Processed command successfully: {normalized_input}")
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

    def _is_direct_shell_command(self, user_input: str) -> bool:
        """Detect if user input is already a shell command and should bypass LLM."""
        if not user_input or not user_input.strip():
            return False

        shell_starters = {
            "ls", "pwd", "cd", "mkdir", "touch", "cat", "echo", "cp", "mv", "rm",
            "find", "grep", "head", "tail", "which", "whoami", "python", "pip", "npm",
            "node", "git", "docker", "docker-compose", "pnpm", "yarn", "chmod", "chown",
            "sed", "awk", "curl", "wget", "ps", "top", "kill", "make",
        }

        try:
            command_word = shlex.split(user_input)[0].lower()
        except Exception:
            command_word = user_input.split()[0].lower() if user_input.split() else ""

        natural_language_hints = ("please", "can you", "how to", "setup", "create a", "install ")
        lowered = user_input.lower().strip()
        if any(hint in lowered for hint in natural_language_hints):
            return False

        return command_word in shell_starters

    def _normalize_shell_command(self, user_input: str) -> str:
        normalized = (user_input or "").strip()
        if normalized == "cd..":
            return "cd .."
        if normalized.lower().startswith("cd.."):
            return normalized.replace("cd..", "cd ..", 1)
        return normalized

    def _is_smalltalk(self, user_input: str) -> bool:
        if not user_input:
            return False
        lowered = user_input.strip().lower()
        return lowered in {
            "hello",
            "hi",
            "hey",
            "hello ai",
            "hi ai",
            "hey ai",
        }

    def _is_python_env_pandas_request(self, user_input: str) -> bool:
        lowered = (user_input or "").lower()
        return (
            "pandas" in lowered
            and ("env" in lowered or "environment" in lowered or "venv" in lowered)
            and ("folder" in lowered or "directory" in lowered or "project" in lowered)
        )

    def _extract_folder_name_for_setup(self, user_input: str) -> str:
        lowered = user_input.lower()
        patterns = [
            r"(?:folder|directory|project)\s+(?:named|called)?\s*([a-zA-Z0-9._-]+)",
            r"create\s+([a-zA-Z0-9._-]+)\s+(?:folder|directory|project)",
        ]

        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                name = match.group(1).strip(" .,")
                if name:
                    return name

        return "new-project"
    
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
