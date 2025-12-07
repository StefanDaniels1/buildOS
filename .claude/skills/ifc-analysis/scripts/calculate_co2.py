#!/usr/bin/env python3
"""
CO2 Calculation CLI Tool for buildOS
Calculates embodied CO2 for classified building elements using NIBE database.

Usage:
    python calculate_co2.py <classified_elements.json> <output_report.json> [database.json]

Example:
    python calculate_co2.py batch_1_elements.json batch_1_co2_report.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# Default database path (relative to this script)
DEFAULT_DATABASE = Path(__file__).parent.parent / "reference" / "durability_database.json"


def load_database(database_path: str = None) -> dict:
    """Load the durability database."""
    db_path = Path(database_path) if database_path else DEFAULT_DATABASE

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_material_data(database: dict, category: str, subcategory: str = None) -> dict:
    """
    Look up material data from database.

    Priority:
    1. Exact subcategory match
    2. Generic fallback for category
    3. First material in category
    """
    materials = database.get("materials", {})
    category_data = materials.get(category, {})

    if not category_data:
        return None

    # Try exact subcategory match
    if subcategory and subcategory in category_data:
        return category_data[subcategory]

    # Try generic fallback
    generic_key = f"{category}_generic"
    if generic_key in category_data:
        return category_data[generic_key]

    # Use first material in category
    first_key = next(iter(category_data.keys()), None)
    if first_key:
        return category_data[first_key]

    return None


def calculate_co2(classified_file: str, output_file: str, database_path: str = None) -> dict:
    """
    Calculate CO2 impact for classified elements.

    Args:
        classified_file: Path to classified elements JSON
        output_file: Path to save CO2 report
        database_path: Optional path to durability database

    Returns:
        Dictionary with calculation results
    """
    try:
        # Load database
        database = load_database(database_path)
        reinforcement_ratios = database.get("reinforcement_ratios", {})
        steel_rebar_data = get_material_data(database, "steel", "steel_reinforcement")
        steel_rebar_co2 = steel_rebar_data["embodied_co2_per_kg"] if steel_rebar_data else 1.65

        # Load classified elements
        with open(classified_file, 'r', encoding='utf-8') as f:
            elements = json.load(f)

        # Ensure elements is a list
        if isinstance(elements, dict):
            elements = elements.get("elements", [])

        # Process each element
        detailed_results = []
        skipped_elements = []
        category_totals = defaultdict(lambda: {"count": 0, "co2_kg": 0.0, "mass_kg": 0.0})

        for element in elements:
            global_id = element.get("global_id", "unknown")
            element_name = element.get("name", "Unknown Element")
            element_type = element.get("element_type", "other")
            material_primary = element.get("material_primary", {})
            volume_m3 = element.get("volume_m3")
            confidence = element.get("confidence", 0.0)

            # Skip if no volume
            if not volume_m3 or volume_m3 <= 0:
                skipped_elements.append({
                    "global_id": global_id,
                    "name": element_name,
                    "element_type": element_type,
                    "warnings": ["No volume data - cannot calculate CO2"]
                })
                continue

            # Get material data
            category = material_primary.get("category", "")
            subcategory = material_primary.get("subcategory", "")

            material_data = get_material_data(database, category, subcategory)

            if not material_data:
                skipped_elements.append({
                    "global_id": global_id,
                    "name": element_name,
                    "element_type": element_type,
                    "material_category": category,
                    "warnings": [f"Material '{category}/{subcategory}' not found in database"]
                })
                continue

            # Calculate mass and CO2
            density = material_data["density_kg_m3"]
            co2_factor = material_data["embodied_co2_per_kg"]
            data_source = material_data.get("source", "NIBE-generic")

            mass_kg = round(volume_m3 * density, 2)
            co2_kg = round(mass_kg * co2_factor, 2)
            warnings = []

            # Add reinforcement for concrete elements
            if category == "concrete" and element_type in reinforcement_ratios:
                ratio = reinforcement_ratios[element_type]
                rebar_mass_kg = mass_kg * (ratio / 100)
                rebar_co2_kg = rebar_mass_kg * steel_rebar_co2
                co2_kg = round(co2_kg + rebar_co2_kg, 2)
                warnings.append(f"Added {ratio}% reinforcement ({rebar_mass_kg:.1f} kg steel)")

            # Record result
            result = {
                "global_id": global_id,
                "element_name": element_name,
                "element_type": element_type,
                "material_category": category,
                "volume_m3": volume_m3,
                "mass_kg": mass_kg,
                "co2_kg": co2_kg,
                "co2_factor_used": co2_factor,
                "data_source": data_source,
                "calculation_method": "volume_based",
                "confidence": confidence,
                "warnings": warnings
            }

            detailed_results.append(result)

            # Update category totals
            category_totals[category]["count"] += 1
            category_totals[category]["co2_kg"] += co2_kg
            category_totals[category]["mass_kg"] += mass_kg

        # Calculate summary
        total_co2 = sum(r["co2_kg"] for r in detailed_results)
        total_mass = sum(r["mass_kg"] for r in detailed_results)
        calculated = len(detailed_results)
        skipped = len(skipped_elements)
        total = calculated + skipped

        # Calculate percentages for categories
        by_category = {}
        for cat, data in sorted(category_totals.items(), key=lambda x: -x[1]["co2_kg"]):
            by_category[cat] = {
                "count": data["count"],
                "co2_kg": round(data["co2_kg"], 2),
                "mass_kg": round(data["mass_kg"], 2),
                "percentage": round((data["co2_kg"] / total_co2 * 100) if total_co2 else 0, 1)
            }

        # Prepare output
        output_data = {
            "metadata": {
                "source_file": str(Path(classified_file).name),
                "calculation_date": datetime.now().strftime("%Y-%m-%d"),
                "database_version": database.get("version", "1.0.0"),
                "database_source": database.get("source", "NIBE (Dutch national database)")
            },
            "summary": {
                "total_elements": total,
                "calculated": calculated,
                "skipped": skipped,
                "total_co2_kg": round(total_co2, 2),
                "total_mass_kg": round(total_mass, 2),
                "completeness_pct": round((calculated / total * 100) if total else 0, 1)
            },
            "by_category": by_category,
            "detailed_results": detailed_results,
            "skipped_elements": skipped_elements
        }

        # Save output
        output_path_obj = Path(output_file)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "output_file": str(output_file),
            "summary": output_data["summary"],
            "by_category": by_category
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python calculate_co2.py <classified_elements.json> <output_report.json> [database.json]")
        print("\nExample:")
        print("  python calculate_co2.py batch_1_elements.json batch_1_co2_report.json")
        sys.exit(1)

    classified_file = sys.argv[1]
    output_file = sys.argv[2]
    database_path = sys.argv[3] if len(sys.argv) > 3 else None

    if not Path(classified_file).exists():
        print(f"Error: Classified elements file not found: {classified_file}")
        sys.exit(1)

    print(f"\nCalculating CO2 impact for: {classified_file}")
    print(f"Output: {output_file}")

    result = calculate_co2(classified_file, output_file, database_path)

    if result["success"]:
        summary = result["summary"]
        by_category = result["by_category"]

        print(f"\n{'='*60}")
        print("CO2 CALCULATION REPORT")
        print(f"{'='*60}\n")

        print(f"Input: {Path(classified_file).name}")
        print(f"Elements: {summary['total_elements']} total, {summary['calculated']} calculated ({summary['completeness_pct']}%)\n")

        print(f"TOTAL CO2 IMPACT: {summary['total_co2_kg']:,.0f} kg CO2-eq")
        print(f"Total Mass: {summary['total_mass_kg']:,.0f} kg\n")

        print("Breakdown by Material:")
        for cat, data in by_category.items():
            print(f"  {cat:<12} | {data['count']:>3} elements | {data['co2_kg']:>10,.0f} kg CO2 ({data['percentage']:>5.1f}%)")

        if summary['skipped'] > 0:
            print(f"\nSkipped: {summary['skipped']} elements (missing volume or material data)")

        print(f"\nOutput: {result['output_file']}")
        print(f"{'='*60}\n")
    else:
        print(f"\nError: {result['error']}")
        if "traceback" in result:
            print(result["traceback"])
        sys.exit(1)


if __name__ == "__main__":
    main()
