---
name: ifc-analysis
description: Analyze IFC building models for CO2 emissions. Parses IFC files, classifies materials, calculates embodied carbon using Dutch NIBE database, and generates PDF reports.
---

# IFC CO2 Analysis Skill

Analyze IFC (Industry Foundation Classes) building models for environmental impact. This skill handles the complete workflow from raw IFC to CO2 report.

## When to Use This Skill

- User uploads `.ifc` file and asks about CO2, carbon, or emissions
- User wants sustainability analysis of a building model
- User mentions NIBE, MPG, or Dutch building standards
- User asks "how much CO2" or "environmental impact"
- User wants a sustainability report

## Quick Reference

| Step | Tool/Script | Input | Output |
|------|------------|-------|--------|
| 1. Parse IFC | `mcp__ifc__parse_ifc_file` | .ifc file | parsed_data.json |
| 2. Prepare Batches | `mcp__ifc__prepare_batches` | parsed_data.json | batches.json |
| 3. Classify | Task agent (batch-processor) | batches.json | batch_X_elements.json |
| 4. Calculate CO2 | `mcp__ifc__calculate_co2` | classified.json | co2_report.json |
| 5. Generate PDF | `scripts/generate_pdf.py` | co2_report.json | report.pdf |

## Workflow Decision Tree

### Small Models (<50 elements)
```
IFC → Parse → Classify directly (no batching) → Calculate CO2 → Report
```

### Medium Models (50-200 elements)
```
IFC → Parse → Create 2-4 batches → Classify in parallel → Aggregate → Calculate CO2 → Report
```

### Large Models (200+ elements)
```
IFC → Parse → Create N batches (50 elements each) → Spawn N Task agents → Aggregate → Calculate CO2 → PDF Report
```

## Step-by-Step Workflow

### Step 1: Parse IFC File

Use MCP tool to extract building elements:

```
Tool: mcp__ifc__parse_ifc_file
Parameters:
  ifc_path: {absolute_path_to_ifc}
  output_path: .context/{session}/parsed_data.json
```

**Output**: JSON with metadata and elements array
- Extracts: IfcWall, IfcColumn, IfcSlab, IfcBeam, IfcDoor, IfcWindow, IfcRoof, IfcStair, IfcCovering, IfcFurnishingElement, IfcFooting
- Includes: materials, quantities, properties, spatial structure

### Step 2: Prepare Batches (If >50 elements)

```
Tool: mcp__ifc__prepare_batches
Parameters:
  json_path: .context/{session}/parsed_data.json
  batch_size: 50
  output_path: .context/{session}/batches.json
```

**Output**: JSON with batches array, each containing ~50 elements

### Step 3: Classify Elements

For each batch, spawn a Task agent:

```
Task: batch-processor
Prompt: Process batch {N} for sustainability analysis.
  Session context: .context/{session}/
  Batch number: {N}
  Output file: .context/{session}/batch_{N}_elements.json
```

**For parallel processing**: Spawn multiple Task agents simultaneously for different batches.

See **CLASSIFICATION.md** for detailed material classification guidance.

### Step 4: Calculate CO2

```
Tool: mcp__ifc__calculate_co2
Parameters:
  classified_path: .context/{session}/batch_X_elements.json
  database_path: $CLAUDE_PROJECT_DIR/.claude/skills/ifc-analysis/reference/durability_database.json
  output_path: .context/{session}/co2_report.json
```

See **CO2-CALCULATION.md** for calculation methodology and NIBE database reference.

### Step 5: Generate PDF Report (Optional)

```bash
python $CLAUDE_PROJECT_DIR/.claude/skills/ifc-analysis/scripts/generate_pdf.py \
  .context/{session}/co2_report.json \
  {ifc_filename} \
  .context/{session}/co2_report.pdf
```

Creates a professional A4 PDF with executive summary, material breakdown, and methodology.

## Output Formats

### Parsed Data (parsed_data.json)
```json
{
  "metadata": {"total_entities": 5234, "geometric_elements": 127},
  "elements": [{"global_id": "...", "ifc_type": "IfcColumn", ...}]
}
```

### Classified Elements (batch_X_elements.json)
```json
[{
  "global_id": "...",
  "element_type": "column",
  "material_primary": {"category": "concrete", "subcategory": "C30/37"},
  "volume_m3": 0.38,
  "confidence": 0.90
}]
```

### CO2 Report (co2_report.json)
```json
{
  "summary": {"total_co2_kg": 31428.13, "total_elements": 50},
  "by_category": {"concrete": {"co2_kg": 10472.36, "percentage": 33.3}},
  "detailed_results": [...]
}
```

## Related Guides (Load On-Demand)

- **PARSING.md**: IFC file structure, supported element types, extraction logic
- **CLASSIFICATION.md**: Material categories, element types, confidence scoring
- **CO2-CALCULATION.md**: NIBE database, reinforcement factors, timber carbon sinks

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/parse_ifc.py` | CLI wrapper for IFC parsing |
| `scripts/prepare_batches.py` | CLI wrapper for batch preparation |
| `scripts/calculate_co2.py` | CO2 calculation with database lookup |
| `scripts/generate_pdf.py` | PDF report generation (reportlab) |
| `scripts/analyze_batch.py` | Batch statistics helper |

## Reference Data

- `reference/durability_database.json` - NIBE CO2 factors with densities
- `reference/co2_factors.json` - Quick CO2 lookup table
- `reference/ifc_schema.md` - Supported IFC element types

## Error Handling

| Error | Solution |
|-------|----------|
| IFC file not found | Check path is absolute and file exists |
| No geometric elements | Model may be architectural only |
| Material not in database | Use generic fallback for category |
| Missing volume data | Skip element, note in warnings |

## Quality Targets

- **Completeness**: 100% of elements processed
- **Accuracy**: >90% correct material classification
- **Confidence**: >70% of elements with confidence >= 0.7
- **Speed**: <2 minutes for 500-element model

---

*IFC Analysis Skill for buildOS*
*Target: Dutch construction industry sustainability reporting*
