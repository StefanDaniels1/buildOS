# CSV Agent Specification

## Implementation Status: COMPLETED

---

## Overview

**Feature Name:** CSV Agent
**Purpose:** Analyze uploaded CSV data, perform transformations, and integrate with the ClaudeAgentClient workflow. The agent can fetch data, transform it, and prepare it in the spreadsheet for user editing and iteration.
**Target Users:** Data analysts, sustainability consultants, BIM managers
**FrontEnd:** Implemented in `SpreadsheetBuilder.vue`

---

## Data Input Methods

The CSV Agent supports two primary methods for receiving data:

### 1. Context Window Upload (User Upload)

Files uploaded via the ChatWindow component are passed to the orchestrator.

**Supported File Types:**
- [x] CSV (.csv)
- [x] TSV (.tsv)
- [x] Auto-detected delimiters (comma, semicolon, tab, pipe)

**Encoding Support:**
- [x] UTF-8 (with BOM support)

### 2. MCP Tool Integration

Built-in MCP tools registered in `sdk_tools.py`:

**Tool Names:**
- `mcp__ifc__parse_csv` - Parse and preview CSV data
- `mcp__ifc__analyze_csv` - Generate statistics and analysis
- `mcp__ifc__csv_to_spreadsheet` - Load CSV into Spreadsheet Builder (PRIMARY)
- `mcp__ifc__transform_csv` - Filter, sort, aggregate data

