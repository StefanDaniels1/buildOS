#!/usr/bin/env python3
"""
Comprehensive CO2 Calculation for Building Elements
Follows CO2-CALCULATION.md specification exactly
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
CLASSIFIED_FILE = '/app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json'
DATABASE_FILE = '/app/.claude/skills/ifc-analysis/reference/durability_database.json'
OUTPUT_FILE = '/app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json'

def load_files():
    """Load JSON files"""
    with open(CLASSIFIED_FILE, 'r') as f:
        classified = json.load(f)
    with open(DATABASE_FILE, 'r') as f:
        database = json.load(f)
    return classified, database

def find_co2_factor(database, material_category, material_subcategory):
    """
    Priority lookup strategy per CO2-CALCULATION.md:
    1. Exact subcategory match
    2. Generic fallback
    3. First material in category
    4. Skip element
    """
    warnings = []

    if material_category not in database.get("materials", {}):
        warnings.append(f"Material category '{material_category}' not found in database")
        return None, "not_found", warnings

    category_data = database["materials"][material_category]

    # Priority 1: Exact subcategory match
    if material_subcategory in category_data:
        co2_factor = category_data[material_subcategory].get("embodied_co2_per_kg")
        source = category_data[material_subcategory].get("source", "unknown")
        return co2_factor, source, warnings

    # Priority 2: Generic fallback in category
    generic_key = f"{material_category}_generic"
    if generic_key in category_data:
        co2_factor = category_data[generic_key].get("embodied_co2_per_kg")
        source = category_data[generic_key].get("source", "unknown")
        warnings.append(f"Used {generic_key} (0.115) for unspecified {material_category} grade")
        return co2_factor, source, warnings

    # Priority 3: First material in category
    first_key = list(category_data.keys())[0] if category_data else None
    if first_key:
        co2_factor = category_data[first_key].get("embodied_co2_per_kg")
        source = category_data[first_key].get("source", "unknown")
        warnings.append(f"Used {first_key} as fallback for {material_subcategory}")
        return co2_factor, source, warnings

    # Priority 4: Skip element
    warnings.append(f"Material '{material_subcategory}' not found in database category '{material_category}'")
    return None, "not_found", warnings

def get_material_density(database, material_category, material_subcategory):
    """Get material density from database"""
    if material_category not in database.get("materials", {}):
        return None

    category_data = database["materials"][material_category]

    if material_subcategory in category_data:
        return category_data[material_subcategory].get("density_kg_m3")

    generic_key = f"{material_category}_generic"
    if generic_key in category_data:
        return category_data[generic_key].get("density_kg_m3")

    first_key = list(category_data.keys())[0] if category_data else None
    if first_key:
        return category_data[first_key].get("density_kg_m3")

    return None

def get_reinforcement_ratio(database, element_type):
    """Get reinforcement ratio for concrete elements"""
    ratios = database.get("reinforcement_ratios", {})

    # Direct match first
    if element_type in ratios:
        return ratios[element_type] / 100.0

    # Fuzzy matching for structural elements
    if "column" in element_type.lower():
        return ratios.get("column", 2.5) / 100.0
    elif "beam" in element_type.lower():
        return ratios.get("beam", 2.8) / 100.0
    elif "slab" in element_type.lower() or "structural" in element_type.lower():
        return ratios.get("structural_slab", 2.0) / 100.0
    elif "footing" in element_type.lower():
        return ratios.get("footing", 1.5) / 100.0
    elif "wall" in element_type.lower():
        if "foundation" in element_type.lower():
            return ratios.get("foundation_wall", 1.8) / 100.0
        else:
            return ratios.get("structural_wall", 2.2) / 100.0

    return 0.0

def should_add_reinforcement(element_type):
    """Check if element should have reinforcement"""
    reinforceable_types = [
        "column", "beam", "slab", "slab_structural", "structural_wall",
        "load_bearing_wall", "footing", "foundation_wall", "foundation_slab"
    ]
    return any(rtype in element_type.lower() for rtype in reinforceable_types)

def calculate_co2_for_element(element, database):
    """
    Calculate CO2 for single element per CO2-CALCULATION.md formula:
    mass_kg = volume_m3 × density_kg_m3
    co2_kg = mass_kg × embodied_co2_per_kg
    """
    result = {
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
        "confidence": round(element.get("confidence", 0.5), 2),
        "warnings": []
    }

    volume = element.get("volume_m3")

    # Handle null/zero volume
    if volume is None or volume == 0:
        result["calculation_method"] = "skipped"
        result["warnings"].append("No volume data - cannot calculate CO2")
        return None, result

    # Get material info
    material_primary = element.get("material_primary", {})
    material_category = material_primary.get("category")
    material_subcategory = material_primary.get("subcategory")

    if not material_category:
        result["calculation_method"] = "skipped"
        result["warnings"].append("No material category - cannot calculate CO2")
        return None, result

    result["material_category"] = material_category

    # Lookup CO2 factor
    co2_factor, source, factor_warnings = find_co2_factor(database, material_category, material_subcategory)

    if co2_factor is None:
        result["calculation_method"] = "skipped"
        result["warnings"].extend(factor_warnings)
        return None, result

    result["co2_factor_used"] = co2_factor
    result["data_source"] = source
    result["warnings"].extend(factor_warnings)

    # Get density
    density = get_material_density(database, material_category, material_subcategory)
    if density is None:
        result["calculation_method"] = "skipped"
        result["warnings"].append("Cannot determine material density")
        return None, result

    # Calculate mass: mass_kg = volume × density
    mass_kg = volume * density
    result["mass_kg"] = round(mass_kg, 2)

    # Calculate CO2: co2_kg = mass × co2_factor
    co2_kg = mass_kg * co2_factor

    # Add reinforcement for concrete structural elements
    if material_category == "concrete" and should_add_reinforcement(element.get("element_type", "")):
        rebar_ratio = get_reinforcement_ratio(database, element.get("element_type", ""))
        if rebar_ratio > 0:
            steel_co2_factor = 1.65  # From database
            rebar_mass_kg = mass_kg * rebar_ratio
            rebar_co2_kg = rebar_mass_kg * steel_co2_factor
            co2_kg += rebar_co2_kg
            result["warnings"].append(f"Added {rebar_ratio*100:.1f}% reinforcement ({rebar_mass_kg:.2f} kg steel)")

    result["co2_kg"] = round(co2_kg, 2)
    result["calculation_method"] = "volume_based"

    return co2_kg, result

def aggregate_results(detailed_results):
    """Aggregate results by material category"""
    by_category = defaultdict(lambda: {
        "count": 0,
        "co2_kg": 0.0,
        "mass_kg": 0.0,
        "elements": []
    })

    for result in detailed_results:
        category = result["material_category"]
        by_category[category]["count"] += 1
        by_category[category]["co2_kg"] += result["co2_kg"]
        by_category[category]["mass_kg"] += result["mass_kg"]
        by_category[category]["elements"].append(result["global_id"])

    return dict(by_category)

def main():
    print("="*70)
    print("BUILDING ELEMENTS CO2 IMPACT CALCULATOR")
    print("="*70)
    print()

    # Load data
    print(f"Loading classified elements from {Path(CLASSIFIED_FILE).name}...")
    classified, database = load_files()
    elements = classified.get("elements", [])
    print(f"  Found {len(elements)} elements")
    print(f"  Database version: {database.get('version', 'unknown')}")

    # Count null volumes
    null_volume_count = len([e for e in elements if e.get("volume_m3") is None])
    print(f"  Elements with null volume: {null_volume_count}")
    print()

    # Calculate CO2 for each element
    print("Calculating CO2 impacts...")
    detailed_results = []
    skipped_elements = []
    total_co2 = 0.0
    total_mass = 0.0

    for i, element in enumerate(elements):
        co2_kg, result = calculate_co2_for_element(element, database)

        if result["calculation_method"] == "skipped":
            skipped_elements.append(result)
        else:
            detailed_results.append(result)
            total_co2 += co2_kg
            total_mass += result["mass_kg"]

        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(elements)} elements...")

    print(f"  Complete. Calculated: {len(detailed_results)}, Skipped: {len(skipped_elements)}")
    print()

    # Sort detailed results by CO2 (descending)
    detailed_results.sort(key=lambda x: x["co2_kg"], reverse=True)

    # Aggregate by category
    print("Aggregating by material category...")
    by_category = aggregate_results(detailed_results)

    # Calculate percentages
    for category in by_category.values():
        if total_co2 != 0:
            category["percentage"] = round((category["co2_kg"] / total_co2) * 100, 1)
        else:
            category["percentage"] = 0.0

    # Sort by CO2 (descending)
    by_category = dict(sorted(
        by_category.items(),
        key=lambda x: x[1]["co2_kg"],
        reverse=True
    ))

    # Build summary
    completeness_pct = (len(detailed_results) / len(elements) * 100) if elements else 0

    summary = {
        "timestamp": datetime.now().isoformat(),
        "input_file": Path(CLASSIFIED_FILE).name,
        "database_version": database.get("version", "unknown"),
        "total_elements": len(elements),
        "calculated": len(detailed_results),
        "skipped": len(skipped_elements),
        "total_co2_kg": round(total_co2, 2),
        "total_mass_kg": round(total_mass, 2),
        "completeness_pct": round(completeness_pct, 1)
    }

    # Build full report
    report = {
        "summary": summary,
        "by_category": by_category,
        "detailed_results": detailed_results,
        "skipped_elements": skipped_elements
    }

    # Save report
    print(f"Saving report to {Path(OUTPUT_FILE).name}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    print()

    # Print summary
    print("="*70)
    print("CO2 CALCULATION REPORT")
    print("="*70)
    print()
    print(f"Input: {Path(CLASSIFIED_FILE).name}")
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
        print(f"Skipped: {summary['skipped']} elements (missing volume or material data)")
        print()
        print("Top skipped elements:")
        for elem in skipped_elements[:5]:
            reason = elem["warnings"][0] if elem["warnings"] else "Unknown"
            print(f"  {elem['element_name'][:50]}: {reason}")
        if len(skipped_elements) > 5:
            print(f"  ... and {len(skipped_elements) - 5} more")

    print()
    print(f"Output: {Path(OUTPUT_FILE).name}")
    print("="*70)
    print()
    print("Report generation complete!")

if __name__ == "__main__":
    main()
