# buildOS Observability System

Real-time monitoring and logging for buildOS agent operations.

## 🎯 Overview

The buildOS observability system captures and logs all agent activity during IFC analysis, providing visibility into:
- Tool usage (IFC parsing, batch creation, agent spawning)
- Agent lifecycle (start, stop, subagent completion)
- User interactions (prompts, commands)
- Processing flow (orchestrator → batch-processor)

## 🏗️ Architecture

```
Claude Code Agent
       ↓
[Hook Triggers] → Python Scripts → Local JSON Logs
       ↓
Status Line (real-time CLI indicator)
```

## 📁 Directory Structure

```
.claude/
├── hooks/
│   └── log_event.py          # Event logging hook
├── status_lines/
│   └── buildos_status.py     # CLI status line indicator
├── data/
│   ├── logs/
│   │   └── events_YYYY-MM-DD.jsonl  # Daily event logs
│   └── sessions/              # Session data (future)
└── settings.local.json        # Hook configuration
```

## 🔧 Event Types

| Event Type       | Emoji | Triggered When                    |
|------------------|-------|-----------------------------------|
| PreToolUse       | 🔧     | Before tool execution             |
| PostToolUse      | ✅     | After tool completes              |
| UserPromptSubmit | 💬     | User submits a prompt             |
| SubagentStop     | 👥     | Subagent (batch-processor) stops  |
| Stop             | 🛑     | Main agent response completes     |

## 🚀 Usage

### View Logs

```bash
# View last 50 events
python view_logs.py

# View last 100 events
python view_logs.py 100

# View specific event type
python view_logs.py 50 PreToolUse
python view_logs.py 50 SubagentStop

# Get help
python view_logs.py --help
```

### Log Format

Events are stored in JSONL format (one JSON object per line):

```json
{
  "timestamp": "2025-11-24T19:52:30.123456",
  "event_type": "PreToolUse",
  "source_app": "buildOS",
  "session_id": "abc12345",
  "full_session_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "tool_name": "mcp__ifc__parse_ifc_file",
  "tool_input": {...}
}
```

### Status Line

The CLI status line shows real-time agent activity:

```
[buildOS] | [Claude 3.5 Sonnet] | [abc12345] | 🔧 parse_ifc_file
```

Components:
- **[buildOS]** - Application name (cyan)
- **[Model]** - Claude model being used (blue)
- **[Session]** - Truncated session ID (yellow)
- **Activity** - Current operation with emoji

## 📊 Example Workflow Trace

When running `uv run python run.py Small_condo.ifc`, you'll see:

```
💬 19:52:30 [abc12345] UserPromptSubmit → "Analyze the IFC file..."
🔧 19:52:31 [abc12345] PreToolUse → mcp__ifc__parse_ifc_file
✅ 19:52:45 [abc12345] PostToolUse → mcp__ifc__parse_ifc_file ✓
🔧 19:52:46 [abc12345] PreToolUse → mcp__ifc__prepare_classification_batches
✅ 19:52:47 [abc12345] PostToolUse → mcp__ifc__prepare_classification_batches ✓
🔧 19:52:48 [abc12345] PreToolUse → Task
👥 19:53:45 [def67890] SubagentStop → batch-processor (completed)
✅ 19:53:46 [abc12345] PostToolUse → Task ✓
🛑 19:53:47 [abc12345] Stop
```

This shows:
1. User initiates IFC analysis
2. Orchestrator parses IFC file (14 seconds)
3. Orchestrator creates batches (1 second)
4. Orchestrator spawns batch-processor agent
5. Batch-processor completes classification (57 seconds)
6. Orchestrator receives results
7. Main agent completes response

## 🔗 Integration with Full Observability System

To connect buildOS to the full multi-agent observability dashboard (optional):

1. Clone the observability repo:
   ```bash
   git clone https://github.com/yourusername/claude-code-hooks-multi-agent-observability.git
   cd claude-code-hooks-multi-agent-observability
   ```

2. Start the server:
   ```bash
   ./scripts/start-system.sh
   ```

3. Update buildOS `.claude/settings.local.json` to send events to server:
   ```json
   {
     "hooks": {
       "PreToolUse": [{
         "matcher": "",
         "hooks": [
           {
             "type": "command",
             "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/log_event.py --source-app buildOS --event-type PreToolUse"
           },
           {
             "type": "command",
             "command": "uv run /path/to/observability/.claude/hooks/send_event.py --source-app buildOS --event-type PreToolUse --summarize"
           }
         ]
       }]
     }
   }
   ```

4. Open dashboard: http://localhost:5173

## 🎨 Status Line Customization

Edit `.claude/status_lines/buildos_status.py` to customize:
- Colors (ANSI escape codes)
- Displayed information
- Event filtering
- Format and layout

## 📝 Log Retention

- Logs are organized by date: `events_YYYY-MM-DD.jsonl`
- No automatic cleanup (manage manually as needed)
- Typical log size: ~1KB per 10 events

## 🐛 Troubleshooting

### Hooks not triggering

1. Check that `.claude/settings.local.json` exists
2. Verify `$CLAUDE_PROJECT_DIR` environment variable
3. Test hook script manually:
   ```bash
   echo '{"session_id": "test", "tool_use": {"name": "Test"}}' | \
     uv run .claude/hooks/log_event.py --source-app buildOS --event-type PreToolUse
   ```

### Status line not showing

1. Verify script is executable: `chmod +x .claude/status_lines/buildos_status.py`
2. Check for syntax errors: `python .claude/status_lines/buildos_status.py`
3. Ensure `statusLine` is configured in settings.local.json

### Logs not appearing

1. Check `.claude/data/logs/` directory exists
2. Verify write permissions
3. Look for error messages in Claude Code output

## 🔍 Advanced Analysis

### Count events by type

```bash
jq -s 'group_by(.event_type) | map({type: .[0].event_type, count: length})' \
  .claude/data/logs/events_*.jsonl
```

### Find slow tools

```bash
jq -s '.[] | select(.event_type == "PostToolUse") | {tool: .tool_name, time: .timestamp}' \
  .claude/data/logs/events_*.jsonl
```

### Track agent sessions

```bash
jq -s 'group_by(.session_id) | map({session: .[0].session_id, events: length})' \
  .claude/data/logs/events_*.jsonl
```

## 🚀 Future Enhancements

- [ ] Real-time dashboard integration
- [ ] Performance metrics (tool execution time)
- [ ] Agent communication visualization
- [ ] Error rate tracking
- [ ] Batch processing analytics
- [ ] Cost tracking per session

---

*Part of buildOS - BIM AI CO2 Analysis System*
