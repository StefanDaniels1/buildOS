"""
Conversation Logger for buildOS Orchestrator

Captures full conversation details including:
- User messages
- Assistant responses
- Tool calls with inputs/outputs
- Errors and exceptions
- Session metadata

Logs are stored per session for easy debugging.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional


class ConversationLogger:
    """Logs full conversation details for debugging."""

    def __init__(self, session_id: str, log_dir: str = "./.logs/conversations"):
        self.session_id = session_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create session-specific log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"session_{session_id[:8]}_{timestamp}.jsonl"

        # Initialize session
        self._write_event({
            "event": "session_start",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "log_file": str(self.log_file)
        })

    def log_user_message(self, message: str, file_path: Optional[str] = None):
        """Log user's message."""
        self._write_event({
            "event": "user_message",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "file_path": file_path
        })

    def log_assistant_message(self, message: str):
        """Log assistant's response."""
        self._write_event({
            "event": "assistant_message",
            "timestamp": datetime.now().isoformat(),
            "message": message
        })

    def log_tool_use(self, tool_name: str, tool_input: Dict[str, Any], tool_output: Any, success: bool = True, error: Optional[str] = None):
        """Log tool usage with full details."""
        self._write_event({
            "event": "tool_use",
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": self._serialize(tool_output),
            "success": success,
            "error": error
        })

    def log_agent_spawn(self, agent_type: str, agent_id: str, prompt: str):
        """Log agent spawning."""
        self._write_event({
            "event": "agent_spawn",
            "timestamp": datetime.now().isoformat(),
            "agent_type": agent_type,
            "agent_id": agent_id,
            "prompt": prompt
        })

    def log_agent_response(self, agent_id: str, response: str):
        """Log agent response."""
        self._write_event({
            "event": "agent_response",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "response": response
        })

    def log_error(self, error_type: str, error_message: str, traceback: Optional[str] = None):
        """Log errors."""
        self._write_event({
            "event": "error",
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "traceback": traceback
        })

    def log_session_end(self, status: str = "completed", summary: Optional[Dict[str, Any]] = None):
        """Log session end."""
        self._write_event({
            "event": "session_end",
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "summary": summary
        })

    def log_system_context(self, context: Dict[str, Any]):
        """Log system context for debugging."""
        self._write_event({
            "event": "system_context",
            "timestamp": datetime.now().isoformat(),
            **context
        })

    def log_debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log debug information."""
        self._write_event({
            "event": "debug",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data
        })

    def log_validation(self, agent_id: str, is_valid: bool, reason: str, feedback: Optional[str] = None, retry_count: int = 0):
        """Log validation of subagent response."""
        self._write_event({
            "event": "validation",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "is_valid": is_valid,
            "reason": reason,
            "feedback": feedback,
            "retry_count": retry_count
        })

    def log_model_prompt(self, role: str, content: str, model: Optional[str] = None, agent_id: Optional[str] = None):
        """Log model prompts (user/system/assistant messages)."""
        self._write_event({
            "event": "model_prompt",
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "model": model,
            "agent_id": agent_id
        })

    def log_model_thinking(self, thinking: str, agent_id: Optional[str] = None):
        """Log model thinking/reasoning (TextBlock from AssistantMessage)."""
        self._write_event({
            "event": "model_thinking",
            "timestamp": datetime.now().isoformat(),
            "thinking": thinking,
            "agent_id": agent_id
        })

    def log_tool_call(self, tool_name: str, tool_input: Dict[str, Any], agent_id: Optional[str] = None):
        """Log tool call initiation."""
        self._write_event({
            "event": "tool_call",
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "tool_input": self._serialize(tool_input),
            "agent_id": agent_id
        })

    def log_tool_result(self, tool_name: str, tool_output: Any, success: bool = True, error: Optional[str] = None, agent_id: Optional[str] = None):
        """Log tool execution result."""
        self._write_event({
            "event": "tool_result",
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "tool_output": self._serialize(tool_output),
            "success": success,
            "error": error,
            "agent_id": agent_id
        })

    def log_model_metrics(self, metrics: Dict[str, Any], agent_id: Optional[str] = None):
        """Log model usage metrics (tokens, cost, duration)."""
        self._write_event({
            "event": "model_metrics",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            **metrics
        })

    def _write_event(self, event: Dict[str, Any]):
        """Write event to log file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            print(f"Failed to write to log: {e}")

    def _serialize(self, obj: Any) -> Any:
        """Serialize objects for JSON logging."""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize(item) for item in obj]
        else:
            return str(obj)

    @classmethod
    def load_session(cls, session_id: str, log_dir: str = "./.logs/conversations") -> list:
        """Load all events from a session log."""
        log_dir = Path(log_dir)

        # Find log file for this session
        pattern = f"session_{session_id[:8]}_*.jsonl"
        log_files = list(log_dir.glob(pattern))

        if not log_files:
            return []

        # Get most recent log file
        log_file = sorted(log_files, reverse=True)[0]

        events = []
        with open(log_file, 'r') as f:
            for line in f:
                events.append(json.loads(line))

        return events

    @classmethod
    def get_recent_sessions(cls, log_dir: str = "./.logs/conversations", limit: int = 10) -> list:
        """Get list of recent session log files."""
        log_dir = Path(log_dir)

        if not log_dir.exists():
            return []

        log_files = sorted(log_dir.glob("session_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)

        sessions = []
        for log_file in log_files[:limit]:
            # Read first event to get session info
            with open(log_file, 'r') as f:
                first_event = json.loads(f.readline())
                sessions.append({
                    "session_id": first_event.get("session_id"),
                    "start_time": first_event.get("timestamp"),
                    "log_file": str(log_file)
                })

        return sessions
