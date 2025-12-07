# IFC Parsing Guide (Level 3 Resource)

This document provides detailed information about IFC file parsing for CO2 analysis. Load this when dealing with parsing issues or understanding IFC data structure.

## Supported IFC Element Types

### Structural Elements (Primary for CO2)
| IFC Type | Element Type | Description |
|----------|-------------|-------------|
| IfcColumn | column | Vertical load-bearing elements |
| IfcBeam | beam | Horizontal spanning elements |
| IfcWall | wall (various) | Load-bearing or partition walls |
| IfcSlab | slab | Floor slabs, roof slabs |
| IfcFooting | footing | Foundation elements |
| IfcPile | pile | Deep foundation elements |

### Envelope Elements
| IFC Type | Element Type | Description |
|----------|-------------|-------------|
| IfcCurtainWall | curtain_wall | Glass facade systems |
| IfcWindow | window | Window elements |
| IfcDoor | door | Door elements |
| IfcRoof | roof | Roof covering elements |
| IfcCovering | covering | Wall/floor/ceiling finishes |

### Other Elements
| IFC Type | Element Type | Description |
|----------|-------------|-------------|
| IfcStair | stair | Staircase elements |
| IfcRailing | railing | Railings and guards |
| IfcFurnishingElement | furniture | Built-in furniture |

## Parsed Data Structure

### Output Format (parsed_data.json)

```json
{
  "metadata": {
    "filename": "building.ifc",
    "ifc_schema": "IFC4",
    "total_entities": 5234,
    "geometric_elements": 127,
    "file_size_mb": 2.4,
    "parsing_date": "2025-11-26T14:30:00Z"
  },
  "elements": [
    {
      "global_id": "2O2Fr$t4X7Zf8NOew3FNr2",
      "ifc_type": "IfcColumn",
      "name": "Column K1",
      "object_type": "Concrete Column 400x400",
      "materials": [...],
      "quantities": {...},
      "properties": {...},
      "spatial_structure": {...}
    }
  ]
}
```

### Element Data Fields

#### Identity
```json
{
  "global_id": "2O2Fr$t4X7Zf8NOew3FNr2",
  "ifc_type": "IfcColumn",
  "name": "Kolom K1 - 400mm",
  "object_type": "M_Concrete-Round-Column:300mm"
}
```

#### Materials Array
```json
{
  "materials": [
    {
      "name": "Concrete C30/37",
      "category": "Concrete",
      "layer_thickness": 300,
      "fraction": 0.98
    },
    {
      "name": "Reinforcement",
      "category": "Steel",
      "fraction": 0.02
    }
  ]
}
```

#### Quantities Object
```json
{
  "quantities": {
    "BaseQuantities": {
      "NetVolume": 0.38,
      "GrossVolume": 0.42,
      "Height": 3000,
      "CrossSectionArea": 0.126
    },
    "Qto_ColumnBaseQuantities": {
      "Length": 3000,
      "GrossVolume": 0.42
    }
  }
}
```

**Volume Extraction Priority:**
1. `NetVolume` - Preferred (excludes voids)
2. `GrossVolume` - Secondary (includes voids)
3. Calculate from dimensions if both missing

#### Properties Object
```json
{
  "properties": {
    "Pset_ColumnCommon": {
      "LoadBearing": true,
      "IsExternal": false,
      "FireRating": "REI 120"
    },
    "Pset_ConcreteElementGeneral": {
      "ConcreteCover": 35,
      "ConcreteGrade": "C30/37"
    }
  }
}
```

**Key Properties for Classification:**
- `LoadBearing` - Structural role (true = structural)
- `IsExternal` - Envelope vs interior
- `FireRating` - Fire resistance class
- `Reference` - Type reference string
- `ThermalTransmittance` - U-value for envelope

#### Spatial Structure
```json
{
  "spatial_structure": {
    "site": "Project Site",
    "building": "Office Building A",
    "storey": "Ground Floor",
    "storey_elevation": 0.0,
    "space": "Reception Area"
  }
}
```

## Batch Preparation

### Batch Configuration (batches.json)

```json
{
  "metadata": {
    "total_elements": 127,
    "batch_size": 50,
    "num_batches": 3,
    "created_at": "2025-11-26T14:35:00Z"
  },
  "batches": [
    {
      "batch_id": 1,
      "start_index": 0,
      "end_index": 49,
      "element_count": 50,
      "elements": [...],
      "summary": {
        "ifc_types": {"IfcColumn": 12, "IfcWall": 25, "IfcSlab": 8, "IfcBeam": 5},
        "storeys": {"Ground Floor": 30, "First Floor": 20}
      }
    }
  ]
}
```

### Optimal Batch Size

| Model Size | Elements | Batch Size | Reason |
|------------|----------|------------|--------|
| Small | <50 | No batching | Direct processing |
| Medium | 50-200 | 50 | 2-4 parallel agents |
| Large | 200+ | 50 | N parallel agents |

**Why 50 elements per batch?**
- Fits within Claude Haiku context efficiently
- Allows detailed analysis per element
- Enables parallel processing
- Target: <30 seconds per batch

## Error Handling

### Common Parsing Issues

| Issue | Detection | Solution |
|-------|-----------|----------|
| File not found | Path error | Verify absolute path |
| Invalid STEP format | Parse exception | Check IFC validity |
| No geometric elements | `geometric_elements: 0` | Architectural model only |
| Missing quantities | `null` volumes | Use dimension calculations |
| Unicode errors | Encoding exception | Try UTF-8 with fallback |

### Data Quality Indicators

After parsing, check these quality metrics:

```json
{
  "quality_metrics": {
    "elements_with_materials": 95,
    "elements_with_volumes": 87,
    "elements_with_properties": 92,
    "completeness_score": 0.91
  }
}
```

**Completeness thresholds:**
- \>90%: Excellent quality
- 70-90%: Good, minor gaps
- 50-70%: Fair, manual review needed
- <50%: Poor, investigate IFC source

## Dutch IFC Naming Conventions

Common Dutch terms in IFC element names:

| Dutch | English | Element Type |
|-------|---------|-------------|
| Kolom | Column | column |
| Balk | Beam | beam |
| Wand | Wall | wall |
| Vloer | Floor | slab |
| Dak | Roof | roof |
| Fundering | Foundation | footing |
| Deur | Door | door |
| Raam | Window | window |
| Trap | Stair | stair |
| Plafond | Ceiling | ceiling |

## IFC Schema Reference

### IFC4 vs IFC2x3

| Feature | IFC4 | IFC2x3 |
|---------|------|--------|
| Material layers | Enhanced | Basic |
| Quantities | Standardized | Varied |
| Geometry | Improved | Standard |
| MEP | Full support | Limited |

Both schemas are supported. IFC4 provides richer data extraction.

### Entity Hierarchy

```
IfcProduct (abstract)
├── IfcElement (abstract)
│   ├── IfcBuildingElement
│   │   ├── IfcColumn
│   │   ├── IfcBeam
│   │   ├── IfcWall
│   │   ├── IfcSlab
│   │   ├── IfcStair
│   │   └── ...
│   ├── IfcOpeningElement
│   └── IfcFurnishingElement
├── IfcSpatialElement
│   ├── IfcSite
│   ├── IfcBuilding
│   ├── IfcBuildingStorey
│   └── IfcSpace
└── IfcProxy (catch-all)
```

---

*IFC Parsing Guide for buildOS*
*Reference: IFC4 Documentation, buildingSMART*
