# agent_system5: SDK-First buildOS Orchestrator

Clean, simple orchestrator for buildOS IFC CO2 analysis using Claude Agent SDK.

## Architecture

**Core Principle**: ClaudeSDKClient IS the orchestrator. We register tools, define agents, and let the SDK handle routing, spawning, context management, and coordination.

### Key Stats
- **86% code reduction** from agent_system4 (2,871 LOC → ~400 LOC)
- **Single entry point**: orchestrator.py
- **Zero custom orchestration logic**: SDK handles everything

## Directory Structure

```
agent_system5/
├── orchestrator.py              # Main entry (~300 LOC)
├── sdk_tools.py                 # MCP tool registration (~200 LOC)
├── conversation_logger.py       # Session logging (reused)
├── requirements.txt             # Python dependencies
├── .claude/
│   ├── agents/                  # SDK auto-discovers
│   │   ├── data-prep.md         # Parse IFC + create batches
│   │   ├── batch-processor.md   # Classify elements
│   │   ├── durability-calculator.md  # Calculate CO2
│   │   └── pdf-report-generator.md   # Generate reports
│   ├── tools/                   # Helper utilities
│   │   ├── analyze_batch.py     # Element classification
│   │   ├── generate_co2_pdf.py  # PDF generation
│   │   ├── ifc_direct_tools.py  # IFC utilities
│   │   └── durability_database.json  # CO2 factors
│   ├── hooks/
│   │   └── send_event.py        # Dashboard event sender
│   └── settings.json            # Hook configuration
└── workspace/                   # Execution workspace
    ├── .context/                # Session-specific data
    └── uploads/                 # User-uploaded files
```

## How It Works

### 1. ClaudeSDKClient as Orchestrator

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query(f"""
    You are the buildOS orchestrator.

    User request: "{message}"
    IFC file: {file_path}

    Classify intent and coordinate agents:
    - Simple query → spawn data-prep agent
    - Full analysis → 4-phase workflow with parallel execution

    Validate completeness after each phase.
    """)

    await stream_to_dashboard(client, session_id, dashboard_url)
