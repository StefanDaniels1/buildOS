#!/usr/bin/env python3
"""Test and calculate CO2 impact"""

import json
from pathlib import Path
from datetime import datetime

# File paths
classified_file = '/app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json'
database_file = '/app/.claude/skills/ifc-analysis/reference/durability_database.json'
output_file = '/app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json'

print("Checking files...")
print(f"  Classified: {Path(classified_file).exists()}")
print(f"  Database: {Path(database_file).exists()}")

# Load data
with open(classified_file, 'r') as f:
    classified_data = json.load(f)

with open(database_file, 'r') as f:
    database = json.load(f)

elements = classified_data.get("elements", [])
print(f"\nLoaded {len(elements)} elements")

# Count null volumes
null_volumes = [e for e in elements if e.get("volume_m3") is None]
print(f"Elements with null volume: {len(null_volumes)}")
print(f"Elements with data: {len(elements) - len(null_volumes)}")

# Quick sample of elements
print("\nSample elements (first 3):")
for elem in elements[:3]:
    print(f"  {elem['name']}: volume={elem.get('volume_m3')}, material={elem.get('material_primary', {}).get('category')}")

print("\nSample of null volume elements:")
for elem in null_volumes[:3]:
    print(f"  {elem['name']}: material={elem.get('material_primary', {}).get('category')}")

# Now run the CO2 calculation
print("\n" + "="*60)
print("RUNNING CO2 CALCULATION")
print("="*60 + "\n")

# Helper functions
def find_co2_factor(material_category, material_subcategory):
    """Find CO2 factor for material"""
    if material_category not in database.get("materials", {}):
        return None, "not_found", [f"Material category '{material_category}' not found"]

    category_data = database["materials"][material_category]

    # Priority 1: Exact match
    if material_subcategory in category_data:
        co2_factor = category_data[material_subcategory].get("embodied_co2_per_kg")
        source = category_data[material_subcategory].get("source", "unknown")
        return co2_factor, source, []

    # Priority 2: Generic
    generic_key = f"{material_category}_generic"
    if generic_key in category_data:
        co2_factor = category_data[generic_key].get("embodied_co2_per_kg")
        source = category_data[generic_key].get("source", "unknown")
        return co2_factor, source, [f"Used {generic_key} as fallback"]

    # Priority 3: First
    first_key = list(category_data.keys())[0]
    if first_key:
        co2_factor = category_data[first_key].get("embodied_co2_per_kg")
        source = category_data[first_key].get("source", "unknown")
        return co2_factor, source, [f"Used {first_key} as fallback"]

    return None, "not_found", [f"Material '{material_subcategory}' not found"]

def get_density(material_category, material_subcategory):
    """Get density from database"""
    if material_category not in database.get("materials", {}):
        return None

    category_data = database["materials"][material_category]

    if material_subcategory in category_data:
        return category_data[material_subcategory].get("density_kg_m3")

    generic_key = f"{material_category}_generic"
    if generic_key in category_data:
        return category_data[generic_key].get("density_kg_m3")

    first_key = list(category_data.keys())[0]
    if first_key:
        return category_data[first_key].get("density_kg_m3")

    return None

def get_reinforcement_ratio(element_type):
    """Get reinforcement ratio"""
    ratios = database.get("reinforcement_ratios", {})

    if element_type in ratios:
        return ratios[element_type] / 100.0

    if "slab" in element_type.lower():
        return ratios.get("structural_slab", 2.0) / 100.0
    elif "column" in element_type.lower():
        return ratios.get("column", 2.5) / 100.0
    elif "beam" in element_type.lower():
        return ratios.get("beam", 2.8) / 100.0
    elif "footing" in element_type.lower():
        return ratios.get("footing", 1.5) / 100.0
    elif "wall" in element_type.lower():
        if "foundation" in element_type.lower():
            return ratios.get("foundation_wall", 1.8) / 100.0
        else:
            return ratios.get("structural_wall", 2.2) / 100.0

    return 0.0

# Process elements
detailed_results = []
skipped_elements = []
total_co2 = 0.0
total_mass = 0.0
calculated_count = 0

