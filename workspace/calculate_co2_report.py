#!/usr/bin/env python3
"""
CO2 Impact Calculator for Building Elements
Handles classified elements with graceful null volume handling
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

def load_json(path: str) -> dict:
    """Load JSON file"""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path: str, data: dict) -> None:
    """Save JSON file"""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def find_co2_factor(database: dict, material_category: str, material_subcategory: str) -> Tuple[Optional[float], str, List[str]]:
    """
    Find CO2 factor for material using priority lookup strategy
    Returns: (co2_factor, source, warnings)
    """
    warnings = []

    # Check if material category exists
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
        warnings.append(f"Used {generic_key} as fallback for {material_subcategory}")
        return co2_factor, source, warnings

    # Priority 3: First material in category
    first_key = list(category_data.keys())[0]
    if first_key and first_key != material_subcategory:
        co2_factor = category_data[first_key].get("embodied_co2_per_kg")
        source = category_data[first_key].get("source", "unknown")
        warnings.append(f"Used {first_key} as fallback for {material_subcategory}")
        return co2_factor, source, warnings

    # Priority 4: Skip element
    warnings.append(f"Material '{material_subcategory}' not found in database category '{material_category}'")
    return None, "not_found", warnings

def get_material_density(database: dict, material_category: str, material_subcategory: str) -> Optional[float]:
    """Get material density from database"""
    if material_category not in database.get("materials", {}):
        return None

    category_data = database["materials"][material_category]

    # Try exact match first
    if material_subcategory in category_data:
        return category_data[material_subcategory].get("density_kg_m3")

    # Try generic fallback
    generic_key = f"{material_category}_generic"
    if generic_key in category_data:
        return category_data[generic_key].get("density_kg_m3")

    # Try first key
    first_key = list(category_data.keys())[0]
    if first_key:
        return category_data[first_key].get("density_kg_m3")

    return None

def get_reinforcement_ratio(database: dict, element_type: str) -> float:
    """Get reinforcement ratio for concrete elements"""
    ratios = database.get("reinforcement_ratios", {})

    # Direct match
    if element_type in ratios:
        return ratios[element_type] / 100.0  # Convert percentage to decimal

    # Fuzzy matching for common patterns
    if "structural" in element_type.lower() or "slab" in element_type.lower():
        if "column" in element_type.lower():
            return ratios.get("column", 2.5) / 100.0
        elif "beam" in element_type.lower():
            return ratios.get("beam", 2.8) / 100.0
        elif "slab" in element_type.lower():
            return ratios.get("structural_slab", 2.0) / 100.0
        elif "wall" in element_type.lower():
            return ratios.get("structural_wall", 2.2) / 100.0

    if "footing" in element_type.lower():
        return ratios.get("footing", 1.5) / 100.0

    if "foundation" in element_type.lower():
        if "wall" in element_type.lower():
            return ratios.get("foundation_wall", 1.8) / 100.0
        else:
            return ratios.get("foundation_slab", 1.8) / 100.0

    return 0.0  # No reinforcement

def calculate_element_co2(element: dict, database: dict) -> Tuple[Optional[float], dict]:
    """
    Calculate CO2 for single element
    Returns: (co2_kg, metadata)
    """
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
        "warnings": [],
        "reinforcement_added": False
    }

    # Check for volume
    volume = element.get("volume_m3")
    if volume is None or volume == 0:
        metadata["calculation_method"] = "skipped"
        metadata["warnings"].append("No volume data - cannot calculate CO2")
        return None, metadata

    # Get material info
    material_primary = element.get("material_primary", {})
    material_category = material_primary.get("category")
    material_subcategory = material_primary.get("subcategory")

    if not material_category:
        metadata["calculation_method"] = "skipped"
        metadata["warnings"].append("No material category - cannot calculate CO2")
        return None, metadata

    metadata["material_category"] = material_category

    # Find CO2 factor
    co2_factor, source, factor_warnings = find_co2_factor(database, material_category, material_subcategory)

    if co2_factor is None:
        metadata["calculation_method"] = "skipped"
        metadata["warnings"].extend(factor_warnings)
        return None, metadata

    metadata["co2_factor_used"] = co2_factor
    metadata["data_source"] = source
    metadata["warnings"].extend(factor_warnings)

    # Get density
    density = get_material_density(database, material_category, material_subcategory)
    if density is None:
        metadata["calculation_method"] = "skipped"
        metadata["warnings"].append(f"Cannot determine density for {material_category}")
        return None, metadata

    # Calculate mass
    mass_kg = volume * density
    metadata["mass_kg"] = round(mass_kg, 2)

    # Calculate CO2
    co2_kg = mass_kg * co2_factor

    # Add reinforcement for concrete structural elements
    if material_category == "concrete" and element.get("element_type") in [
        "column", "beam", "slab", "slab_structural", "structural_wall", "load_bearing_wall",
        "footing", "foundation_wall", "foundation_slab"
    ]:
        rebar_ratio = get_reinforcement_ratio(database, element.get("element_type"))
        if rebar_ratio > 0:
            steel_co2_factor = 1.65  # reinforcement steel
            rebar_mass = mass_kg * rebar_ratio
            rebar_co2 = rebar_mass * steel_co2_factor
            co2_kg += rebar_co2
            metadata["reinforcement_added"] = True
            metadata["warnings"].append(f"Added {rebar_ratio*100:.1f}% reinforcement ({rebar_mass:.2f} kg steel)")

    metadata["co2_kg"] = round(co2_kg, 2)
    metadata["calculation_method"] = "volume_based"

    return co2_kg, metadata

def aggregate_by_category(results: List[dict]) -> Dict[str, dict]:
    """Aggregate results by material category"""
    by_category = {}

    for result in results:
        if result["calculation_method"] == "skipped":
            continue

        category = result["material_category"]
        if category not in by_category:
            by_category[category] = {
                "count": 0,
                "co2_kg": 0.0,
                "mass_kg": 0.0,
                "elements": []
            }

        by_category[category]["count"] += 1
        by_category[category]["co2_kg"] += result["co2_kg"]
        by_category[category]["mass_kg"] += result["mass_kg"]
        by_category[category]["elements"].append(result["global_id"])

    return by_category

def generate_report(
    elements: List[dict],
    database: dict,
    input_file: str
) -> dict:
    """Generate CO2 report"""

    detailed_results = []
    skipped_elements = []
    total_co2 = 0.0
    total_mass = 0.0
    calculated_count = 0

    # Calculate CO2 for each element
    for element in elements:
        co2_kg, metadata = calculate_element_co2(element, database)

        if metadata["calculation_method"] == "skipped":
            skipped_elements.append(metadata)
        else:
            detailed_results.append(metadata)
            total_co2 += co2_kg
            total_mass += metadata["mass_kg"]
            calculated_count += 1

    # Sort detailed results by CO2 impact (descending)
    detailed_results.sort(key=lambda x: x["co2_kg"], reverse=True)

    # Aggregate by category
    by_category = aggregate_by_category(detailed_results)

    # Calculate percentages and sort
    total_co2_for_pct = sum(cat["co2_kg"] for cat in by_category.values())
    if total_co2_for_pct != 0:
        for category in by_category.values():
            category["percentage"] = round((category["co2_kg"] / total_co2_for_pct) * 100, 1)
    else:
        for category in by_category.values():
            category["percentage"] = 0.0

    # Sort by CO2 impact
    by_category_sorted = dict(sorted(
        by_category.items(),
        key=lambda x: x[1]["co2_kg"],
        reverse=True
    ))

    # Build summary
    total_elements = len(elements)
    completeness_pct = (calculated_count / total_elements * 100) if total_elements > 0 else 0

    summary = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_file,
        "database_version": database.get("version", "unknown"),
        "total_elements": total_elements,
        "calculated": calculated_count,
        "skipped": len(skipped_elements),
        "total_co2_kg": round(total_co2, 2),
        "total_mass_kg": round(total_mass, 2),
        "completeness_pct": round(completeness_pct, 1)
    }

    # Build full report
    report = {
        "summary": summary,
        "by_category": by_category_sorted,
        "detailed_results": detailed_results,
        "skipped_elements": skipped_elements
    }

    return report

def print_summary(report: dict, input_file: str, output_file: str) -> None:
    """Print human-readable summary"""
    summary = report["summary"]
    by_category = report["by_category"]

    print("\n" + "="*60)
    print("CO2 CALCULATION REPORT")
    print("="*60)
    print()
    print(f"Input: {Path(input_file).name}")
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
    print(f"Output: {Path(output_file).name}")
    print("="*60)
    print()

def main():
    if len(sys.argv) < 4:
        print("Usage: python calculate_co2_report.py <classified_file> <database_file> <output_file>")
        sys.exit(1)

    classified_file = sys.argv[1]
    database_file = sys.argv[2]
    output_file = sys.argv[3]

    # Load data
    print(f"Loading classified elements from {classified_file}...")
    classified_data = load_json(classified_file)
    elements = classified_data.get("elements", [])
    print(f"  Found {len(elements)} elements")

    print(f"Loading database from {database_file}...")
    database = load_json(database_file)
    print(f"  Database version: {database.get('version', 'unknown')}")

    # Generate report
    print("Calculating CO2 impacts...")
    report = generate_report(elements, database, classified_file)

    # Save report
    print(f"Saving report to {output_file}...")
    save_json(output_file, report)

    # Print summary
    print_summary(report, classified_file, output_file)

    print("CO2 calculation complete!")

if __name__ == "__main__":
    main()
