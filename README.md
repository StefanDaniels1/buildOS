# BIM AI CO2 Analysis

Automated environmental impact analysis for BIM models using AI agents.

Transform 3-day sustainability reports into 10-minute analyses.

## What This Does

1. **Parses IFC files** - Extracts building elements with materials, properties, and quantities
2. **Classifies elements** - Uses AI to analyze ALL element types (concrete, steel, timber, etc.)
3. **Extracts comprehensive data** - Material composition, volumes (m³), areas (m²), properties
4. **Generates structured datasets** - Rich JSON for downstream sustainability analysis (CO2, circularity, EPD lookup)

## Quick Start

### 1. Install

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY='your-key-here'
```

### 3. Run Analysis

```bash
# Analyze an IFC file
uv run python run.py Small_condo.ifc

# Or interactive mode
uv run python run.py
```

## Architecture

```
User Request
    ↓
Main Claude Session (orchestrator)
    ↓
├── Tool: parse_ifc_file          → Extracts building data
├── Tool: prepare_batches         → Creates classification batches
│
└── For each batch:
    └── Agent: element-classifier → AI element analysis (spawned via Task)
        ├── Reads batch elements from session context
        ├── Analyzes materials, properties, spatial context
        ├── Extracts: element type, function, materials (primary+secondary),
        │   volumes (m³), areas (m²), dimensions, properties
        ├── Writes comprehensive element data to JSON
        └── Returns structured dataset
    ↓
[Next phase: Sustainability agent maps to EPD/CO2 databases]
```

## Project Structure

```
agent_system4/
├── run.py                        # Main entry point & orchestrator
├── ifc_comprehensive_parser.py   # IFC parsing logic
├── tools/
│   └── ifc_analysis_tool.py     # Custom MCP tools for Claude
├── .claude/
│   └── agents/
│       ├── element-classifier.md # Comprehensive element classification agent
│       └── co2-classifier.md    # (deprecated - use element-classifier)
└── workspace/                    # Output directory
    ├── .context/                # Session context (intermediate data)
    │   └── [filename]_[timestamp]/
    │       ├── parsed_data.json  # Parsed IFC data
    │       └── batches.json      # Element batches
    └── batch_1_elements.json    # Final: Classified element data
```

## Output Format

The element-classifier agent produces comprehensive JSON data for each building element:

```json
{
  "global_id": "2O2Fr$t4X7Zf8NOew3FNr2",
  "ifc_type": "IfcColumn",
  "name": "Kolom K1 - 400mm",
  "element_type": "column",

  "function": "structural",
  "structural_role": "vertical_load_bearing",
  "location": "above_ground",

  "material_primary": {
    "name": "Concrete C30/37",
    "category": "concrete",
    "subcategory": "C30/37",
    "percentage": 98
  },
  "material_secondary": [
    {"name": "Reinforcement steel", "category": "steel", "percentage": 2}
  ],

  "volume_m3": 0.38,
  "area_m2": 3.77,
  "dimensions": {"diameter_mm": 400, "height_m": 3.0},

  "properties": {"LoadBearing": true, "FireRating": "REI 120"},
  "spatial_context": {"building": "Office A", "storey": "Ground Floor"},

  "confidence": 0.90,
  "data_quality": {
    "material_source": "ifc_properties",
    "quantity_source": "ifc_quantities",
    "missing_data": [],
    "assumptions": ["2% reinforcement typical for columns"]
  },
  "reasoning": "Load-bearing column identified from LoadBearing=true..."
}
```

**Key features:**
- Works for ALL element types (not just concrete)
- Primary + secondary material composition
- Both volume (m³) AND area (m²)
- Dimensional data preserved
- Properties and spatial context
- Data quality tracking and reasoning

See `CLASSIFICATION_SCHEMA.md` for complete documentation.

## How It Works

### Tools (Python functions callable by Claude)

1. **parse_ifc_file** - Wraps ifcopenshell, extracts all building data
2. **get_geometric_elements** - Filters elements suitable for CO2 analysis
3. **prepare_classification_batches** - Groups elements into batches (50 per batch)
4. **classify_elements** - Prepares a batch for classification by the agent
5. **aggregate_classifications** - Combines batch results into final report

### Agent (Specialized AI expert)

**element-classifier** - Comprehensive building element analysis
- Reads batch elements from session context
- Analyzes: materials, IFC types, properties, spatial context
- Extracts structured data for ALL element types (concrete, steel, timber, etc.)
- Outputs: element type, function, material composition, volumes, areas, properties
- Writes rich JSON with confidence scores, data quality assessment, and reasoning

### Key Design Principles

1. **Claude drives the workflow** - We give goals, not step-by-step commands
2. **Tools return structured JSON** - Machine-parseable, not pretty text
3. **Agent spawning via Task tool** - element-classifier is invoked when needed
4. **Session-based context** - Intermediate data in `.context/`, final outputs in workspace root
5. **Separation of concerns** - Classification extracts data, sustainability agents calculate impact
6. **Comprehensive data extraction** - Rich datasets enable multiple downstream analyses

## Example Usage

### Automated Analysis

```bash
uv run python run.py model.ifc
```

Claude will autonomously:
1. Parse the IFC file → `.context/[filename]_[timestamp]/parsed_data.json`
2. Prepare element batches → `.context/[filename]_[timestamp]/batches.json`
3. Classify first batch using element-classifier agent → `batch_1_elements.json`
4. Report summary statistics

### Interactive Mode

```bash
uv run python run.py
```

Then chat with Claude:
```
👤 You: Parse Small_condo.ifc
🤖 Claude: [parses file, shows statistics]