for element in elements:
    metadata = {
        "global_id": element.get("global_id"),
        "element_name": element.get("name"),
        "element_type": element.get("element_type"),
        "material_category": None,
        "volume_m3": element.get("volume_m3"),
        "mass_kg": None,
        "co2_kg": None,
        "co2_factor_used": None,
        "data_source": None,
        "calculation_method": None,
        "confidence": element.get("confidence", 0.5),
        "warnings": []
    }

    volume = element.get("volume_m3")

    # Skip if no volume
    if volume is None or volume == 0:
        metadata["calculation_method"] = "skipped"
        metadata["warnings"].append("No volume data - cannot calculate CO2")
        skipped_elements.append(metadata)
        continue

    # Get material
    material_primary = element.get("material_primary", {})
    material_category = material_primary.get("category")
    material_subcategory = material_primary.get("subcategory")

    if not material_category:
        metadata["calculation_method"] = "skipped"
        metadata["warnings"].append("No material category")
        skipped_elements.append(metadata)
        continue

    metadata["material_category"] = material_category

    # Get CO2 factor
    co2_factor, source, warnings = find_co2_factor(material_category, material_subcategory)

    if co2_factor is None:
        metadata["calculation_method"] = "skipped"
        metadata["warnings"].extend(warnings)
        skipped_elements.append(metadata)
        continue

    metadata["co2_factor_used"] = co2_factor
    metadata["data_source"] = source
    metadata["warnings"].extend(warnings)

    # Get density
    density = get_density(material_category, material_subcategory)
    if density is None:
        metadata["calculation_method"] = "skipped"
        metadata["warnings"].append(f"Cannot determine density")
        skipped_elements.append(metadata)
        continue

    # Calculate mass
    mass_kg = volume * density
    metadata["mass_kg"] = round(mass_kg, 2)

    # Calculate CO2
    co2_kg = mass_kg * co2_factor

    # Add reinforcement for concrete
    if material_category == "concrete" and element.get("element_type") in [
        "column", "beam", "slab", "slab_structural", "structural_wall", "load_bearing_wall",
        "footing", "foundation_wall", "foundation_slab"
    ]:
        rebar_ratio = get_reinforcement_ratio(element.get("element_type"))
        if rebar_ratio > 0:
            rebar_mass = mass_kg * rebar_ratio
            rebar_co2 = rebar_mass * 1.65  # steel reinforcement factor
            co2_kg += rebar_co2
            metadata["warnings"].append(f"Added {rebar_ratio*100:.1f}% reinforcement")

    metadata["co2_kg"] = round(co2_kg, 2)
    metadata["calculation_method"] = "volume_based"

    detailed_results.append(metadata)
    total_co2 += co2_kg
    total_mass += metadata["mass_kg"]
    calculated_count += 1

# Sort by CO2
detailed_results.sort(key=lambda x: x["co2_kg"], reverse=True)

# Aggregate by category
by_category = {}
for result in detailed_results:
    cat = result["material_category"]
    if cat not in by_category:
        by_category[cat] = {
            "count": 0,
            "co2_kg": 0.0,
            "mass_kg": 0.0
        }
    by_category[cat]["count"] += 1
    by_category[cat]["co2_kg"] += result["co2_kg"]
    by_category[cat]["mass_kg"] += result["mass_kg"]

# Calculate percentages
total_co2_for_pct = sum(cat["co2_kg"] for cat in by_category.values())
for category in by_category.values():
    if total_co2_for_pct != 0:
        category["percentage"] = round((category["co2_kg"] / total_co2_for_pct) * 100, 1)
    else:
        category["percentage"] = 0.0

# Sort by CO2
by_category = dict(sorted(by_category.items(), key=lambda x: x[1]["co2_kg"], reverse=True))

# Build report
summary = {
    "timestamp": datetime.now().isoformat(),
    "input_file": classified_file,
    "database_version": database.get("version", "unknown"),
    "total_elements": len(elements),
    "calculated": calculated_count,
    "skipped": len(skipped_elements),
    "total_co2_kg": round(total_co2, 2),
    "total_mass_kg": round(total_mass, 2),
    "completeness_pct": round((calculated_count / len(elements) * 100), 1) if elements else 0
}

report = {
    "summary": summary,
    "by_category": by_category,
    "detailed_results": detailed_results,
    "skipped_elements": skipped_elements
}

# Save
with open(output_file, 'w') as f:
    json.dump(report, f, indent=2)

# Print summary
print(f"Input: {Path(classified_file).name}")
print(f"Elements: {summary['total_elements']} total, {summary['calculated']} calculated ({summary['completeness_pct']:.1f}%)")
print()
print(f"TOTAL CO2 IMPACT: {summary['total_co2_kg']:,.2f} kg CO2-eq")
print(f"Total Mass: {summary['total_mass_kg']:,.2f} kg")
print()
print("Breakdown by Material:")
for category, data in by_category.items():
    pct = data["percentage"]
    print(f"  {category:16} | {data['count']:2} elements | {data['co2_kg']:10,.2f} kg CO2 ({pct:6.1f}%)")

if summary["skipped"] > 0:
    print()
    print(f"Skipped: {summary['skipped']} elements")

print()
print(f"Output: {Path(output_file).name}")
print("="*60)

print("\nCO2 calculation complete!")
print(f"Report saved to: {output_file}")
