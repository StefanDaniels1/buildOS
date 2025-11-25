"""Helper to send events to observability dashboard"""
import json
import urllib.request
import sys
from datetime import datetime

def send_event(event_type, tool_name=None, status=None, session_id="buildos-direct", payload=None):
    """Send event to observability dashboard"""
    event = {
        "source_app": "buildOS",
        "session_id": session_id,
        "hook_event_type": event_type,
        "timestamp": int(datetime.now().timestamp() * 1000),
        "payload": payload or {}
    }
    
    if tool_name:
        event["payload"]["tool_name"] = tool_name
    if status:
        event["payload"]["status"] = status
    
    try:
        req = urllib.request.Request(
            "http://localhost:4000/events",
            data=json.dumps(event).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except:
        return False  # Silently fail if dashboard not running

if __name__ == "__main__":
    # Test
    send_event("PreToolUse", tool_name="test", payload={"test": True})
    print("Event sent to dashboard")
