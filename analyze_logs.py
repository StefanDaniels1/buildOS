#!/usr/bin/env python3
"""
Session Log Analyzer

Utility script for analyzing buildOS conversation logs.
Provides insights into model usage, tool calls, and session patterns.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any
import argparse


class LogAnalyzer:
    """Analyze conversation logs."""

    def __init__(self, log_dir: str = "./.logs/conversations"):
        self.log_dir = Path(log_dir)
        self.sessions = []
        self._load_sessions()

    def _load_sessions(self):
        """Load all session logs."""
        if not self.log_dir.exists():
            print(f"No logs found at {self.log_dir}")
            return

        for log_file in sorted(self.log_dir.glob("session_*.jsonl")):
            events = []
            with open(log_file, 'r') as f:
                for line in f:
                    events.append(json.loads(line))
            
            if events:
                self.sessions.append({
                    'file': log_file.name,
                    'events': events,
                    'session_id': events[0].get('session_id', 'unknown')
                })

    def list_sessions(self):
        """List all available sessions."""
        print(f"\n{'='*80}")
        print(f"Found {len(self.sessions)} session(s)")
        print(f"{'='*80}\n")

        for i, session in enumerate(self.sessions, 1):
            events = session['events']
            start_event = events[0]
            end_event = events[-1] if events else None

            session_id = start_event.get('session_id', 'unknown')
            start_time = start_event.get('timestamp', 'unknown')
            
            user_msg = next((e for e in events if e.get('event') == 'user_message'), None)
            user_query = user_msg.get('message', 'N/A') if user_msg else 'N/A'

            status = end_event.get('status', 'unknown') if end_event and end_event.get('event') == 'session_end' else 'running'

            print(f"{i}. Session: {session_id[:16]}")
            print(f"   File: {session['file']}")
            print(f"   Start: {start_time}")
            print(f"   Status: {status}")
            print(f"   Query: {user_query[:70]}...")
            print(f"   Events: {len(events)}")
            print()

    def analyze_session(self, session_idx: int):
        """Analyze a specific session."""
        if session_idx < 0 or session_idx >= len(self.sessions):
            print(f"Invalid session index. Use 0-{len(self.sessions)-1}")
            return

        session = self.sessions[session_idx]
        events = session['events']

        print(f"\n{'='*80}")
        print(f"Session Analysis: {session['session_id'][:16]}")
        print(f"{'='*80}\n")

        # Event counts
        event_types = Counter(e.get('event') for e in events)
        print("📊 Event Breakdown:")
        for event_type, count in event_types.most_common():
            print(f"   {event_type}: {count}")
        print()

        # User message
        user_msg = next((e for e in events if e.get('event') == 'user_message'), None)
        if user_msg:
            print("👤 User Query:")
            print(f"   {user_msg.get('message')}")
            if user_msg.get('file_path'):
                print(f"   File: {user_msg.get('file_path')}")
            print()

        # Model prompts
        prompts = [e for e in events if e.get('event') == 'model_prompt']
        if prompts:
            print(f"🤖 Model Prompts ({len(prompts)}):")
            for i, prompt in enumerate(prompts, 1):
                role = prompt.get('role', 'unknown')
                model = prompt.get('model', 'unknown')
                agent = prompt.get('agent_id', 'unknown')
                content_len = len(prompt.get('content', ''))
                print(f"   {i}. {role} → {model} ({agent}) - {content_len} chars")
            print()

        # Tool calls
        tool_calls = [e for e in events if e.get('event') == 'tool_call']
        if tool_calls:
            print(f"🔧 Tool Calls ({len(tool_calls)}):")
            tool_counts = Counter(t.get('tool_name') for t in tool_calls)
            for tool_name, count in tool_counts.most_common():
                print(f"   {tool_name}: {count}x")
            print()

        # Agent spawns
        agents = [e for e in events if e.get('event') == 'agent_spawn']
        if agents:
            print(f"🚀 Agents Spawned ({len(agents)}):")
            for agent in agents:
                agent_type = agent.get('agent_type', 'unknown')
                agent_id = agent.get('agent_id', 'unknown')
                prompt = agent.get('prompt', '')[:60]
                print(f"   {agent_type} ({agent_id})")
                print(f"      → {prompt}...")
            print()

        # Metrics
        metrics = [e for e in events if e.get('event') == 'model_metrics']
        if metrics:
            total_cost = sum(m.get('cost_usd', 0) or 0 for m in metrics)
            total_duration = sum(m.get('duration_ms', 0) or 0 for m in metrics)
            total_turns = sum(m.get('num_turns', 0) or 0 for m in metrics)
            
            print("📈 Metrics:")
            print(f"   Cost: ${total_cost:.4f}")
            print(f"   Duration: {total_duration}ms ({total_duration/1000:.2f}s)")
            print(f"   Turns: {total_turns}")
            print()

        # Errors
        errors = [e for e in events if e.get('event') == 'error']
        if errors:
            print(f"❌ Errors ({len(errors)}):")
            for error in errors:
                error_type = error.get('error_type', 'unknown')
                error_msg = error.get('error_message', '')[:70]
                print(f"   {error_type}: {error_msg}...")
            print()

        # Status
        end_event = events[-1] if events and events[-1].get('event') == 'session_end' else None
        if end_event:
            status = end_event.get('status', 'unknown')
            print(f"✅ Status: {status}")
        else:
            print("⚠️  Status: Session did not complete normally")
        print()

    def show_thinking(self, session_idx: int):
        """Show model thinking/reasoning for a session."""
        if session_idx < 0 or session_idx >= len(self.sessions):
            print(f"Invalid session index. Use 0-{len(self.sessions)-1}")
            return

        session = self.sessions[session_idx]
        events = session['events']

        print(f"\n{'='*80}")
        print(f"Model Thinking: {session['session_id'][:16]}")
        print(f"{'='*80}\n")

        thinking_events = [e for e in events if e.get('event') == 'model_thinking']
        
        if not thinking_events:
            print("No thinking events found.")
            return

        for i, event in enumerate(thinking_events, 1):
            agent = event.get('agent_id', 'unknown')
            thinking = event.get('thinking', '')
            timestamp = event.get('timestamp', '')
            
            print(f"[{i}] {agent} @ {timestamp}")
            print(f"{thinking}")
            print(f"{'-'*80}")

    def show_tools(self, session_idx: int):
        """Show tool calls and results for a session."""
        if session_idx < 0 or session_idx >= len(self.sessions):
            print(f"Invalid session index. Use 0-{len(self.sessions)-1}")
            return

        session = self.sessions[session_idx]
        events = session['events']

        print(f"\n{'='*80}")
        print(f"Tool Usage: {session['session_id'][:16]}")
        print(f"{'='*80}\n")

        tool_calls = [e for e in events if e.get('event') in ('tool_call', 'tool_result')]
        
        if not tool_calls:
            print("No tool calls found.")
            return

        for i, event in enumerate(tool_calls, 1):
            event_type = event.get('event')
            timestamp = event.get('timestamp', '')
            
            if event_type == 'tool_call':
                tool_name = event.get('tool_name', 'unknown')
                tool_input = json.dumps(event.get('tool_input', {}), indent=2)
                agent = event.get('agent_id', 'unknown')
                
                print(f"🔧 [{i}] CALL: {tool_name} ({agent})")
                print(f"   @ {timestamp}")
                print(f"   Input: {tool_input}")
                
            elif event_type == 'tool_result':
                tool_output = str(event.get('tool_output', ''))[:200]
                success = event.get('success', True)
                status = "✅" if success else "❌"
                
                print(f"{status} [{i}] RESULT:")
                print(f"   @ {timestamp}")
                print(f"   Output: {tool_output}...")
            
            print(f"{'-'*80}")

    def compare_sessions(self):
        """Compare metrics across all sessions."""
        print(f"\n{'='*80}")
        print(f"Session Comparison")
        print(f"{'='*80}\n")

        if not self.sessions:
            print("No sessions to compare.")
            return

        print(f"{'Session':<20} {'Events':<10} {'Tools':<10} {'Agents':<10} {'Cost':<10} {'Duration':<12}")
        print(f"{'-'*80}")

        for session in self.sessions:
            events = session['events']
            session_id = session['session_id'][:16]
            
            event_count = len(events)
            tool_count = len([e for e in events if e.get('event') == 'tool_call'])
            agent_count = len([e for e in events if e.get('event') == 'agent_spawn'])
            
            metrics = [e for e in events if e.get('event') == 'model_metrics']
            total_cost = sum(m.get('cost_usd', 0) or 0 for m in metrics)
            total_duration = sum(m.get('duration_ms', 0) or 0 for m in metrics)
            
            print(f"{session_id:<20} {event_count:<10} {tool_count:<10} {agent_count:<10} ${total_cost:<9.4f} {total_duration/1000:<11.2f}s")


def main():
    parser = argparse.ArgumentParser(description="Analyze buildOS session logs")
    parser.add_argument('--log-dir', default='./.logs/conversations', help='Log directory path')
    parser.add_argument('--list', action='store_true', help='List all sessions')
    parser.add_argument('--analyze', type=int, metavar='N', help='Analyze session N')
    parser.add_argument('--thinking', type=int, metavar='N', help='Show thinking for session N')
    parser.add_argument('--tools', type=int, metavar='N', help='Show tool usage for session N')
    parser.add_argument('--compare', action='store_true', help='Compare all sessions')

    args = parser.parse_args()

    analyzer = LogAnalyzer(args.log_dir)

    if args.list or (not args.analyze and not args.thinking and not args.tools and not args.compare):
        analyzer.list_sessions()
    
    if args.analyze is not None:
        analyzer.analyze_session(args.analyze)
    
    if args.thinking is not None:
        analyzer.show_thinking(args.thinking)
    
    if args.tools is not None:
        analyzer.show_tools(args.tools)
    
    if args.compare:
        analyzer.compare_sessions()


if __name__ == "__main__":
    main()
