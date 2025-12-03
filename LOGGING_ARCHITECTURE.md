# buildOS Agent System - Logging Architecture

## Overview

The buildOS agent system implements **comprehensive observability** for multi-agent workflows. Every prompt, model input/output, tool call, and agent interaction is captured for debugging, quality analysis, and continuous improvement.

## Design Principles

### 1. **Zero Redundancy**
- Leverages existing event streaming infrastructure (`stream_to_dashboard`)
- Logs are written at the same point where dashboard events are sent
- Single source of truth for both real-time UI and persistent logs

### 2. **Complete Visibility**
- **Model Prompts**: Every prompt sent to Claude (orchestrator and subagents)
- **Model Thinking**: All reasoning/thinking blocks from model responses
- **Tool Calls**: Full tool inputs (not just tool names)
- **Tool Results**: Complete tool outputs and error details
- **Agent Spawns**: Subagent types, prompts, and IDs
- **Metrics**: Cost, tokens, duration for each model call

### 3. **Structured Logging**
- JSONL format (one event per line)
- Easy to parse, grep, and analyze
- Each event is timestamped and typed
- Session-scoped for easy debugging

## Log Structure

### Storage Location
```
.logs/conversations/session_{session_id[:8]}_{timestamp}.jsonl
```

### Event Types

#### 1. Session Events
```json
{"event": "session_start", "session_id": "...", "timestamp": "..."}
{"event": "session_end", "status": "completed", "summary": {...}}
```

#### 2. User Input
```json
{
  "event": "user_message",
  "timestamp": "...",
  "message": "How many wooden elements?",
  "file_path": "/path/to/file.ifc"
}
```

#### 3. Model Prompts (NEW!)
```json
{
  "event": "model_prompt",
  "timestamp": "...",
  "role": "system",
  "content": "You are the buildOS orchestrator...",
  "model": "claude-sonnet-4-5",
  "agent_id": "orchestrator"
}
```

#### 4. Model Thinking (NEW!)
```json
{
  "event": "model_thinking",
  "timestamp": "...",
  "thinking": "I need to classify this as a Simple Query...",
  "agent_id": "orchestrator"
}
```

#### 5. Tool Calls (NEW!)
```json
{
  "event": "tool_call",
  "timestamp": "...",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "data-prep",
    "description": "Parse Small_condo.ifc",
    "model": "haiku"
  },
  "agent_id": "orchestrator"
}
```

#### 6. Tool Results (NEW!)
```json
{
  "event": "tool_result",
  "timestamp": "...",
  "tool_name": "Task",
  "tool_output": "Batch file created: batches.json",
  "success": true,
  "error": null,
  "agent_id": "orchestrator"
}
```

#### 7. Agent Spawns
```json
{
  "event": "agent_spawn",
  "timestamp": "...",
  "agent_type": "data-prep",
  "agent_id": "data-prep_abc12345",
  "prompt": "Parse Small_condo.ifc and create classification batches"
}
```

#### 8. Model Metrics (NEW!)
```json
{
  "event": "model_metrics",
  "timestamp": "...",
  "agent_id": "orchestrator",
  "cost_usd": 0.0234,
  "duration_ms": 3421,
  "num_turns": 2
}
```

#### 9. Errors
```json
{
  "event": "error",
  "timestamp": "...",
  "error_type": "FileNotFoundError",
  "error_message": "File not found: ...",
  "traceback": "..."
}
```

## Implementation

### Architecture Flow

```
User Request → Orchestrator
    ↓
    ├─→ ConversationLogger.log_user_message()
    ├─→ ConversationLogger.log_model_prompt()  ← NEW!
    ↓
SDK Client.query(prompt)
    ↓
SDK streams messages → stream_to_dashboard()
    ↓
    ├─→ Dashboard Events (real-time UI)
    └─→ ConversationLogger.log_*() ← NEW!
         ├─→ log_model_thinking()
         ├─→ log_tool_call()
         ├─→ log_tool_result()
         ├─→ log_agent_spawn()
         └─→ log_model_metrics()
```

