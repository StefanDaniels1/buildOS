#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
buildOS Status Line - Shows current agent activity and IFC processing progress
"""

import json
import sys
from pathlib import Path

def get_latest_event():
    """Get most recent event from logs."""
    log_dir = Path(".claude/data/logs")
    if not log_dir.exists():
        return None
    
    # Find most recent log file
    log_files = sorted(log_dir.glob("events_*.jsonl"), reverse=True)
    if not log_files:
        return None
    
    # Read last line of most recent file
    try:
        with open(log_files[0], 'r') as f:
            lines = f.readlines()
            if lines:
                return json.loads(lines[-1])
    except:
        pass
    
    return None

def generate_status_line(input_data):
    """Generate status line showing agent activity."""
    # Get model info
    model_info = input_data.get("model", {})
    model_name = model_info.get("display_name", "Claude")
    
    # Get session ID
    session_id = input_data.get("session_id", "unknown")[:8]
    
    # Get latest event for context
    latest_event = get_latest_event()
    
    parts = []
    
    # App name - Cyan
    parts.append(f"\033[36m[buildOS]\033[0m")
    
    # Model - Blue  
    parts.append(f"\033[34m[{model_name}]\033[0m")
    
    # Session - Yellow
    parts.append(f"\033[33m[{session_id}]\033[0m")
    
    # Activity indicator based on latest event
    if latest_event:
        event_type = latest_event.get('event_type', '')
        
        if event_type == 'PreToolUse':
            tool_name = latest_event.get('tool_name', '?')
            parts.append(f"🔧 \033[92m{tool_name}\033[0m")
        elif event_type == 'PostToolUse':
            tool_name = latest_event.get('tool_name', '?')
            success = latest_event.get('success', True)
            icon = "✅" if success else "❌"
            parts.append(f"{icon} \033[90m{tool_name}\033[0m")
        elif event_type == 'SubagentStop':
            subagent = latest_event.get('subagent_type', 'agent')
            parts.append(f"👥 \033[95m{subagent}\033[0m")
        elif event_type == 'UserPromptSubmit':
            prompt = latest_event.get('prompt', '')[:30]
            parts.append(f"💬 \033[97m{prompt}...\033[0m")
        else:
            parts.append(f"\033[90m{event_type}\033[0m")
    else:
        parts.append("\033[90m💭 Ready\033[0m")
    
    return " | ".join(parts)

def main():
    try:
        input_data = json.loads(sys.stdin.read())
        status_line = generate_status_line(input_data)
        print(status_line)
        sys.exit(0)
    except:
        print("\033[36m[buildOS]\033[0m \033[90m💭 Status unavailable\033[0m")
        sys.exit(0)

if __name__ == "__main__":
    main()
