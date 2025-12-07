# Material Classification Guide (Level 3 Resource)

This document provides detailed guidance for classifying building elements and materials. Load this when processing element batches or troubleshooting classification decisions.

## Element Type Classification

### Structural Elements

| element_type | IFC Types | Key Indicators |
|-------------|-----------|----------------|
| `column` | IfcColumn | LoadBearing=true, vertical |
| `beam` | IfcBeam | LoadBearing=true, horizontal |
| `load_bearing_wall` | IfcWall | LoadBearing=true |
| `slab_structural` | IfcSlab | Floor/roof slab, LoadBearing=true |
| `foundation_wall` | IfcWall | Below ground, storey_elevation < 0 |
| `foundation_slab` | IfcSlab | Below ground, storey_elevation < 0 |
| `footing` | IfcFooting | Foundation element |
| `pile` | IfcPile | Deep foundation |
| `core_wall` | IfcWall | Elevator/stair core |

### Envelope Elements

| element_type | IFC Types | Key Indicators |
|-------------|-----------|----------------|
| `external_wall` | IfcWall | IsExternal=true, not load-bearing |
| `roof_structure` | IfcRoof, IfcSlab | Roof level, structural |
| `roof_covering` | IfcCovering | Roof level, finishing |
| `curtain_wall` | IfcCurtainWall | Glass facade |
| `window` | IfcWindow | Glazing element |
| `door_external` | IfcDoor | IsExternal=true |

### Interior Elements

| element_type | IFC Types | Key Indicators |
|-------------|-----------|----------------|
| `partition_wall` | IfcWall | LoadBearing=false, IsExternal=false |
| `door_internal` | IfcDoor | IsExternal=false |
| `ceiling` | IfcCovering | CoveringType=CEILING |
| `raised_floor` | IfcCovering | CoveringType=FLOORING |
| `floor_finish` | IfcCovering | Floor covering |
| `wall_finish` | IfcCovering | Wall covering |

### Other Elements

| element_type | IFC Types | Key Indicators |
|-------------|-----------|----------------|
| `stair` | IfcStair | Staircase |
| `railing` | IfcRailing | Guard, handrail |
| `ramp` | IfcRamp | Accessibility ramp |
| `other` | IfcProxy, unknown | Catch-all |

## Material Categories

### Concrete

**Category**: `concrete`

| Subcategory | Dutch Terms | CO2 Factor Range |
|-------------|-------------|------------------|
| `C20/25` | Beton C20/25 | 0.110 kg/kg |
| `C25/30` | Beton C25/30 | 0.115 kg/kg |
| `C30/37` | Beton C30/37 | 0.120 kg/kg |
| `C35/45` | Beton C35/45 | 0.125 kg/kg |
| `C40/50` | Beton C40/50 | 0.130 kg/kg |
| `concrete_insitu` | Stortbeton | Use grade |
| `concrete_precast` | Prefab beton | Use grade |
| `concrete_generic` | Beton (generic) | 0.115 kg/kg |

**Identification patterns:**
- "Beton", "Concrete", "C20", "C25", "C30", etc.
- "Gewapend beton" = Reinforced concrete
- "Ongewapend beton" = Unreinforced concrete

### Steel

**Category**: `steel`

| Subcategory | Description | CO2 Factor |
|-------------|-------------|------------|
| `steel_structural` | S235, S355, S460 sections | 1.85 kg/kg |
| `steel_reinforcement` | Rebar, mesh | 1.65 kg/kg |
| `steel_stainless` | Stainless finishes | 4.20 kg/kg |

**Identification patterns:**
- "Steel", "Staal", "S235", "S355", "HEA", "HEB", "IPE"
- "Wapeningsstaal", "Reinforcement"
- "RVS", "Stainless"

### Timber

**Category**: `timber`

| Subcategory | Description | CO2 Factor |
|-------------|-------------|------------|
| `timber_softwood` | Pine, spruce, fir | -0.95 kg/kg |
| `timber_hardwood` | Oak, beech | -0.85 kg/kg |
| `timber_engineered` | CLT, glulam, LVL | -0.65 kg/kg |

**Note**: Timber has NEGATIVE CO2 factors (carbon sink)

**Identification patterns:**
- "Hout", "Wood", "Timber"
- "Eiken" (oak), "Beuken" (beech)
- "Vuren" (spruce), "Grenen" (pine)
- "CLT", "Glulam", "LVL", "Multiplex"

### Masonry

**Category**: `masonry`

| Subcategory | Dutch Term | CO2 Factor |
|-------------|------------|------------|
| `brick_clay` | Baksteen | 0.220 kg/kg |
| `brick_calcium_silicate` | Kalkzandsteen | 0.135 kg/kg |
| `concrete_block` | Betonblok | 0.105 kg/kg |
| `stone_natural` | Natuursteen | 0.060 kg/kg |

**Identification patterns:**
- "Metselwerk", "Masonry"
- "Baksteen", "Brick"
- "Kalkzandsteen", "KZS"
- "Betonblok", "CMU"

### Insulation

**Category**: `insulation`

| Subcategory | Description | Density | CO2 Factor |
|-------------|-------------|---------|------------|
| `insulation_mineral_wool` | Glass/rock wool | 40 kg/m³ | 1.35 kg/kg |
| `insulation_eps` | Expanded polystyrene | 25 kg/m³ | 3.45 kg/kg |
| `insulation_xps` | Extruded polystyrene | 35 kg/m³ | 5.85 kg/kg |
| `insulation_pur_pir` | PUR/PIR foam | 30 kg/m³ | 3.95 kg/kg |
| `insulation_bio` | Wood fiber, hemp | 50 kg/m³ | 0.15 kg/kg |

