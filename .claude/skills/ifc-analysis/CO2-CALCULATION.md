# CO2 Calculation Guide (Level 3 Resource)

This document provides detailed guidance for calculating embodied CO2 from classified building elements. Load this when performing CO2 calculations or troubleshooting calculation issues.

## NIBE Database Overview

The durability database uses data from NIBE (Dutch national environmental database).

**Location**: `.claude/skills/ifc-analysis/reference/durability_database.json`

### Database Structure

```json
{
  "materials": {
    "concrete": {
      "C30/37": {
        "embodied_co2_per_kg": 0.120,
        "density_kg_m3": 2400,
        "source": "NIBE-generic",
        "notes": "Higher strength concrete"
      }
    }
  },
  "reinforcement_ratios": {
    "column": 2.5,
    "beam": 2.8
  }
}
```

### Key Fields

| Field | Unit | Description |
|-------|------|-------------|
| `embodied_co2_per_kg` | kg CO2-eq/kg | CO2 factor per kilogram material |
| `density_kg_m3` | kg/m³ | Material density |
| `source` | string | Data source (NIBE-generic, NIBE-fallback) |

## CO2 Calculation Formula

### Basic Calculation

```
mass_kg = volume_m3 × density_kg_m3
co2_kg = mass_kg × embodied_co2_per_kg
```

### Example: Concrete Column

```
Volume: 0.38 m³
Density: 2400 kg/m³
CO2 factor: 0.120 kg CO2/kg

Mass = 0.38 × 2400 = 912 kg
CO2 = 912 × 0.120 = 109.44 kg CO2-eq
```

## Material Lookup Strategy

### Priority Order

1. **Exact subcategory match**
   ```
   materials["concrete"]["C30/37"] ✓
   ```

2. **Generic fallback in category**
   ```
   materials["concrete"]["concrete_generic"] ✓
   ```

3. **First material in category**
   ```
   materials["concrete"][<first_key>] ✓
   Add warning: "Used C20/25 as fallback for concrete"
   ```

4. **Skip element**
   ```
   Add warning: "Material not found in database"
   calculation_method: "skipped"
   ```

## Reinforcement Calculation (Concrete Only)

### When to Add Reinforcement

Add reinforcement steel to concrete elements with structural roles:

| Element Type | Reinforcement Ratio | Notes |
|--------------|---------------------|-------|
| `footing` | 1.5% | Foundation pad |
| `foundation_wall` | 1.8% | Basement wall |
| `foundation_slab` | 1.8% | Foundation mat |
| `column` | 2.5% | Vertical support |
| `beam` | 2.8% | Horizontal spanning |
| `slab_structural` | 2.0% | Floor slab |
| `load_bearing_wall` | 2.0% | Structural wall |

### Reinforcement Formula

```
rebar_mass_kg = concrete_mass_kg × (ratio_percent / 100)
rebar_co2_kg = rebar_mass_kg × steel_reinforcement_co2_factor

where:
  steel_reinforcement_co2_factor = 1.65 kg CO2/kg
```

### Example: Reinforced Column

```
Concrete mass: 912 kg
Reinforcement ratio: 2.5%
Steel CO2 factor: 1.65 kg CO2/kg

Rebar mass = 912 × 0.025 = 22.8 kg
Rebar CO2 = 22.8 × 1.65 = 37.62 kg CO2

Total CO2 = 109.44 + 37.62 = 147.06 kg CO2-eq
```

**Always log**: `"Added 2.5% reinforcement (22.8 kg steel)"`

## Carbon Sink Materials (Timber)

### Negative CO2 Values

Timber products have NEGATIVE CO2 factors because they sequester carbon:

| Material | CO2 Factor | Explanation |
|----------|------------|-------------|
| `timber_softwood` | -0.95 kg/kg | Pine, spruce, fir |
| `timber_hardwood` | -0.85 kg/kg | Oak, beech |
| `timber_engineered` | -0.65 kg/kg | CLT, glulam, LVL |

**CRITICAL**: Preserve negative values in calculations and reporting!

### Example: Timber Beam

```
Volume: 0.15 m³
Density: 500 kg/m³
CO2 factor: -0.95 kg CO2/kg

Mass = 0.15 × 500 = 75 kg
CO2 = 75 × (-0.95) = -71.25 kg CO2-eq

This REDUCES total building CO2!
```

## CO2 Factors Reference

### High Impact Materials (>1.0 kg CO2/kg)

| Material | CO2 Factor | Priority |
|----------|------------|----------|
| Aluminum | 8.50 | Critical |
| XPS insulation | 5.85 | High |
| Stainless steel | 4.20 | High |
| PUR/PIR insulation | 3.95 | High |
| EPS insulation | 3.45 | High |
| Structural steel | 1.85 | High |
| Steel reinforcement | 1.65 | High |
| Mineral wool | 1.35 | Medium |

### Medium Impact Materials (0.1-1.0 kg CO2/kg)