**Input Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source` | string | Yes | "file_path", "url", or "inline_data" |
| `file_path` | string | No | Path to uploaded file |
| `url` | string | No | URL to fetch CSV from |
| `inline_data` | string | No | Raw CSV string |
| `delimiter` | string | No | Auto-detected if not provided |
| `has_header` | bool | No | Default: true |
| `preview_rows` | int | No | Limit rows for preview |

**Custom Tool Template:** Available at `/api/tools/templates` for UI configuration

---

## Processing Capabilities

### Core Features

- [x] **Parse CSV** - Read and validate CSV structure (`parse_csv`)
- [x] **Preview Data** - Show first N rows for validation (`preview_rows` param)
- [x] **Column Analysis** - Detect types, stats, missing values (`analyze_csv`)
- [x] **Data Filtering** - Filter rows by conditions (`transform_csv`)
- [x] **Data Transformation** - Sort, select columns (`transform_csv`)
- [x] **Aggregation** - Sum, average, count, min, max with group by (`transform_csv`)
- [ ] **Joining** - Merge multiple CSVs (not yet implemented)
- [x] **Validation** - Check data quality, missing values (`analyze_csv`)

### Analysis Features

- [x] **Statistical Summary** - Min, max, mean, sum per column (`analyze_csv`)
- [ ] **Correlation Analysis** - Not yet implemented
- [ ] **Outlier Detection** - Not yet implemented
- [ ] **Trend Analysis** - Not yet implemented
- [x] **Category Distribution** - Value counts, top values (`analyze_csv`)

### BIM/CO2 Specific Features

- [ ] **Material Mapping** - Use existing IFC tools
- [ ] **Quantity Extraction** - Use existing IFC tools
- [ ] **Element Classification** - Use existing IFC tools
- [ ] **CO2 Calculation** - Use existing IFC tools

---

## Output Formats

### Spreadsheet Display

Return data for `SpreadsheetBuilder.vue`:

```json
{
  "spreadsheet": {
    "name": "Analysis Results",
    "data": [
      ["Column A", "Column B", "Column C"],
      ["value1", "value2", "value3"]
    ],
    "columns": [
      {"title": "Column A", "width": 150},
      {"title": "Column B", "width": 120},
      {"title": "Column C", "width": 100}
    ]
  }
}
```

### Export Options

- [ ] CSV download
- [ ] Excel (.xlsx) download
- [ ] JSON export
- [ ] PDF report
- [ ] Other: [FILL IN]

### Visualization (Optional)

- [ ] Bar charts
- [ ] Line charts
- [ ] Pie charts
- [ ] Scatter plots
- [ ] Tables with conditional formatting
- [ ] Other: [FILL IN]

---

## Agent Behavior

### Conversation Flow

1. **Trigger:** ["User uploads CSV or asks to analyze data"]
2. **Initial Response:** ["Acknowledge file, show preview, ask what to analyze"]
3. **Processing:** ["Execute requested analysis with progress updates"]
4. **Output:** [ "Present results in spreadsheet + summary text"]

### Error Handling

| Error Type | Response |
|------------|----------|
| Invalid CSV format | [stop action] |
| File too large | [notify file to large] |
| Missing columns | [find columns] |
| Data type mismatch | [notify type mismatch] |

### Event Types to Broadcast

| Event Type | When | Payload |
|------------|------|---------|
| `CSVUploaded` | File received | `{filename, rows, columns}` |
| `CSVProcessing` | Analysis started | `{operation, status}` |
| `CSVAnalysisComplete` | Analysis done | `{results, spreadsheet}` |
| `CSVError` | Error occurred | `{error, suggestion}` |
| [ADD MORE] | | |

---

## Integration Points

### With Existing Components

| Component | Integration |
|-----------|-------------|
| `ChatWindow.vue` | File upload passes CSV to orchestrator via `availableFiles` |
| `SpreadsheetBuilder.vue` | Displays CSV data, supports Import button, handles events |
| `EventTimeline.vue` | Shows processing events (Stop, CSVLoaded, SpreadsheetReady) |
| `orchestrator.py` | Tool registration via `mcp__ifc__*`, CSV tools in system prompt |

### With MCP Tools

| Tool | Purpose |
|------|---------|
| `mcp__ifc__parse_csv` | Parse and preview CSV files |
| `mcp__ifc__analyze_csv` | Generate column statistics |
| `mcp__ifc__csv_to_spreadsheet` | Load CSV into UI spreadsheet |
| `mcp__ifc__transform_csv` | Filter, sort, aggregate data |
| `mcp__ifc__generate_spreadsheet` | Display any tabular data |
| `mcp__custom__csv_processor` | Template for custom CSV processing |

---

## Technical Requirements

### Dependencies (Python)

```
# Built-in modules only (no pandas required)
csv (stdlib)
io (stdlib)
collections (stdlib)
httpx (for URL fetching, already installed)
```

### Dependencies (Client)

```
jspreadsheet-ce (already installed)
```

### Performance Targets

| Metric | Target |
|--------|--------|
| Parse 10k rows | < 2 seconds |
| Analysis operation | < 5 seconds |
| Max rows loaded | 1000 (configurable via max_rows) |

---

## Security Considerations

- [x] Sanitize file paths (uses `_resolve_path` helper)
- [x] Validate file content (CSV parsing validates structure)
- [x] Limit memory usage (`max_rows` parameter, default 1000)
- [x] Path traversal prevention (server-side validation)

---

## Implementation Phases

### Phase 1: Core Parsing - COMPLETED
- [x] CSV parsing with auto-delimiter detection
- [x] File upload integration (via ChatWindow)
- [x] Spreadsheet display (SpreadsheetBuilder.vue)
- [x] Direct Import button in SpreadsheetBuilder

### Phase 2: Analysis Features - COMPLETED
- [x] Statistical analysis (`analyze_csv`)
- [x] Data filtering (`transform_csv`)
- [x] Column transformations (`transform_csv`)
- [x] Sorting and grouping

### Phase 3: Advanced Features - COMPLETED
- [x] Edit CSV data in SpreadsheetBuilder
- [x] Save to session context (`/api/spreadsheet/save`)
- [x] Load saved spreadsheets (`/api/spreadsheet/load`)

### Phase 4: Integration - COMPLETED
- [x] Fetch from file path (uploaded files)
- [x] Fetch from URL (via parse_csv)
- [x] Show in spreadsheet editor
- [x] Custom tool template for UI configuration

---