**Identification patterns:**
- "Isolatie", "Insulation"
- "Minerale wol", "Glaswol", "Steenwol"
- "EPS", "Tempex", "Piepschuim"
- "XPS", "Styrodur"
- "PUR", "PIR", "Purschuim"

### Gypsum

**Category**: `gypsum`

| Subcategory | Description | CO2 Factor |
|-------------|-------------|------------|
| `gypsum_board` | Plasterboard | 0.185 kg/kg |
| `gypsum_plaster` | Plaster finish | 0.185 kg/kg |

**Identification patterns:**
- "Gips", "Gypsum"
- "Gipsplaat", "Gipskarton"
- "Stuc", "Plaster"

### Glass

**Category**: `glass`

| Subcategory | Description | CO2 Factor |
|-------------|-------------|------------|
| `glass_float` | Float glass | 0.85 kg/kg |
| `glass_double` | Double glazing | 0.95 kg/kg |
| `glass_triple` | Triple glazing | 1.05 kg/kg |

**Identification patterns:**
- "Glas", "Glass", "Glazing"
- "Dubbel glas", "Double"
- "HR++", "Triple"

### Aluminum

**Category**: `aluminum`

| Subcategory | Description | CO2 Factor |
|-------------|-------------|------------|
| `aluminum_sections` | Profiles, frames | 8.50 kg/kg |
| `aluminum_sheet` | Sheet material | 8.50 kg/kg |

**High CO2 impact** - flag for attention

## Classification Logic

### Step 1: Extract Identity
```
1. Read global_id, ifc_type, name
2. Extract storey from spatial_structure
3. Normalize element_type from IFC type
```

### Step 2: Determine Function
```
IF LoadBearing = true:
    function = "structural"
    IF IsExternal = true:
        location = "external"
    ELSE:
        location = "internal"
ELIF IsExternal = true:
    function = "enclosure"
    location = "external"
ELSE:
    function = "partition" OR "finishing"
    location = "internal"
```

### Step 3: Classify Element Type
```
IF ifc_type = "IfcColumn":
    element_type = "column"
ELIF ifc_type = "IfcBeam":
    element_type = "beam"
ELIF ifc_type = "IfcWall":
    IF LoadBearing = true:
        IF storey_elevation < 0:
            element_type = "foundation_wall"
        ELSE:
            element_type = "load_bearing_wall"
    ELIF IsExternal = true:
        element_type = "external_wall"
    ELSE:
        element_type = "partition_wall"
...
```

### Step 4: Identify Materials
```
1. Extract material names from materials array
2. Match against category patterns (see above)
3. Identify primary material (>50% or main structural)
4. List secondary materials
5. Assign category + subcategory
```

### Step 5: Extract Quantities
```
VOLUME extraction priority:
1. quantities.BaseQuantities.NetVolume
2. quantities.BaseQuantities.GrossVolume
3. quantities.Qto_*Quantities.NetVolume
4. Calculate: length × width × height
5. Estimate from typical values

AREA extraction priority:
1. quantities.BaseQuantities.NetArea
2. quantities.BaseQuantities.GrossArea
3. Calculate from dimensions
```

## Confidence Scoring

### Score Guidelines

| Confidence | Data Quality | When to Use |
|------------|-------------|-------------|
| 0.95-1.00 | Complete IFC data | All fields populated, explicit materials |
| 0.85-0.95 | Good data | Most fields, clear material identification |
| 0.70-0.85 | Adequate | Volume present, material inferred |
| 0.50-0.70 | Limited | Missing quantities, uncertain materials |
| 0.30-0.50 | Poor | Major assumptions, flag for review |
| 0.00-0.30 | Very uncertain | Minimal data, manual review required |

### Confidence Factors

**Increase confidence:**
- Explicit material properties in IFC
- NetVolume from BaseQuantities
- LoadBearing property present
- Clear element naming

**Decrease confidence:**
- Material inferred from element type
- Volume calculated/estimated
- Missing properties
- Generic/ambiguous naming

## Output Schema

### Complete Element Classification

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
    {
      "name": "Reinforcement steel",
      "category": "steel",
      "subcategory": "steel_reinforcement",
      "percentage": 2
    }
  ],
  "material_notes": "Standard reinforced concrete column",

  "volume_m3": 0.38,
  "area_m2": 3.77,
  "dimensions": {
    "diameter_mm": 400,
    "height_m": 3.0
  },

  "properties": {
    "LoadBearing": true,
    "IsExternal": false,
    "FireRating": "REI 120"
  },
  "spatial_context": {
    "building": "Office Building A",
    "storey": "Ground Floor",
    "space": null
  },

  "confidence": 0.90,
  "data_quality": {
    "material_source": "ifc_properties",
    "quantity_source": "ifc_quantities",
    "missing_data": [],
    "assumptions": ["2% reinforcement ratio typical for columns"]
  },
  "reasoning": "Load-bearing column identified from LoadBearing=true and IfcColumn type. Concrete C30/37 material from IFC properties. Volume from BaseQuantities. High confidence due to complete data."
}
```

## Quality Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Completeness | 100% | All batch elements classified |
| Accuracy | >90% | Correct element_type and material |
| Data richness | >80% | Fields populated per element |
| Confidence | >70% | Elements with confidence >= 0.7 |
| Speed | <60 sec | 50 elements per batch |

---

*Material Classification Guide for buildOS*
*Target: Dutch construction industry sustainability reporting*
