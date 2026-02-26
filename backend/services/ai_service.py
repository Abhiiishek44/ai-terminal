# services/ai_service.py

from google.genai import Client
from google.genai.types import GenerateContentConfig
import json
import re
import logging
from typing import Dict, Optional
from core.config import get_settings
from models.request_models import CommandIntent, SafetyLevel

logger = logging.getLogger(__name__)


class AIService:
    """
    Production-grade AI Service using Gemini AI
    Handles all AI-related operations for terminal command generation
    """
    
    def __init__(self):
        """Initialize Gemini AI"""
        self.settings = get_settings()
        
        if not self.settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
           
        # Initialize client with API key
        self.client = Client(api_key=self.settings.gemini_api_key)
        
        logger.info(f"AIService initialized with model: {self.settings.gemini_model}")
    
    async def generate_command(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate terminal command from natural language input
        
        Args:
            user_input: Natural language command from user
            context: Optional context information
            
        Returns:
            Dictionary containing intent, command, explanation, etc.
        """
        try:
            # Build prompt
            prompt = self._build_command_prompt(user_input, context)
            
            # Generate response using new API
            response = self.client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            # Parse response
            result = self._parse_ai_response(response.text)
            
            # Validate and classify
            result = self._validate_and_classify(result, user_input)
            
            logger.info(f"Generated command for: '{user_input}' -> {result.get('command')}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating command: {str(e)}")
            raise
    
    def _build_command_prompt(self, user_input: str, context: Optional[Dict]) -> str:
        """Build optimized prompt for Gemini"""
        
        context_info = ""
        if context:
            cwd = context.get('cwd', '~')
            context_info = f"\n\nCONTEXT:\n- Current Working Directory: {cwd}\n- OS: {context.get('os', 'linux')}\n- Shell: {context.get('shell', 'bash')}"
        
        prompt = f"""You are an AI Developer Terminal Assistant that converts human instructions into executable terminal commands.

USER INPUT: "{user_input}"{context_info}

TASK: Analyze the input and generate the appropriate terminal command.

RESPONSE FORMAT (JSON):
{{
  "intent": "install_package|setup_project|run_command|fix_error|git_operation|docker_operation|file_operation|system_command",
  "command": "actual terminal command to execute",
  "explanation": "brief explanation of what the command does",
  "technology": "detected technology (python, node, docker, git, etc.)",
  "safety": "safe|caution|danger",
  "warnings": ["list of any safety warnings"],
  "new_cwd": "new working directory if command changes it (e.g., cd command), otherwise null"
}}

IMPORTANT FOR DIRECTORY CHANGES:
- If the command is "cd <directory>", set new_cwd to the target directory
- For relative paths (cd subfolder), append to current directory
- For absolute paths (cd /home/user), use the full path
- For "cd ..", go up one directory
- For "cd ~" or "cd", set to "~"

EXAMPLES:

Input: "install fastapi"
Output:
{{
  "intent": "install_package",
  "command": "pip install fastapi",
  "explanation": "Install FastAPI Python web framework using pip",
  "technology": "python",
  "safety": "safe",
  "warnings": [],
  "new_cwd": null
}}

Input: "go to home directory"
Output:
{{
  "intent": "file_operation",
  "command": "cd ~",
  "explanation": "Change to home directory",
  "technology": "system",
  "safety": "safe",
  "warnings": [],
  "new_cwd": "~"
}}

Input: "change to documents folder"
Output:
{{execute
  "intent": "file_operation",
  "command": "cd ~/Documents",
  "explanation": "Change to Documents directory",
  "technology": "system",
  "safety": "safe",
  "warnings": [],
  "new_cwd": "~/Documents"
}}

Input: "create react app called my-app"
Output:
{{
  "intent": "setup_project",
  "command": "npx create-react-app my-app",
  "explanation": "Create a new React application named 'my-app'",
  "technology": "react",
  "safety": "safe",
  "warnings": []
}}

Input: "initialize git repository"
Output:
{{
  "intent": "git_operation",
  "command": "git init",
  "explanation": "Initialize a new Git repository in current directory",
  "technology": "git",
  "safety": "safe",
  "warnings": []
}}

Input: "delete all files"
Output:
{{
  "intent": "file_operation",
  "command": "BLOCKED",
  "explanation": "This command is too dangerous and cannot be executed",
  "technology": "system",
  "safety": "danger",
  "warnings": ["This command would delete all files", "Command blocked for safety"]
}}

SAFETY RULES:
- BLOCK: rm -rf /, rm -rf /*, dd commands, fork bombs
- BLOCK: Modifications to /etc, /usr, /bin, /boot
- WARN: Any destructive operations (rm -rf, format, etc.)
- PREFER: Safe alternatives when possible

Generate the JSON response for the user input above. Return ONLY valid JSON, no additional text.
"""
        return prompt
    


    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response and extract JSON"""
        try:
            # Clean response
            text = response_text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```"):
                text = re.sub(r'```json\n?', '', text)
                text = re.sub(r'```\n?', '', text)
            
            # Find JSON object
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                text = json_match.group(0)
            
            # Parse JSON
            result = json.loads(text)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}\nResponse: {response_text}")
            # Return fallback response
            return {
                "intent": "unknown",
                "command": "BLOCKED",
                "explanation": "Failed to parse AI response",
                "technology": "unknown",
                "safety": "danger",
                "warnings": ["Could not parse AI response"],
                "new_cwd": None
            }
    
    def _validate_and_classify(self, result: Dict, user_input: str) -> Dict:
        """Validate and classify the generated command"""
        
        command = result.get("command", "")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'rm\s+-rf\s+/\*',
            r'dd\s+if=',
            r'mkfs',
            r'format',
            r':\(\)\{',  # Fork bomb
            r'>\s*/dev/sda',
            r'chmod\s+-R\s+777\s+/',
            r'chown\s+-R\s+root\s+/'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                result["command"] = "BLOCKED"
                result["safety"] = "danger"
                result["warnings"] = ["This command is blocked for security reasons", "Dangerous pattern detected"]
                logger.warning(f"Blocked dangerous command: {command}")
                break
        
        # Ensure all required fields exist
        result.setdefault("intent", "unknown")
        result.setdefault("explanation", "No explanation provided")
        result.setdefault("technology", "unknown")
        result.setdefault("safety", "safe")
        result.setdefault("warnings", [])
        
        return result
    
    async def suggest_fix(self, error_message: str, failed_command: str) -> Dict:
        """Suggest fix for failed command"""
        
        prompt = f"""You are an AI Developer Terminal Assistant helping to fix command errors.

FAILED COMMAND: {failed_command}

ERROR MESSAGE:
{error_message}

TASK: Analyze the error and suggest a corrected command.

RESPONSE FORMAT (JSON):
{{
  "error_type": "permission|not_found|syntax|network|configuration|other",
  "explanation": "why the command failed",
  "corrected_command": "fixed command",
  "additional_steps": ["step 1", "step 2"]
}}

Return ONLY valid JSON, no additional text.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_ai_response(response.text)
            logger.info(f"Generated fix for command: {failed_command}")
            return result
        except Exception as e:
            logger.error(f"Error generating fix: {str(e)}")
            return {
                "error_type": "other",
                "explanation": "Could not generate fix suggestion",
                "corrected_command": failed_command,
                "additional_steps": []
            }
