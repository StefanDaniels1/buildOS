# Agent Orchestration Architecture

## Current Problems

1. **Context Loss During Subagent Handoff**
   - Subagents run in parallel but orchestrator doesn't wait for completion
   - Orchestrator continues processing with incomplete/stale data
   - No reliable mechanism to collect and aggregate subagent outputs

2. **File-Based Coordination Is Fragile**
   - Inconsistent field names between stages (`guid` vs `global_id`)
   - Path resolution issues across Docker/local environments
   - No validation that files were actually created by subagents

3. **Large Context Gets Truncated**
   - 152 elements × detailed classification = context overflow
   - Orchestrator loses track of what was already processed
   - Makes up data or uses partial information

## Proposed Architecture: State Machine with Explicit Checkpoints

### Design Principles

1. **Explicit State Persistence**: Every stage writes a state file that the next stage reads
2. **Sequential Processing with Parallel Batching**: Don't spawn all subagents at once
3. **Schema Validation**: Every JSON output is validated against a schema
4. **Progress Tracking**: Clear checkpoint files showing what's completed
5. **Reduced Context Window**: Use file references, not inline data

### New Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                             │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  PARSE   │───>│  BATCH   │───>│ CLASSIFY │───>│ GENERATE │  │
│  │  STAGE   │    │  STAGE   │    │  STAGE   │    │  STAGE   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │               │               │               │         │
│       ▼               ▼               ▼               ▼         │
│  parsed.json    batches.json    classified/      report.xlsx   │
│  + schema       + schema        batch_*.json      + PDF        │
│                                 + progress.json                 │
└─────────────────────────────────────────────────────────────────┘
```

### Stage 1: Parse (MCP Tool)

**Input**: IFC file path
**Output**: `parsed_data.json` with schema validation
**State File**: `stage_1_complete.json`

```json
{
  "stage": "parse",
  "status": "complete",
  "timestamp": "...",
  "output_file": "parsed_data.json",
  "element_count": 152,
  "checksums": {
    "input": "sha256:abc...",
    "output": "sha256:def..."
  }
}
```

### Stage 2: Batch (MCP Tool)

**Input**: `parsed_data.json`
**Output**: Individual batch files `batch_1.json`, `batch_2.json`, etc.
**State File**: `stage_2_complete.json`

Key change: Create individual batch files, not one big batches.json

### Stage 3: Classify (Sequential Subagent Calls)

**CRITICAL CHANGE**: Process batches SEQUENTIALLY, not in parallel!

```python
for batch_num in range(1, total_batches + 1):
    # 1. Call subagent for ONE batch
    await spawn_subagent("batch-processor", batch_num)
    
    # 2. WAIT for completion by checking for output file
    await wait_for_file(f"batch_{batch_num}_classified.json", timeout=60)
    
    # 3. Validate output schema
    validate_classification_schema(f"batch_{batch_num}_classified.json")
    
    # 4. Update progress
    update_progress(batch_num, total_batches)
```

**Progress File**: `classification_progress.json`
```json
{
  "stage": "classify",
  "total_batches": 4,
  "completed_batches": [1, 2, 3],
  "current_batch": 4,
  "status": "in_progress"
}
```

### Stage 4: Aggregate + Generate (MCP Tool)

**Input**: All `batch_*_classified.json` files
**Output**: Merged `classified_all.json` + Excel report
**State File**: `stage_4_complete.json`

Only starts when `classification_progress.json` shows all batches complete!

## Implementation Changes

### 1. New MCP Tools

```python
@tool(name="check_stage_completion")
async def check_stage_completion(args):
    """Check if a workflow stage is complete by reading state file."""
    stage_file = f"stage_{args['stage_num']}_complete.json"
    if os.path.exists(stage_file):
        with open(stage_file) as f:
            state = json.load(f)
        return {"complete": True, "state": state}
    return {"complete": False}