👤 You: What element types are in the model?
🤖 Claude: [reads parsed data, analyzes]

👤 You: Classify all elements
🤖 Claude: [prepares batches, spawns element-classifier agent, returns results]
```

## Output Files

**Session context** (`workspace/.context/[filename]_[timestamp]/`):
- `parsed_data.json` - Complete parsed IFC data (intermediate)
- `batches.json` - Element batches for classification (intermediate)

**Final outputs** (`workspace/`):
- `batch_1_elements.json` - Comprehensive element data for batch 1
- `batch_2_elements.json` - Comprehensive element data for batch 2
- ... (one file per batch)

Each element in the output contains:
- Element identity and type
- Functional classification (structural/enclosure/partition/finishing)
- Material composition (primary + secondary with percentages)
- Quantities (volume_m3, area_m2, dimensions)
- Properties and spatial context
- Data quality assessment and reasoning

## What Was Fixed

Previous issues:
- ❌ Parallel classifier was orphaned (never connected to orchestrator)
- ❌ co2-classifier agent definition was decorative (never spawned)
- ❌ Tools returned pretty text instead of structured JSON
- ❌ Manual file juggling with temp files
- ❌ Over-prescriptive orchestration (micromanaging Claude)

New architecture:
- ✅ Single entry point (run.py)
- ✅ Tools return JSON that Claude can parse
- ✅ Agent properly spawned via Task tool when needed
- ✅ Claude drives the workflow autonomously
- ✅ Clean separation: tools (functions) vs agents (specialized AI)
- ✅ All clutter removed (70% less code)

## Development

To extend this system:

1. **Add new tool** - Create a function in `tools/ifc_analysis_tool.py` with `@tool` decorator
2. **Add new agent** - Create `.claude/agents/{name}.md` with domain expertise
3. **Modify workflow** - Update the goal in `run.py`, Claude figures out the steps

## Dutch Construction Context

- Material naming: "Beton", "Gewapend beton"
- Concrete grades: C20/25, C30/37, C35/45, C40/50
- Standards: NIBE database, MPG compliance
- Units: Metric (m³ for volumes)

## Requirements

- Python 3.10+
- Anthropic API key
- IFC files (Industry Foundation Classes format)

## License

Internal project - BIM AI (bimai.nl)

## Contact

Stefan Daniels - stefan@bimai.nl
