# Quick Start Guide

## 1. Setup (2 minutes)

```bash
# Make sure you have uv installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set your API key
export ANTHROPIC_API_KEY='sk-ant-...'
```

## 2. Run Your First Analysis (3 minutes)

```bash
# Analyze the included IFC file
uv run python run.py Small_condo.ifc
```

You'll see:
- Parsing progress
- Tool usage in real-time
- Classification results
- Cost and timing

## 3. Check Results

```bash
ls workspace/

# You should see:
# - Small_condo_parsed.json        (all building elements)
# - Small_condo_batches.json       (classification batches)
# - batch_1_classifications.json   (first batch results)
```

## 4. Explore Interactively

```bash
uv run python run.py

👤 You: Parse Small_condo.ifc and tell me how many walls there are
🤖 Claude: [parses file, counts walls, responds]

👤 You: Show me the first 5 concrete elements
🤖 Claude: [reads parsed data, shows elements]

👤 You: Classify them using the co2-classifier agent
🤖 Claude: [prepares batch, spawns agent, returns classifications]
```

## Understanding the Flow

### What Happens When You Run `run.py Small_condo.ifc`

1. **Claude receives goal**: "Analyze Small_condo.ifc for CO2"

2. **Claude decides**: "I need to parse it first"
   - Uses `parse_ifc_file` tool
   - Gets JSON response with file path and stats

3. **Claude decides**: "Now filter geometric elements"
   - Uses `get_geometric_elements` tool
   - Gets JSON with element counts by type

4. **Claude decides**: "Prepare batches for classification"
   - Uses `prepare_classification_batches` tool
   - Gets JSON with batch configuration

5. **Claude decides**: "Classify first batch"
   - Uses `classify_elements` tool
   - Tool returns: "Use co2-classifier agent"
   - Claude spawns agent via Task tool

6. **co2-classifier agent**:
   - Reads batch elements
   - Analyzes materials, properties, spatial context
   - Classifies each element
   - Writes results to JSON
   - Returns to main Claude

7. **Claude reports**: Summary of what was done

All outputs saved to `workspace/` for inspection.

## Key Files to Understand

### `run.py` - The Orchestrator
- Lines 40-90: Sets up tools and agent
- Lines 92-120: The goal prompt (this drives everything)
- Lines 122-145: Response handling

**Key insight**: We give Claude a GOAL, not step-by-step commands.

### `tools/ifc_analysis_tool.py` - The Tools
- Lines 19-133: `parse_ifc_file` - Extract IFC data
- Lines 135-196: `get_geometric_elements` - Filter elements
- Lines 217-338: `prepare_classification_batches` - Group into batches
- Lines 350-446: `classify_elements` - Bridge to agent
- Lines 449-552: `aggregate_classifications` - Combine results

**Key insight**: All tools return JSON strings, not pretty text.

### `.claude/agents/co2-classifier.md` - The Expert
- Lines 1-5: Agent metadata (name, tools)
- Lines 18-46: Classification categories
- Lines 48-82: Analysis process
- Lines 96-105: Response format

**Key insight**: Agent has domain expertise, main Claude has orchestration logic.

## Common Tasks

### Process All Batches
```bash
uv run python run.py

👤 You: Analyze Small_condo.ifc and classify ALL batches (not just first)
🤖 Claude: [processes all batches in sequence]
```

### Custom Batch Size
```bash
👤 You: Parse Small_condo.ifc, prepare batches of 25 elements
🤖 Claude: [uses prepare_batches with batch_size=25]
```

### Aggregate Results
```bash
👤 You: Aggregate all batch_*_classifications.json files in workspace/
🤖 Claude: [uses aggregate_classifications tool]
```

### Investigate Specific Elements
```bash
👤 You: Show me all IfcWall elements with concrete material
🤖 Claude: [reads parsed JSON, filters, displays]
```

## Debugging

### Tool Returns Error
Check the JSON output - it includes `"is_error": true` and error message.

### Agent Not Spawning
Make sure your prompt includes something like:
- "Use the co2-classifier agent"
- "Spawn co2-classifier"
- Or let classify_elements tool suggest it

### Cost Concerns
Each tool call costs tokens. For large files:
- Parse once, reuse the JSON
- Process batches incrementally
- Use smaller batch sizes for testing

### Classification Quality
Check the `confidence` scores in results. Low confidence = needs manual review.

## Next Steps

1. **Understand the code**:
   - Read `run.py` - see how tools are registered
   - Read `tools/ifc_analysis_tool.py` - see JSON response pattern
   - Read `.claude/agents/co2-classifier.md` - see agent expertise

2. **Experiment**:
   - Try different IFC files
   - Modify batch sizes
   - Ask Claude exploratory questions

3. **Extend**:
   - Add a `calculate_co2` tool (see REFACTOR_SUMMARY.md)
   - Create a `volume-estimator` agent
   - Build a report generator

4. **Deploy**:
   - Wrap in FastAPI for web service
   - Add batch processing queue
   - Connect to NIBE database for CO2 factors

## Getting Help

- Check `README.md` for architecture overview
- Check `REFACTOR_SUMMARY.md` for detailed changes
- Check `.claude/agents/co2-classifier.md` for classification logic

## Testing the System

```bash
# Quick smoke test
uv run python run.py Small_condo.ifc

# Expected output:
# ✅ Parsing complete
# ✅ Batch preparation complete
# ✅ Classification complete (first batch)
# ✅ Files in workspace/

# Check classification quality
cat workspace/batch_1_classifications.json | grep -A 3 "classification"
```

## Tips

1. **Claude remembers context** in interactive mode - use this!
2. **Tools return JSON** - Claude can parse and use the data
3. **Agent is specialized** - use it for classification, not parsing
4. **Batch processing is parallelizable** - future optimization
5. **All outputs are in workspace/** - easy to inspect/debug

---

Ready to build? Start with `uv run python run.py Small_condo.ifc` 🚀