### Key Files

1. **`conversation_logger.py`** - Enhanced with new logging methods:
   - `log_model_prompt()` - Captures prompts sent to models
   - `log_model_thinking()` - Captures model reasoning
   - `log_tool_call()` - Captures tool inputs
   - `log_tool_result()` - Captures tool outputs
   - `log_model_metrics()` - Captures usage metrics

2. **`orchestrator.py`** - Enhanced `stream_to_dashboard()`:
   - Now accepts `logger` parameter
   - Logs to both dashboard AND conversation logger
   - Captures all SDK message types with full details

## Usage Examples

### View a Session Log
```bash
# Pretty print with jq
cat .logs/conversations/session_abc12345_*.jsonl | jq .

# Filter by event type
cat .logs/conversations/session_*.jsonl | jq 'select(.event == "model_prompt")'

# Extract all model thinking
cat .logs/conversations/session_*.jsonl | jq -r 'select(.event == "model_thinking") | .thinking'

# Get tool call statistics
cat .logs/conversations/session_*.jsonl | jq 'select(.event == "tool_call") | .tool_name' | sort | uniq -c
```

### Programmatic Access
```python
from conversation_logger import ConversationLogger

# Load full session
events = ConversationLogger.load_session("abc12345")

# Filter by event type
prompts = [e for e in events if e['event'] == 'model_prompt']
tool_calls = [e for e in events if e['event'] == 'tool_call']

# Get recent sessions
sessions = ConversationLogger.get_recent_sessions(limit=10)
```

## Analysis Use Cases

### 1. **Debugging Failed Sessions**
- See exact prompt sent to model
- Trace tool call sequence
- Identify where errors occurred
- Review model's reasoning process

### 2. **Quality Improvement**
- Analyze which prompts lead to better results
- Identify common failure patterns
- Measure tool usage efficiency
- Track cost per session type

### 3. **Performance Optimization**
- Identify slow tool calls
- Measure model latency
- Track token usage patterns
- Optimize prompt lengths

### 4. **User Experience**
- Understand user intent patterns
- Identify confusing queries
- Improve agent coordination
- Reduce retry rates

## API Endpoints (Already Implemented)

### List Recent Sessions
```bash
GET /api/sessions
```

### Get Session Details
```bash
GET /api/sessions/:sessionId
```

## Next Steps

### Frontend (Pending)
- [ ] Session Logs Viewer UI component
- [ ] Timeline visualization of agent interactions
- [ ] Diff view for prompt iterations
- [ ] Cost/performance dashboard

### Analytics (Future)
- [ ] Automated quality scoring
- [ ] Prompt optimization suggestions
- [ ] Anomaly detection
- [ ] Cost alerts and budgets

### Advanced Features (Future)
- [ ] Session replay capability
- [ ] A/B testing infrastructure
- [ ] Automated regression testing
- [ ] Export to external analytics tools

## Benefits

✅ **Complete Observability**: Every model interaction is logged  
✅ **Zero Redundancy**: Reuses existing event streaming  
✅ **Easy Debugging**: Trace full execution path  
✅ **Quality Analysis**: Analyze patterns and improve prompts  
✅ **Cost Tracking**: Monitor spending per session  
✅ **Privacy-Focused**: Logs stay local (not committed to git)  

## Privacy & Security

- Logs are stored in `.logs/` (gitignored by default)
- Contains full prompts and model outputs (may include sensitive data)
- Should be excluded from version control
- Consider encryption for production deployments
- Implement log rotation for disk space management

## Log Retention

Current implementation:
- No automatic cleanup
- Logs persist indefinitely

Recommended for production:
- Implement log rotation (e.g., keep last 30 days)
- Archive old logs to cloud storage
- Compress logs older than 7 days
- Set disk space alerts
