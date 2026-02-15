# services/executor_service.py

import os
import subprocess
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ExecutorService:
    """
    Service for safe command execution with CWD tracking
    Handles actual terminal command execution with directory management
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize executor service
        
        Args:
            dry_run: If True, commands won't actually execute
        """
        self.dry_run = dry_run
        logger.info(f"ExecutorService initialized (dry_run={dry_run})")
    
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
        if not cwd or cwd == '~' or cwd == '':
            cwd = os.getcwd()
        else:
            cwd = os.path.abspath(os.path.expanduser(cwd))
        
        # Ensure directory exists
        if not os.path.exists(cwd):
            cwd = os.getcwd()
        
        try:
            # Handle 'pwd' command to show current directory
            if command.strip() == 'pwd':
                return {
                    "success": True,
                    "executed": True,
                    "command": command,
                    "stdout": cwd,
                    "stderr": "",
                    "exit_code": 0,
                    "new_cwd": cwd
                }
            
            # Handle 'cd' command specially to change directory
            if command.strip().startswith('cd '):
                new_path = command.replace('cd ', '').strip()
                
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
                        "command": command,
                        "stdout": "",
                        "stderr": "",
                        "exit_code": 0,
                        "new_cwd": new_cwd
                    }
                else:
                    return {
                        "success": False,
                        "executed": True,
                        "command": command,
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
                    "command": command,
                    "stdout": "",
                    "stderr": "",
                    "exit_code": 0,
                    "new_cwd": cwd,
                    "note": "Command not executed (dry-run mode)"
                }
            
            logger.info(f"Executing command: {command} in directory: {cwd}")
            
            # Execute command in the specified directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "executed": True,
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "new_cwd": cwd  # CWD stays same for non-cd commands
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return {
                "success": False,
                "executed": True,
                "command": command,
                "stdout": "",
                "stderr": "Command timed out after 30 seconds",
                "exit_code": -1,
                "new_cwd": cwd,
                "error": "timeout"
            }
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return {
                "success": False,
                "executed": False,
                "command": command,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "new_cwd": cwd,
                "error": str(e)
            }
