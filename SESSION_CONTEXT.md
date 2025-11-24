# Session Context System

## Overview

The system now uses a session-based context folder structure to separate intermediate data from final outputs. This keeps the workspace clean and makes it easy to track what files are temporary vs. permanent results.

## Folder Structure

```
workspace/
├── .context/                           # Session context (gitignored)
│   ├── Small_condo_20251123_143022/   # Timestamped session folder
│   │   ├── parsed_data.json           # Parsed IFC data
│   │   └── batches.json               # Element batches for classification
│   └── interactive_20251123_150330/   # Interactive session
│       └── ...
├── batch_1_classifications.json        # Final output: Classification results
├── batch_2_classifications.json        # Final output: More results
└── final_report.json                   # Final output: Aggregated report
```

## Session Context vs Final Output

### Session Context (`.context/[name]_[timestamp]/`)

**Purpose:** Temporary intermediate data for a single analysis run

**Contents:**
- `parsed_data.json` - Complete parsed IFC file data
- `batches.json` - Element batches prepared for classification
- Other intermediate processing files

**Characteristics:**
- Created automatically with timestamp
- Named after IFC file (e.g., `Small_condo_20251123_143022`)
- Can be deleted after analysis completes
- Useful for debugging and understanding the pipeline
- Gitignored (not committed to version control)

### Final Output (workspace root)

**Purpose:** Results to keep and share

**Contents:**
- `batch_N_classifications.json` - Classification results per batch
- `final_report.json` - Aggregated CO2 analysis report
- `validation_queue.json` - Elements needing manual review
- Other deliverable files

**Characteristics:**
- Saved in workspace root for easy access
- These are the files users care about
- Can be committed to git if desired
- Ready to share with clients or import to other tools

## How It Works

### Automatic Session Creation

When you run an analysis:

```bash
uv run python run.py Small_condo.ifc
```

The system automatically:
1. Creates timestamp: `20251123_143022`
2. Extracts IFC basename: `Small_condo`
3. Creates context folder: `workspace/.context/Small_condo_20251123_143022/`
4. Stores all intermediate data there
5. Saves final outputs to workspace root

### Path Management

**Orchestrator responsibilities:**
- Creates session context folder
- Passes session context path to all tools and agents
- Uses relative paths from workspace

**Agent responsibilities:**
- Reads from session context folder (as instructed)
- Writes final outputs to workspace root
- Uses exact paths provided by orchestrator

## Benefits

### 1. Clean Workspace
- Workspace root only contains final deliverables
- No clutter from intermediate processing files
- Easy to see what results are available

### 2. Session Isolation
- Multiple analyses can run without file conflicts
- Each session has its own context folder
- Timestamps prevent naming collisions

### 3. Debugging Support
- Session context preserved for troubleshooting
- Can inspect intermediate data if issues arise
- Full pipeline data available for analysis

### 4. Clear Intent
- Session context = temporary, can delete
- Workspace root = final results, keep these
- No confusion about what files matter

### 5. Version Control
- `.context/` folders are gitignored
- Don't bloat repository with intermediate data
- Only commit code and important results

## Usage Examples

### Running Analysis

```bash
# Run CO2 analysis
uv run python run.py Small_condo.ifc

# Output shows:
# IFC File: Small_condo.ifc
# Workspace: /path/to/workspace
# Session Context: .context/Small_condo_20251123_143022
```

### Accessing Session Data

If you need to inspect intermediate data:

```python
# Read parsed IFC data
import json
from pathlib import Path

session = Path("workspace/.context/Small_condo_20251123_143022")
with open(session / "parsed_data.json") as f:
    data = json.load(f)
```

### Cleanup

Delete old session contexts to save space:

```bash
# Remove all session contexts
rm -rf workspace/.context/

# Remove sessions older than 7 days
find workspace/.context/ -type d -mtime +7 -exec rm -rf {} +

# Keep only the most recent 5 sessions
ls -t workspace/.context/ | tail -n +6 | xargs -I {} rm -rf workspace/.context/{}
```

### Interactive Mode

Interactive sessions also get context folders:

```bash
uv run python run.py

# Creates: workspace/.context/interactive_20251123_150330/
```

## Orchestrator Instructions

When spawning agents, the orchestrator provides:

```python
f"""
**Context:**
- Session context folder: {session_context_rel}
- Read batch data from: {session_context_rel}/batches.json
- Save output to: batch_1_classifications.json (in workspace root)
"""
```

This ensures agents know:
1. Where to find input data (session context)
2. Where to save outputs (workspace root)
3. Exact file paths to use

## Agent Instructions

Agents understand:

1. **Input files** are in session context folder
   - Example: `.context/Small_condo_20251123_143022/batches.json`

2. **Output files** go to workspace root
   - Example: `batch_1_classifications.json`

3. **All paths** are relative to workspace CWD

## File Lifecycle

```
1. User runs: uv run python run.py Small_condo.ifc

2. System creates session context folder
   └─> .context/Small_condo_20251123_143022/

3. Parse IFC file
   └─> .context/Small_condo_20251123_143022/parsed_data.json

4. Prepare batches
   └─> .context/Small_condo_20251123_143022/batches.json

5. Classify elements (agent reads from context, writes to workspace)
   └─> batch_1_classifications.json

6. Final report
   └─> final_report.json

7. User reviews results in workspace root

8. Optional: Clean up old session contexts
```

## .gitignore Configuration

Add to `.gitignore`:

```
# Session context (intermediate data)
workspace/.context/

# But keep final outputs
!workspace/*.json
!workspace/*.csv
!workspace/*.xlsx
```

## Future Enhancements

Potential improvements:

1. **Auto-cleanup**: Delete session contexts older than N days
2. **Session linking**: Store metadata linking sessions to outputs
3. **Resume capability**: Restart failed analyses from session context
4. **Context compression**: Archive old sessions as tar.gz
5. **Session browser**: Web UI to explore session history

---

*Document created: 2025-11-23*
*Implements: Session-based context folder structure*