| Material | CO2 Factor |
|----------|------------|
| Glass | 0.85 |
| Clay brick | 0.22 |
| Gypsum | 0.185 |
| Calcium silicate | 0.135 |
| Concrete (various) | 0.11-0.13 |
| Concrete block | 0.105 |

### Low/Negative Impact Materials

| Material | CO2 Factor |
|----------|------------|
| Natural stone | 0.06 |
| Bio insulation | 0.15 |
| Timber engineered | -0.65 |
| Timber hardwood | -0.85 |
| Timber softwood | -0.95 |

## Output Report Format

### Summary Section

```json
{
  "summary": {
    "total_elements": 50,
    "calculated": 43,
    "skipped": 7,
    "total_co2_kg": 31428.13,
    "total_mass_kg": 117266,
    "completeness_pct": 86.0
  }
}
```

### By Category Section

```json
{
  "by_category": {
    "steel": {
      "count": 13,
      "co2_kg": 16346.54,
      "mass_kg": 8836,
      "percentage": 52.0
    },
    "concrete": {
      "count": 8,
      "co2_kg": 10472.36,
      "mass_kg": 89520,
      "percentage": 33.3
    },
    "timber": {
      "count": 4,
      "co2_kg": -64.25,
      "mass_kg": 375,
      "percentage": -0.2
    }
  }
}
```

**Sort by CO2 impact (descending)** - highest impact first

### Detailed Results

```json
{
  "detailed_results": [
    {
      "global_id": "2OrWItJ6zAwBNp0OUxK$Dv",
      "element_name": "Steel Beam W310X60",
      "element_type": "beam",
      "material_category": "steel",
      "volume_m3": 0.0549,
      "mass_kg": 431.00,
      "co2_kg": 797.35,
      "co2_factor_used": 1.85,
      "data_source": "NIBE-generic",
      "calculation_method": "volume_based",
      "confidence": 0.92,
      "warnings": []
    }
  ]
}
```

### Skipped Elements

```json
{
  "skipped_elements": [
    {
      "global_id": "xyz789",
      "name": "Railing R1",
      "element_type": "railing",
      "material_category": null,
      "warnings": ["No volume data - cannot calculate CO2"]
    }
  ]
}
```

## Error Handling

### Missing Volume Data

```json
{
  "calculation_method": "skipped",
  "warnings": ["No volume data - cannot calculate CO2"]
}
```

**Do not estimate volume** - skip and flag for review

### Material Not Found

```json
{
  "calculation_method": "skipped",
  "warnings": ["Material 'ceramic_tile' not found in database"]
}
```

Log the specific material for database expansion

### Zero Volume

```json
{
  "calculation_method": "skipped",
  "warnings": ["Zero volume - cannot calculate CO2"]
}
```

May indicate IFC modeling issue

### Conflicting Data

When material in element doesn't match CO2 factor:
```json
{
  "warnings": ["Used concrete_generic (0.115) for unspecified concrete grade"],
  "confidence": 0.7
}
```

Reduce confidence and document fallback

## Calculation Rules

### Rounding

| Value | Precision | Example |
|-------|-----------|---------|
| Mass | 2 decimals | 431.00 kg |
| CO2 | 2 decimals | 797.35 kg |
| Percentage | 1 decimal | 52.0% |
| Confidence | 2 decimals | 0.92 |

### Aggregation

```
total_co2_kg = SUM(element.co2_kg) for calculated elements
total_mass_kg = SUM(element.mass_kg) for calculated elements
completeness_pct = (calculated / total_elements) × 100
```

### Category Percentage

```
category_percentage = (category_co2_kg / total_co2_kg) × 100
```

Note: Timber may show negative percentage (carbon sink)

## Quality Metrics

### Completeness Targets

| Threshold | Quality | Action |
|-----------|---------|--------|
| >95% | Excellent | Report as-is |
| 85-95% | Good | Note minor gaps |
| 70-85% | Fair | Review skipped elements |
| <70% | Poor | Investigate data quality |

### Confidence Distribution

Aim for:
- >80% of elements with confidence >= 0.7
- <5% of elements with confidence < 0.5
- Average confidence >= 0.75

## Report Summary Format

```
============================================================
CO2 CALCULATION REPORT
============================================================

Input: batch_1_elements.json
Elements: 50 total, 43 calculated (86.0%)

TOTAL CO2 IMPACT: 31,428 kg CO2-eq
Total Mass: 117,266 kg

Breakdown by Material:
  steel        | 13 elements | 16,347 kg CO2 (52.0%)
  concrete     |  8 elements | 10,472 kg CO2 (33.3%)
  masonry      |  8 elements |  2,814 kg CO2 ( 9.0%)
  gypsum       | 10 elements |  1,860 kg CO2 ( 5.9%)
  timber       |  4 elements |    -64 kg CO2 (-0.2%)

Skipped: 7 elements (missing volume or material data)

Output: batch_1_co2_report.json
============================================================
```

---

*CO2 Calculation Guide for buildOS*
*Data source: NIBE Dutch national database*
*Target: Dutch construction industry sustainability reporting*
