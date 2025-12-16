#!/usr/bin/env python3
"""Inline CO2 calculation - direct execution"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ===== CONFIGURATION =====
CLASSIFIED_FILE = '/app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json'
DATABASE_FILE = '/app/.claude/skills/ifc-analysis/reference/durability_database.json'
OUTPUT_FILE = '/app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json'

# ===== LOAD FILES =====
with open(CLASSIFIED_FILE, 'r') as f:
    classified = json.load(f)
with open(DATABASE_FILE, 'r') as f:
    database = json.load(f)

elements = classified.get("elements", [])

print(f"Loaded {len(elements)} elements")
print(f"Database version: {database.get('version', 'unknown')}")

# ===== HELPER FUNCTIONS =====

def find_co2_factor(mat_cat, mat_subcat):
    """Find CO2 factor with priority lookup"""
    w = []

    if mat_cat not in database.get("materials", {}):
        w.append(f"Material category '{mat_cat}' not found")
        return None, "not_found", w

    cat_data = database["materials"][mat_cat]

    # 1. Exact match
    if mat_subcat in cat_data:
        return cat_data[mat_subcat].get("embodied_co2_per_kg"), cat_data[mat_subcat].get("source"), w

    # 2. Generic
    gen_key = f"{mat_cat}_generic"
    if gen_key in cat_data:
        return cat_data[gen_key].get("embodied_co2_per_kg"), cat_data[gen_key].get("source"), w

    # 3. First key
    first = list(cat_data.keys())[0] if cat_data else None
    if first:
        w.append(f"Used {first} as fallback")
        return cat_data[first].get("embodied_co2_per_kg"), cat_data[first].get("source"), w

    w.append(f"Material '{mat_subcat}' not found")
    return None, "not_found", w

def get_density(mat_cat, mat_subcat):
    """Get material density"""
    if mat_cat not in database.get("materials", {}):
        return None

    cat_data = database["materials"][mat_cat]

    if mat_subcat in cat_data:
        return cat_data[mat_subcat].get("density_kg_m3")

    gen_key = f"{mat_cat}_generic"
    if gen_key in cat_data:
        return cat_data[gen_key].get("density_kg_m3")

    first = list(cat_data.keys())[0] if cat_data else None
    return cat_data[first].get("density_kg_m3") if first else None

def get_rebar_ratio(et):
    """Get reinforcement ratio"""
    ratios = database.get("reinforcement_ratios", {})

    if et in ratios:
        return ratios[et] / 100.0

    if "column" in et.lower():
        return ratios.get("column", 2.5) / 100.0
    elif "beam" in et.lower():
        return ratios.get("beam", 2.8) / 100.0
    elif "slab" in et.lower() or "structural" in et.lower():
        return ratios.get("structural_slab", 2.0) / 100.0
    elif "footing" in et.lower():
        return ratios.get("footing", 1.5) / 100.0
    elif "wall" in et.lower():
        if "foundation" in et.lower():
            return ratios.get("foundation_wall", 1.8) / 100.0
        return ratios.get("structural_wall", 2.2) / 100.0

    return 0.0

def should_reinforce(et):
    """Check if element needs reinforcement"""
    types = ["column", "beam", "slab", "structural", "footing", "wall"]
    return any(t in et.lower() for t in types)

# ===== CALCULATE =====

detailed = []
skipped = []
tot_co2 = 0.0
tot_mass = 0.0

for elem in elements:
    res = {
        "global_id": elem.get("global_id"),
        "element_name": elem.get("name"),
        "element_type": elem.get("element_type"),
        "material_category": None,
        "volume_m3": elem.get("volume_m3"),
        "mass_kg": None,
        "co2_kg": None,
        "co2_factor_used": None,
        "data_source": None,
        "calculation_method": None,
        "confidence": round(elem.get("confidence", 0.5), 2),
        "warnings": []
    }

    vol = elem.get("volume_m3")

    # Check volume
    if vol is None or vol == 0:
        res["calculation_method"] = "skipped"
        res["warnings"].append("No volume data - cannot calculate CO2")
        skipped.append(res)
        continue

    # Get material
    mat_p = elem.get("material_primary", {})
    mat_cat = mat_p.get("category")
    mat_subcat = mat_p.get("subcategory")

    if not mat_cat:
        res["calculation_method"] = "skipped"
        res["warnings"].append("No material category")
        skipped.append(res)
        continue

    res["material_category"] = mat_cat

    # Get CO2 factor
    co2_fac, src, fac_w = find_co2_factor(mat_cat, mat_subcat)

    if co2_fac is None:
        res["calculation_method"] = "skipped"
        res["warnings"].extend(fac_w)
        skipped.append(res)
        continue

    res["co2_factor_used"] = co2_fac
    res["data_source"] = src
    res["warnings"].extend(fac_w)

    # Get density
    den = get_density(mat_cat, mat_subcat)
    if den is None:
        res["calculation_method"] = "skipped"
        res["warnings"].append("Cannot determine density")
        skipped.append(res)
        continue

    # Calculate mass
    mass = vol * den
    res["mass_kg"] = round(mass, 2)

    # Calculate CO2
    co2 = mass * co2_fac

    # Add reinforcement
    if mat_cat == "concrete" and should_reinforce(elem.get("element_type", "")):
        ratio = get_rebar_ratio(elem.get("element_type", ""))
        if ratio > 0:
            rebar_mass = mass * ratio
            rebar_co2 = rebar_mass * 1.65
            co2 += rebar_co2
            res["warnings"].append(f"Added {ratio*100:.1f}% reinforcement")

    res["co2_kg"] = round(co2, 2)
    res["calculation_method"] = "volume_based"

    detailed.append(res)
    tot_co2 += co2
    tot_mass += res["mass_kg"]

# Sort by CO2
detailed.sort(key=lambda x: x["co2_kg"], reverse=True)

# Aggregate
by_cat = defaultdict(lambda: {"count": 0, "co2_kg": 0.0, "mass_kg": 0.0})

for res in detailed:
    cat = res["material_category"]
    by_cat[cat]["count"] += 1
    by_cat[cat]["co2_kg"] += res["co2_kg"]
    by_cat[cat]["mass_kg"] += res["mass_kg"]

# Calculate percentages
for cat_data in by_cat.values():
    cat_data["percentage"] = round((cat_data["co2_kg"] / tot_co2 * 100), 1) if tot_co2 != 0 else 0.0

by_cat = dict(sorted(by_cat.items(), key=lambda x: x[1]["co2_kg"], reverse=True))

# Summary
comp = round((len(detailed) / len(elements) * 100), 1) if elements else 0

summary = {
    "timestamp": datetime.now().isoformat(),
    "input_file": Path(CLASSIFIED_FILE).name,
    "database_version": database.get("version", "unknown"),
    "total_elements": len(elements),
    "calculated": len(detailed),
    "skipped": len(skipped),
    "total_co2_kg": round(tot_co2, 2),
    "total_mass_kg": round(tot_mass, 2),
    "completeness_pct": comp
}

# Report
report = {
    "summary": summary,
    "by_category": by_cat,
    "detailed_results": detailed,
    "skipped_elements": skipped
}

# Save
with open(OUTPUT_FILE, 'w') as f:
    json.dump(report, f, indent=2)

# Print
print("\n" + "="*70)
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
for cat, data in by_cat.items():
    pct = data["percentage"]
    print(f"  {cat:16} | {data['count']:2} elements | {data['co2_kg']:10,.2f} kg CO2 ({pct:6.1f}%)")

if summary["skipped"] > 0:
    print()
    print(f"Skipped: {summary['skipped']} elements (missing volume or material data)")

print()
print(f"Output: {Path(OUTPUT_FILE).name}")
print("="*70)
print()
print("CO2 calculation complete!")
