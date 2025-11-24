#!/usr/bin/env python3
"""
buildOS Log Viewer
View agent activity logs in a readable format
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def format_timestamp(iso_time):
    """Format ISO timestamp to readable time."""
    try:
        dt = datetime.fromisoformat(iso_time)
        return dt.strftime("%H:%M:%S")
    except:
        return iso_time

def get_event_color(event_type):
    """Get ANSI color for event type."""
    colors = {
        'PreToolUse': '\033[96m',  # Cyan
        'PostToolUse': '\033[92m',  # Green
        'UserPromptSubmit': '\033[93m',  # Yellow
        'SubagentStop': '\033[95m',  # Magenta
        'Stop': '\033[91m',  # Red
    }
    return colors.get(event_type, '\033[97m')  # White default

def get_event_emoji(event_type):
    """Get emoji for event type."""
    emojis = {
        'PreToolUse': '🔧',
        'PostToolUse': '✅',
        'UserPromptSubmit': '💬',
        'SubagentStop': '👥',
        'Stop': '🛑',
    }
    return emojis.get(event_type, '📝')

def view_logs(limit=50, event_filter=None):
    """View recent logs."""
    log_dir = Path(".claude/data/logs")
    
    if not log_dir.exists():
        print("No logs found. Run buildOS first to generate logs.")
        return
    
    # Get all log files sorted by date (newest first)
    log_files = sorted(log_dir.glob("events_*.jsonl"), reverse=True)
    
    if not log_files:
        print("No log files found.")
        return
    
    print("\n" + "="*80)
    print(f"{'buildOS Agent Activity Logs':^80}")
    print("="*80 + "\n")
    
    events = []
    
    # Read events from log files
    for log_file in log_files:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    if event_filter is None or event['event_type'] == event_filter:
                        events.append(event)
                except:
                    pass
    
    # Sort by timestamp (newest first) and limit
    events = sorted(events, key=lambda e: e['timestamp'], reverse=True)[:limit]
    events = list(reversed(events))  # Show chronologically
    
    # Display events
    for event in events:
        time = format_timestamp(event['timestamp'])
        event_type = event['event_type']
        session = event['session_id']
        color = get_event_color(event_type)
        emoji = get_event_emoji(event_type)
        reset = '\033[0m'
        
        # Base info
        print(f"{color}{emoji} {time}{reset} [{session}] {color}{event_type}{reset}", end="")
        
        # Event-specific details
        if event_type == 'PreToolUse':
            tool = event.get('tool_name', '?')
            print(f" → {tool}")
        elif event_type == 'PostToolUse':
            tool = event.get('tool_name', '?')
            success = event.get('success', True)
            status = "✓" if success else "✗"
            print(f" → {tool} {status}")
        elif event_type == 'UserPromptSubmit':
            prompt = event.get('prompt', '')
            print(f" → \"{prompt}\"")
        elif event_type == 'SubagentStop':
            subagent = event.get('subagent_type', '?')
            status = event.get('status', '?')
            print(f" → {subagent} ({status})")
        else:
            print()
    
    print(f"\n{'-'*80}")
    print(f"Showing {len(events)} most recent events")
    print(f"Log directory: {log_dir.absolute()}\n")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage: python view_logs.py [limit] [event_type]")
            print("\nExamples:")
            print("  python view_logs.py           # Show last 50 events")
            print("  python view_logs.py 100       # Show last 100 events")
            print("  python view_logs.py 50 PreToolUse  # Show last 50 PreToolUse events")
            return
        
        try:
            limit = int(sys.argv[1])
        except:
            limit = 50
        
        event_filter = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        limit = 50
        event_filter = None
    
    view_logs(limit, event_filter)

if __name__ == '__main__':
    main()
