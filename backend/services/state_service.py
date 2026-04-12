import os
from dataclasses import dataclass, field
from threading import RLock
from typing import Dict, Optional, Set


@dataclass
class SessionState:
    """Runtime state stored per session."""
    session_id: str
    cwd: str
    installed_tools: Set[str] = field(default_factory=set)
    environment_status: Dict[str, str] = field(default_factory=dict)


class StateService:
    """
    In-memory session state manager.

    Maintains cwd and environment/tool cache per session across requests.
    """

    def __init__(self, base_directory: Optional[str] = None):
        self.base_directory = os.path.abspath(base_directory or os.getcwd())
        self._sessions: Dict[str, SessionState] = {}
        self._lock = RLock()

    def _safe_cwd(self, cwd: Optional[str]) -> str:
        candidate = os.path.abspath(os.path.expanduser(cwd or self.base_directory))
        if not os.path.isdir(candidate):
            return self.base_directory
        return candidate

    def get_or_create_session(self, session_id: str, cwd: Optional[str] = None) -> SessionState:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionState(
                    session_id=session_id,
                    cwd=self._safe_cwd(cwd),
                )
            return self._sessions[session_id]

    def update_cwd(self, session_id: str, cwd: str) -> SessionState:
        with self._lock:
            session = self.get_or_create_session(session_id)
            session.cwd = self._safe_cwd(cwd)
            return session

    def mark_tool(self, session_id: str, tool_name: str, status: str = "available") -> None:
        with self._lock:
            session = self.get_or_create_session(session_id)
            if status == "available":
                session.installed_tools.add(tool_name)
            session.environment_status[tool_name] = status

    def get_state_snapshot(self, session_id: str) -> Dict:
        session = self.get_or_create_session(session_id)
        return {
            "session_id": session.session_id,
            "cwd": session.cwd,
            "installed_tools": sorted(session.installed_tools),
            "environment_status": session.environment_status,
        }
