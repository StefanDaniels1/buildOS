# Enhanced Logging - Quick Start Guide

## What Changed?

Your buildOS orchestrator now captures **everything** that happens during agent interactions:
- ✅ Full prompts sent to models
- ✅ Complete model thinking/reasoning
- ✅ All tool calls with inputs
- ✅ All tool results with outputs
- ✅ Cost and performance metrics

## How to Use

### 1. Use the System Normally
Just use your dashboard and chat with the orchestrator. Everything is automatically logged to:
```
.logs/conversations/session_{id}_{timestamp}.jsonl
```

### 2. View Your Sessions
```bash
python analyze_logs.py --list
```

Output:
```
================================================================================
Found 1 session(s)
================================================================================

1. Session: session_17643199
   File: session_session__20251128_095301.jsonl
   Start: 2025-11-28T09:53:01.967360
   Status: completed
   Query: how many wooden elements are there in the browser?...
   Events: 7
```

### 3. Analyze a Session
```bash
python analyze_logs.py --analyze 0
```

See detailed breakdown:
- Event counts
- User query
- Model prompts
- Tool calls
- Agent spawns
- Cost metrics
- Errors (if any)

### 4. Deep Dive

**See model thinking:**
```bash
python analyze_logs.py --thinking 0
```

**See tool usage:**
```bash
python analyze_logs.py --tools 0
```

**Compare all sessions:**
```bash
python analyze_logs.py --compare
```

## What Gets Logged?

### Every Session Logs:

1. **User Input** - Your query and context
2. **Model Prompts** - The FULL prompt sent to Claude
3. **Model Thinking** - Every reasoning step
4. **Tool Calls** - Complete tool inputs
5. **Tool Results** - Full outputs
6. **Agent Spawns** - Subagent creation
7. **Metrics** - Cost, duration, turns
8. **Errors** - Full traceback if something fails

### Example Log Entry (Model Thinking):
```json
{
  "event": "model_thinking",
  "timestamp": "2025-11-28T09:53:05.123456",
  "thinking": "I need to classify this query as a Simple Query pattern. The user is asking 'how many wooden elements' which matches the pattern 'How many [element type]'. I'll spawn a single explore agent to answer this quickly.",
  "agent_id": "orchestrator"
}
```

### Example Log Entry (Tool Call):
```json
{
  "event": "tool_call",
  "timestamp": "2025-11-28T09:53:06.789012",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "explore",
    "description": "Count wooden elements in the IFC model",
    "model": "haiku"
  },
  "agent_id": "orchestrator"
}
```

## Why This Matters

### For Debugging 🐛
When something goes wrong, you can:
1. See the exact prompt sent to the model
2. Read the model's reasoning
3. Trace the tool call sequence
4. Identify where it failed

### For Improvement 📈
Over time, you can:
1. Compare successful vs failed sessions
2. Identify patterns in user queries
3. Optimize prompts for better results
4. Reduce costs by analyzing tool usage

### For Understanding 🧠
You get complete visibility into:
1. How the orchestrator makes decisions
2. Which agents are spawned and why
3. What tools are used and when
4. How much each session costs

## Quick Commands Cheat Sheet

```bash
# List all sessions
python analyze_logs.py --list

# Analyze session 0
python analyze_logs.py --analyze 0

# Show model thinking
python analyze_logs.py --thinking 0

# Show tool calls
python analyze_logs.py --tools 0

# Compare sessions
python analyze_logs.py --compare

# View raw log (requires jq)
cat .logs/conversations/session_*.jsonl | jq .

# Extract all prompts
jq 'select(.event == "model_prompt")' .logs/conversations/*.jsonl

# Find errors
jq 'select(.event == "error")' .logs/conversations/*.jsonl
```

## No Configuration Needed! ✨

The enhanced logging is **automatic**:
- Logs are created when you use the system
- No setup required
- No performance impact
- Works with existing dashboard

## Where to Learn More

- **LOGGING_ARCHITECTURE.md** - Complete technical overview
- **LOG_ANALYSIS_GUIDE.md** - Advanced analysis techniques
- **ENHANCED_LOGGING_SUMMARY.md** - Implementation details

## Next Time You Run a Query...

1. Use the dashboard normally
2. After the session completes, run:
   ```bash
   python analyze_logs.py --list
   python analyze_logs.py --analyze 0
   ```
3. See everything that happened!

That's it! 🎉

Your orchestrator now has **complete observability** without any extra work on your part.