```

**What SDK Handles**:
- Agent spawning via `Task` tool
- Context preservation across turns
- Tool routing based on `allowed_tools`
- Error handling and recovery
- Streaming responses

### 2. Agent Discovery

Agents defined in `.claude/agents/*.md` are auto-discovered:

```python
ClaudeAgentOptions(
    setting_sources=["project"]  # Auto-loads .claude/agents/*.md
)
```

SDK spawns agents when it decides to use the `Task` tool:

```python
Task(
    subagent_type="data-prep",
    description="Parse IFC and create batches",
    model="haiku"
)
```

### 3. Tool Registration (MCP Server)

```python
# sdk_tools.py
@tool("parse_ifc_file", "Parse IFC file", {...})
async def parse_ifc_file(args: Dict[str, Any]) -> Dict[str, Any]:
    import ifcopenshell
    ifc_file = ifcopenshell.open(args["ifc_path"])
    # Extract elements...
    return {"content": [{"type": "text", "text": json.dumps(result)}]}

def create_ifc_tools_server():
    return create_sdk_mcp_server(
        name="ifc",
        tools=[parse_ifc_file, prepare_batches, calculate_co2]
    )

# In orchestrator.py
options = ClaudeAgentOptions(
    mcp_servers={"ifc": create_ifc_tools_server()},
    allowed_tools=["Task", "Read", "Write", "mcp__ifc__*"]
)
```

Tools become available as:
- `mcp__ifc__parse_ifc_file`
- `mcp__ifc__prepare_batches`
- `mcp__ifc__calculate_co2`

### 4. Event Streaming (Two Levels)

**Level 1: SDK Events** (orchestrator → dashboard)
```python
async def stream_to_dashboard(client, session_id, dashboard_url):
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    await send_event("AgentThinking", {"thought": block.text})
                elif isinstance(block, ToolUseBlock):
                    if block.name == "Task":
                        await send_event("SubagentStart", {...})
```

**Level 2: Hook Events** (from .claude/hooks/send_event.py)
- PreToolUse, PostToolUse
- Sent automatically by Claude Code
- Provides tool-level observability

### 5. Validation Loop

Implemented as orchestrator prompt logic:

```
After each agent completes:
1. Review output files in workspace/.context/
2. Check completeness:
   - data-prep: batches.json exists with all elements?
   - batch-processor: ALL elements classified?
   - calculator: ALL elements have CO2 values?
3. If incomplete: Re-spawn agent with specific feedback (max 2 retries)
4. If complete: Proceed to next phase
```

SDK preserves full conversation history, enabling rich feedback.

## Usage

### Installation

```bash
cd agent_system5
pip install -r requirements.txt
```

### Running the Orchestrator

```bash
python orchestrator.py \
  --message "Calculate CO2 for this building" \
  --session-id "session-123" \
  --file-path "/path/to/model.ifc" \
  --dashboard-url "http://localhost:4000"
```

### Environment Variables

```bash
export ANTHROPIC_API_KEY="your-api-key"
export BUILDOS_SESSION_ID="session-123"  # For hooks
export DASHBOARD_URL="http://localhost:4000"
```

## Workflow Example

### Full CO2 Analysis

**User Request**: "Calculate CO2 for this building"

**Orchestrator Flow**:
```
1. Intent Classification → Full CO2 Analysis
2. Spawn data-prep agent (Haiku)
   → Use mcp__ifc__parse_ifc_file
   → Create batches.json
3. Validate: All elements present?
4. Spawn batch-processor agents × N (parallel, Haiku)
   → Classify each batch
   → Return classifications
5. Validate: ALL elements classified?
6. Spawn durability-calculator agents × N (parallel, Haiku)
   → Calculate CO2 per batch
   → Return results
7. Validate: ALL elements have CO2?
8. Spawn pdf-report-generator agent (Sonnet)
   → Generate final PDF
   → Return report path
9. Return to user: "CO2 analysis complete: workspace/report_session-123.pdf"
```

### Event Timeline

```
SessionStart
  → AgentThinking: "Initializing buildOS orchestrator"
  → AgentThinking: "SDK initialized, analyzing user request"
  → SubagentStart: data-prep
    → ToolStart: mcp__ifc__parse_ifc_file
    → ToolStop: success
  → SubagentStop: data-prep
  → AgentThinking: "Validation: 450 elements found, creating batches"
  → SubagentStart: batch-processor (batch 1)
  → SubagentStart: batch-processor (batch 2)
  → ... (parallel execution)
  → SubagentStop: batch-processor (batch 1)
  → ...
  → AgentThinking: "Validation: All elements classified"
  → SubagentStart: durability-calculator (batch 1)
  → ...
  → AgentThinking: "Validation: CO2 calculated for all elements"
  → SubagentStart: pdf-report-generator
  → SubagentStop: pdf-report-generator
  → AgentMetrics: cost_usd, duration_ms, num_turns
SessionEnd
```

## Comparison with agent_system4

| Aspect | agent_system4 | agent_system5 | Change |
|--------|---------------|---------------|--------|
| Entry points | 7 files | 1 file | -86% |
| Total LOC | 2,871 | ~400 | -86% |
| Orchestration logic | 500+ LOC custom | 0 LOC (SDK) | -100% |
| Agent routing | 300+ LOC custom | 0 LOC (SDK) | -100% |
| Context management | 200+ LOC custom | 0 LOC (SDK) | -100% |

**Preserved Features**:
- ✅ Multi-agent orchestration (via SDK Task tool)
- ✅ Real-time event streaming (hooks + SDK events)
- ✅ Validation loop (orchestrator validation logic)
- ✅ Conversation logging (reuse conversation_logger.py)
- ✅ Dashboard integration (Vue.js UI)

## Testing

### Test Single Agent Spawn

```bash
python orchestrator.py \
  --message "How many structural elements are in this model?" \
  --session-id "test-1" \
  --file-path "tests/fixtures/small_condo.ifc"
```

Expected: data-prep agent spawns, parses IFC, returns element count.

### Test Full Workflow

```bash
python orchestrator.py \
  --message "Calculate CO2 impact" \
  --session-id "test-2" \
  --file-path "tests/fixtures/small_condo.ifc"
```

Expected: 4-phase workflow completes, PDF report generated.

### Test Validation Loop

Modify `workspace/.context/test-3/batches.json` to have incomplete data, re-run orchestrator.

Expected: Orchestrator detects incompleteness, re-spawns agent.

## Next Steps

- [ ] Phase 2: Full multi-agent workflow testing
- [ ] Phase 3: Dashboard integration (update orchestrator.ts path)
- [ ] Phase 4: Comprehensive test suite
- [ ] Production deployment: Container setup

## Resources

- **Claude Agent SDK Docs**: `docs/claude-agent-sdk/`
- **Plan**: `.claude/plans/lovely-dazzling-quill.md`
- **Dashboard**: `claude-code-hooks-multi-agent-observability/`

---

**Built with**: Claude Agent SDK | Python 3.10+ | ifcopenshell | httpx
