#!/usr/bin/env python3
"""
Hook Event Sender for buildOS agent_system5

Sends PreToolUse and PostToolUse events to the dashboard server.
This provides detailed tool-level observability for subagent operations.
"""

import sys
import json
import os
from datetime import datetime

try:
    import httpx
except ImportError:
    # Gracefully handle missing httpx - hooks should never crash
    sys.exit(0)


def send_event(event_type: str, payload: dict):
    """Send event to dashboard server."""
    # Get session ID from environment or use default
    session_id = os.environ.get("BUILDOS_SESSION_ID", "unknown")
    dashboard_url = os.environ.get("DASHBOARD_URL", "http://localhost:4000")

    try:
        with httpx.Client(timeout=2.0) as client:
            client.post(
                f"{dashboard_url}/events",
                json={
                    "source_app": "buildos-orchestrator",
                    "session_id": session_id,
                    "hook_event_type": event_type,
                    "payload": payload
                }
            )
    except Exception:
        # Silently fail - hooks should never block operations
        pass


def main():
    """
    Hook entry point called by Claude Code.

    Hook context is provided via stdin as JSON with structure:
    {
        "hook_event_type": "PreToolUse" | "PostToolUse",
        "tool_name": string,
        "tool_input": object,
        "tool_result": object (PostToolUse only)
    }
    """
    try:
        # Read hook context from stdin
        hook_context = json.loads(sys.stdin.read())

        event_type = hook_context.get("hook_event_type")
        tool_name = hook_context.get("tool_name", "unknown")

        if event_type == "PreToolUse":
            # Tool about to execute
            send_event("ToolStart", {
                "tool_name": tool_name,
                "tool_input": hook_context.get("tool_input", {}),
                "timestamp": datetime.now().isoformat()
            })

        elif event_type == "PostToolUse":
            # Tool completed
            tool_result = hook_context.get("tool_result", {})
            is_error = tool_result.get("is_error", False)

            send_event("ToolStop", {
                "tool_name": tool_name,
                "status": "error" if is_error else "success",
                "timestamp": datetime.now().isoformat()
            })

    except Exception:
        # Hooks must never crash
        pass


if __name__ == "__main__":
    main()