@tool(name="wait_for_subagent")
async def wait_for_subagent(args):
    """Wait for a subagent to complete by polling for output file."""
    output_file = args['output_file']
    timeout = args.get('timeout', 120)
    poll_interval = 5
    
    for _ in range(timeout // poll_interval):
        if os.path.exists(output_file):
            # Validate file is complete (not still being written)
            await asyncio.sleep(1)
            with open(output_file) as f:
                data = json.load(f)
            return {"success": True, "data": data}
        await asyncio.sleep(poll_interval)
    
    return {"success": False, "error": "Timeout waiting for subagent"}

@tool(name="aggregate_batch_results")
async def aggregate_batch_results(args):
    """Combine all batch classification files into one."""
    batch_dir = args['batch_dir']
    output_file = args['output_file']
    
    all_elements = []
    for batch_file in sorted(glob.glob(f"{batch_dir}/batch_*_classified.json")):
        with open(batch_file) as f:
            batch_data = json.load(f)
        all_elements.extend(batch_data)
    
    # Validate all elements have required fields
    for elem in all_elements:
        assert 'global_id' in elem, f"Missing global_id in element"
        assert 'ifc_type' in elem
        assert 'material_primary' in elem
    
    with open(output_file, 'w') as f:
        json.dump({"elements": all_elements, "count": len(all_elements)}, f)
    
    return {"success": True, "element_count": len(all_elements)}
```

### 2. Modified Orchestrator Prompt

```markdown
## CRITICAL WORKFLOW RULES

1. **NEVER spawn multiple subagents at once** - process batches sequentially
2. **ALWAYS wait for each batch to complete** before starting the next
3. **ALWAYS verify output files exist** before proceeding to next stage
4. **ALWAYS use aggregate_batch_results** before generating reports
5. **NEVER generate reports from memory** - always read from aggregated file

## Workflow Checkpoints

Before each stage, check the previous stage is complete:
- Before batching: verify `stage_1_complete.json` exists
- Before classifying: verify `stage_2_complete.json` exists  
- Before generating: verify ALL `batch_*_classified.json` files exist
```

### 3. Subagent Output Validation

The batch-processor agent must:
1. Write to the EXACT output path specified
2. Use the EXACT field names (global_id, not guid)
3. Write a completion marker when done

```markdown
# batch-processor.md

## OUTPUT REQUIREMENTS

1. Write output to EXACTLY: `{session_context}/batch_{batch_num}_classified.json`
2. Use this EXACT schema:
   ```json
   [
     {
       "global_id": "...",  // NOT "guid"!
       "ifc_type": "...",
       "name": "...",
       "element_type": "...",
       "material_primary": {...},
       "volume_m3": 0.0,
       "confidence": 0.0
     }
   ]
   ```
3. After writing, create marker: `{session_context}/batch_{batch_num}_complete.txt`
```

### 4. Context Window Management

For large models, DON'T send all elements to the orchestrator:

```python
# Instead of returning full data:
return {"elements": [...152 elements...]}  # BAD - uses context

# Return summary + file reference:
return {
    "success": True,
    "element_count": 152,
    "output_file": "/path/to/parsed_data.json",
    "summary": {
        "by_type": {"IfcWall": 10, "IfcColumn": 20, ...}
    }
}
```

## Summary of Changes

| Area | Before | After |
|------|--------|-------|
| Subagent spawning | Parallel (all at once) | Sequential (one at a time) |
| Data handoff | In-memory context | File-based with validation |
| Field names | Inconsistent | Strict schema |
| Progress tracking | None | Explicit progress.json |
| Error handling | Silent failures | Checkpoint verification |
| Report generation | From partial memory | From aggregated file |

## Next Steps

1. [ ] Implement new MCP tools (`wait_for_subagent`, `aggregate_batch_results`)
2. [ ] Update `batch-processor.md` agent with strict output requirements
3. [ ] Update orchestrator prompt with workflow rules
4. [ ] Add schema validation to all JSON outputs
5. [ ] Test with small model (< 50 elements) first
6. [ ] Test with medium model (50-200 elements)
7. [ ] Test with large model (200+ elements)
