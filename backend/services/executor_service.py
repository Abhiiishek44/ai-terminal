# services/executor_service.py

import os
import subprocess
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class ExecutorService:
    """
    Service for safe command execution with CWD tracking
    Handles actual terminal command execution with directory management
    """
    
    def __init__(self, dry_run: bool = False, base_directory: Optional[str] = None):
        """
        Initialize executor service
        
        Args:
            dry_run: If True, commands won't actually execute
        """
        self.dry_run = dry_run
        self.base_directory = os.path.abspath(base_directory or os.getcwd())
        self.dangerous_patterns = [
            r'(^|\s)(sudo\s+)?rm\s+-[a-zA-Z]*[rf][a-zA-Z]*\s+(/|\.|~|\$HOME|\$\{HOME\}|\*)',
            r'(^|\s)(sudo\s+)?rm\s+--no-preserve-root',
            r'dd\s+if=',
            r'mkfs',
            r'\bshutdown\b',
            r'\breboot\b',
            r'\bpoweroff\b',
            r'\bhalt\b',
            r'\binit\s+0\b',
            r':\(\)\{',
            r'\bchmod\s+-R\s+777\s+/',
            r'\bchown\s+-R\s+[^\s]+\s+/',
            r'>\s*/dev/sd[a-z][0-9]*',
            r'\bmkfs\.[a-z0-9]+\b',
            r':\(\)\{',
        ]
        logger.info(f"ExecutorService initialized (dry_run={dry_run})")

    def _normalize_cwd(self, cwd: Optional[str]) -> str:
        if not cwd or cwd == '~' or cwd == '':
            cwd = self.base_directory
        cwd = os.path.abspath(os.path.expanduser(cwd))
        if not os.path.exists(cwd):
            return self.base_directory
        return cwd

    def _is_dangerous(self, command: str) -> bool:
        import re
        return any(re.search(pattern, command, re.IGNORECASE) for pattern in self.dangerous_patterns)
    
    def execute(self, command: str, cwd: Optional[str] = None) -> Dict:
        """
        Execute terminal command with CWD tracking
        
        Args:
            command: Terminal command to execute
            cwd: Current working directory
            
        Returns:
            Execution result with stdout, stderr, exit code, and new_cwd
        """
        # Default to actual current working directory if no CWD provided
        cwd = self._normalize_cwd(cwd)

        normalized_command = (command or "").strip()
        if normalized_command == "cd..":
            normalized_command = "cd .."
        elif normalized_command.lower().startswith("cd.."):
            normalized_command = normalized_command.replace("cd..", "cd ..", 1)

        if self._is_dangerous(normalized_command):
            return {
                "success": False,
                "executed": False,
                "command": normalized_command,
                "stdout": "",
                "stderr": "Command blocked by safety policy",
                "exit_code": 126,
                "new_cwd": cwd,
                "error": "blocked"
            }
        
        try:
            # Handle 'pwd' command to show current directory
            if normalized_command == 'pwd':
                return {
                    "success": True,
                    "executed": True,
                    "command": normalized_command,
                    "stdout": cwd,
                    "stderr": "",
                    "exit_code": 0,
                    "new_cwd": cwd
                }
            
            # Handle 'cd' command specially to change directory
            if normalized_command.startswith('cd ') and '&&' not in normalized_command and ';' not in normalized_command:
                new_path = normalized_command.replace('cd ', '').strip()
                
                # Handle special cases
                if not new_path or new_path == '~':
                    new_cwd = os.path.expanduser('~')
                elif new_path == '-':
                    # cd - (go back) - just return current for now
                    new_cwd = cwd
                else:
                    # Resolve path relative to current CWD
                    new_cwd = os.path.abspath(os.path.join(cwd, os.path.expanduser(new_path)))
                
                # Check if directory exists
                if os.path.exists(new_cwd) and os.path.isdir(new_cwd):
                    return {
                        "success": True,
                        "executed": True,
                        "command": normalized_command,
                        "stdout": "",
                        "stderr": "",
                        "exit_code": 0,
                        "new_cwd": new_cwd
                    }
                else:
                    return {
                        "success": False,
                        "executed": True,
                        "command": normalized_command,
                        "stdout": "",
                        "stderr": f"cd: no such file or directory: {new_path}",
                        "exit_code": 1,
                        "new_cwd": cwd  # Keep current directory
                    }
            
            # Execute other commands
            if self.dry_run:
                return {
                    "success": True,
                    "executed": False,
                    "mode": "dry_run",
                    "command": normalized_command,
                    "stdout": "",
                    "stderr": "",
                    "exit_code": 0,
                    "new_cwd": cwd,
                    "note": "Command not executed (dry-run mode)"
                }
            
            logger.info(f"Executing command: {normalized_command} in directory: {cwd}")
            
            # Execute command in the specified directory
            # For complex commands with && (like cd foo && do bar), 
            # we need to capture the final directory if it changed successfully.
            # We append a 'pwd' command to grab the final working directory.
            cmd_with_pwd = f"{normalized_command} && pwd" if not normalized_command.endswith('& pwd') else normalized_command

            # Auto-activate .venv if it exists in the current directory
            env = os.environ.copy()
            potential_venv_bin = os.path.join(cwd, ".venv", "bin")
            if os.path.exists(potential_venv_bin):
                env["PATH"] = f"{potential_venv_bin}:{env.get('PATH', '')}"
                env["VIRTUAL_ENV"] = os.path.join(cwd, ".venv")

            result = subprocess.run(
                cmd_with_pwd,
                shell=True,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=120
            )

            stdout = result.stdout
            final_cwd = cwd
            
            # If successful, the last line of stdout from `&& pwd` is our new CWD
            if result.returncode == 0:
                lines = stdout.rstrip('\r\n').split('\n')
                if lines:
                    potential_cwd = lines[-1].strip()
                    if os.path.exists(potential_cwd) and os.path.isdir(potential_cwd):
                        final_cwd = potential_cwd
                        # Remove the pwd output from stdout
                        stdout = '\n'.join(lines[:-1])
                        if stdout: stdout += '\n'
            elif result.returncode != 0 and '&& pwd' in cmd_with_pwd:
                # Execution failed, the 'pwd' part never ran. Just return the stdout.
                pass
            
            return {
                "success": result.returncode == 0,
                "executed": True,
                "command": normalized_command,
                "stdout": stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "new_cwd": final_cwd  # Capture actual path after chained commands
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {normalized_command}")
            return {
                "success": False,
                "executed": True,
                "command": normalized_command,
                "stdout": "",
                "stderr": "Command timed out after execution limit constraint. If this is `sudo`, it may be waiting for a password in a non-interactive shell.",
                "exit_code": -1,
                "new_cwd": cwd,
                "error": "timeout"
            }
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return {
                "success": False,
                "executed": False,
                "command": normalized_command,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "new_cwd": cwd,
                "error": str(e)
            }

    def execute_plan(self, steps: List[Dict], cwd: Optional[str] = None) -> Dict:
        """
        Execute planned steps sequentially with fail-fast behavior.
        """
        current_cwd = self._normalize_cwd(cwd)
        results: List[Dict] = []

        for step in steps:
            command = step.get("command", "")
            result = self.execute(command=command, cwd=current_cwd)
            result["step_id"] = step.get("id")
            result["step_kind"] = step.get("kind")
            results.append(result)

            if result.get("new_cwd"):
                current_cwd = self._normalize_cwd(result["new_cwd"])

            if not result.get("success"):
                return {
                    "success": False,
                    "stopped_at_step": step.get("id"),
                    "results": results,
                    "new_cwd": current_cwd,
                    "error": result.get("stderr", "Step execution failed"),
                }

        return {
            "success": True,
            "results": results,
            "new_cwd": current_cwd,
            "stopped_at_step": None,
        }
