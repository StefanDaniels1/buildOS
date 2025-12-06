# Session Log Analysis - Quick Reference

## View Logs with Built-in Analyzer

### List all sessions
```bash
python analyze_logs.py --list
```

### Analyze specific session
```bash
python analyze_logs.py --analyze 0  # Analyze first session
```

### Show model thinking/reasoning
```bash
python analyze_logs.py --thinking 0
```

### Show tool usage details
```bash
python analyze_logs.py --tools 0
```

### Compare all sessions
```bash
python analyze_logs.py --compare
```

## Manual Analysis with jq

### View entire session (pretty)
```bash
cat .logs/conversations/session_*.jsonl | jq .
```

### Extract all user queries
```bash
jq -r 'select(.event == "user_message") | .message' .logs/conversations/session_*.jsonl
```

### View all model prompts
```bash
jq 'select(.event == "model_prompt")' .logs/conversations/session_*.jsonl
```

### Extract model thinking
```bash
jq -r 'select(.event == "model_thinking") | .thinking' .logs/conversations/session_*.jsonl
```

### View tool calls with inputs
```bash
jq 'select(.event == "tool_call") | {tool: .tool_name, input: .tool_input}' .logs/conversations/session_*.jsonl
```

### View tool results
```bash
jq 'select(.event == "tool_result") | {success: .success, output: .tool_output}' .logs/conversations/session_*.jsonl
```

### Get cost summary
```bash
jq -s 'map(select(.event == "model_metrics")) | map(.cost_usd // 0) | add' .logs/conversations/session_*.jsonl
```

### Count events by type
```bash
jq -r '.event' .logs/conversations/session_*.jsonl | sort | uniq -c
```

### Find errors
```bash
jq 'select(.event == "error")' .logs/conversations/session_*.jsonl
```

### Get session duration
```bash
# First and last timestamp
jq -s '[.[0].timestamp, .[-1].timestamp]' .logs/conversations/session_*.jsonl
```

## Programmatic Access (Python)

```python
from conversation_logger import ConversationLogger

# Load a specific session
events = ConversationLogger.load_session("abc12345")

# Get recent sessions
sessions = ConversationLogger.get_recent_sessions(limit=10)

# Filter events
prompts = [e for e in events if e['event'] == 'model_prompt']
tools = [e for e in events if e['event'] == 'tool_call']
thinking = [e for e in events if e['event'] == 'model_thinking']

# Calculate metrics
total_cost = sum(
    e.get('cost_usd', 0) or 0 
    for e in events 
    if e['event'] == 'model_metrics'
)

# Get full conversation flow
for event in events:
    print(f"{event['timestamp']} - {event['event']}")
```

## What Gets Logged

✅ **User Input**
- Query text
- File paths
- Session context

✅ **Model Prompts** (FULL TEXT)
- System prompts
- Agent instructions
- Context provided to model

✅ **Model Thinking** (FULL TEXT)
- Reasoning steps
- Decision making
- Internal monologue

✅ **Tool Calls** (FULL INPUT)
- Tool name
- Complete input parameters
- Agent ID

✅ **Tool Results** (FULL OUTPUT)
- Success/failure status
- Complete output
- Error messages

✅ **Agent Spawns**
- Agent type
- Agent ID
- Spawn prompt

✅ **Metrics**
- Cost (USD)
- Duration (ms)
- Number of turns

✅ **Errors**
- Error type
- Error message
- Full traceback

## Common Analysis Patterns

### Debug a failed session
```bash
# 1. Find the session
python analyze_logs.py --list

# 2. Analyze it
python analyze_logs.py --analyze 0

# 3. Look for errors
jq 'select(.event == "error")' .logs/conversations/session_abc12345_*.jsonl

# 4. Trace tool calls
python analyze_logs.py --tools 0
```

### Optimize prompts
```bash
# Extract all prompts
jq -r 'select(.event == "model_prompt") | .content' .logs/conversations/session_*.jsonl > all_prompts.txt

# Compare successful vs failed sessions
# (manually review thinking patterns)
```

### Track costs
```bash
# Cost per session
for file in .logs/conversations/session_*.jsonl; do
    echo "$file: $(jq -s 'map(select(.event == "model_metrics")) | map(.cost_usd // 0) | add' $file)"
done
```

### Find patterns
```bash
# Most common queries
jq -r 'select(.event == "user_message") | .message' .logs/conversations/session_*.jsonl | sort | uniq -c | sort -rn

# Most used tools
jq -r 'select(.event == "tool_call") | .tool_name' .logs/conversations/session_*.jsonl | sort | uniq -c | sort -rn

# Average session duration
# (calculate from first/last timestamp)
```
