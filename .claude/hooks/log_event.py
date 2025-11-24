#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
buildOS Observability Hook - Local Logging
Logs Claude Code hook events to local JSON files for post-analysis.
"""

import json
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

def ensure_log_dir():
    """Ensure log directory exists."""
    log_dir = Path(".claude/data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def log_event(event_type, source_app, input_data):
    """Log event to local JSON file."""
    try:
        log_dir = ensure_log_dir()
        
        # Create timestamped log file (one per day)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"events_{today}.jsonl"
        
        # Extract key info
        session_id = input_data.get('session_id', 'unknown')
        
        # Build event entry
        event_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'source_app': source_app,
            'session_id': session_id[:8],  # Truncate for readability
            'full_session_id': session_id,
        }
        
        # Add event-specific data
        if event_type == 'PreToolUse':
            event_entry['tool_name'] = input_data.get('tool_use', {}).get('name', 'unknown')
            event_entry['tool_input'] = input_data.get('tool_use', {}).get('input', {})
        elif event_type == 'PostToolUse':
            event_entry['tool_name'] = input_data.get('tool_use', {}).get('name', 'unknown')
            event_entry['success'] = 'error' not in str(input_data.get('result', {})).lower()
        elif event_type == 'UserPromptSubmit':
            user_msg = input_data.get('user_message', {})
            prompt_text = ""
            if isinstance(user_msg, dict):
                content = user_msg.get('content', [])
                if content and len(content) > 0:
                    prompt_text = content[0].get('text', '')
            event_entry['prompt'] = prompt_text[:100]  # First 100 chars
        elif event_type == 'SubagentStop':
            event_entry['subagent_type'] = input_data.get('subagent', {}).get('subagent_type', 'unknown')
            event_entry['status'] = input_data.get('subagent', {}).get('status', 'unknown')
        elif event_type == 'Stop':
            event_entry['status'] = 'completed'
        
        # Append to log file (JSONL format)
        with open(log_file, 'a') as f:
            f.write(json.dumps(event_entry) + '\n')
        
        return True
        
    except Exception as e:
        print(f"Failed to log event: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description='Log Claude Code hook events locally')
    parser.add_argument('--source-app', required=True, help='Source application name')
    parser.add_argument('--event-type', required=True, help='Hook event type')
    
    args = parser.parse_args()
    
    try:
        # Read hook data from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON input: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block Claude operations
    
    # Log the event
    log_event(args.event_type, args.source_app, input_data)
    
    # Always exit with 0 to not block Claude Code
    sys.exit(0)

if __name__ == '__main__':
    main()
