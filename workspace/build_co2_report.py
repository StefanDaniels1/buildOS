#!/usr/bin/env python3
"""Build CO2 report from classified elements and NIBE database"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Load input files
print("Loading files...")
with open('/app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json') as f:
    classified_data = json.load(f)

with open('/app/.claude/skills/ifc-analysis/reference/durability_database.json') as f:
    database = json.load(f)

elements = classified_data['elements']
print(f"Loaded {len(elements)} elements")

# Helper functions for CO2 lookup and calculation
def find_co2_factor(db, mat_cat, mat_subcat):
    """Find CO2 factor using priority strategy"""
    if mat_cat not in db['materials']:
        return None, "not_found", []

    cat_data = db['materials'][mat_cat]

    # Priority 1: Exact match
    if mat_subcat in cat_data:
        return (cat_data[mat_subcat]['embodied_co2_per_kg'],
                cat_data[mat_subcat]['source'], [])

    # Priority 2: Generic
    gen_key = f"{mat_cat}_generic"
    if gen_key in cat_data:
        return (cat_data[gen_key]['embodied_co2_per_kg'],
                cat_data[gen_key]['source'], [])

    # Priority 3: First available
    if cat_data:
        first_key = list(cat_data.keys())[0]
        return (cat_data[first_key]['embodied_co2_per_kg'],
                cat_data[first_key]['source'],
                [f"Used {first_key} as fallback"])

    return None, "not_found", []

def get_density(db, mat_cat, mat_subcat):
    """Get material density"""
    if mat_cat not in db['materials']:
        return None

    cat_data = db['materials'][mat_cat]

    if mat_subcat in cat_data:
        return cat_data[mat_subcat]['density_kg_m3']

    gen_key = f"{mat_cat}_generic"
    if gen_key in cat_data:
        return cat_data[gen_key]['density_kg_m3']

    if cat_data:
        first_key = list(cat_data.keys())[0]
        return cat_data[first_key]['density_kg_m3']

    return None

def get_rebar_ratio(db, element_type):
    """Get reinforcement ratio for structural concrete"""
    ratios = db.get('reinforcement_ratios', {})
    et_lower = element_type.lower()

    if element_type in ratios:
        return ratios[element_type] / 100.0

    for key in ['column', 'beam', 'slab', 'footing', 'wall']:
        if key in et_lower:
            if key == 'column':
                return ratios.get('column', 2.5) / 100.0
            elif key == 'beam':
                return ratios.get('beam', 2.8) / 100.0
            elif key == 'slab':
                return ratios.get('structural_slab', 2.0) / 100.0
            elif key == 'footing':
                return ratios.get('footing', 1.5) / 100.0
            elif key == 'wall' and 'foundation' in et_lower:
                return ratios.get('foundation_wall', 1.8) / 100.0
            elif key == 'wall':
                return ratios.get('structural_wall', 2.2) / 100.0

    return 0.0

# Process each element
detailed_results = []
skipped_elements = []
total_co2 = 0.0
total_mass = 0.0

print(f"Processing {len(elements)} elements...")

for i, elem in enumerate(elements):
    volume = elem.get('volume_m3')
    mat_primary = elem.get('material_primary', {})
    mat_category = mat_primary.get('category')
    mat_subcategory = mat_primary.get('subcategory')
    element_type = elem.get('element_type', '')

    # Build result object
    result = {
        'global_id': elem['global_id'],
        'element_name': elem['name'],
        'element_type': element_type,
        'material_category': mat_category,
        'volume_m3': volume,
        'mass_kg': None,
        'co2_kg': None,
        'co2_factor_used': None,
        'data_source': None,
        'calculation_method': None,
        'confidence': round(elem.get('confidence', 0.5), 2),
        'warnings': []
    }

    # Check volume
    if volume is None or volume == 0:
        result['calculation_method'] = 'skipped'
        result['warnings'].append('No volume data - cannot calculate CO2')
        skipped_elements.append(result)
        continue

    # Check material
    if not mat_category:
        result['calculation_method'] = 'skipped'
        result['warnings'].append('No material category - cannot calculate CO2')
        skipped_elements.append(result)
        continue

    # Find CO2 factor
    co2_factor, source, warn = find_co2_factor(database, mat_category, mat_subcategory)

    if co2_factor is None:
        result['calculation_method'] = 'skipped'
        result['warnings'].extend(warn)
        skipped_elements.append(result)
        continue

    result['co2_factor_used'] = co2_factor
    result['data_source'] = source
    result['warnings'].extend(warn)

    # Get density
    density = get_density(database, mat_category, mat_subcategory)
    if density is None:
        result['calculation_method'] = 'skipped'
        result['warnings'].append('Cannot determine material density')
        skipped_elements.append(result)
        continue

    # Calculate mass and CO2
    mass_kg = volume * density
    result['mass_kg'] = round(mass_kg, 2)

    co2_kg = mass_kg * co2_factor

    # Add reinforcement for concrete structural elements
    if mat_category == 'concrete' and any(t in element_type.lower() for t in
        ['column', 'beam', 'slab', 'footing', 'wall', 'structural']):
        rebar_ratio = get_rebar_ratio(database, element_type)
        if rebar_ratio > 0:
            rebar_mass = mass_kg * rebar_ratio
            rebar_co2 = rebar_mass * 1.65  # Steel reinforcement factor
            co2_kg += rebar_co2
            result['warnings'].append(f"Added {rebar_ratio*100:.1f}% reinforcement ({rebar_mass:.2f} kg steel)")

    result['co2_kg'] = round(co2_kg, 2)
    result['calculation_method'] = 'volume_based'

    detailed_results.append(result)
    total_co2 += co2_kg
    total_mass += result['mass_kg']

    if (i + 1) % 50 == 0:
        print(f"  Processed {i+1} elements...")

print(f"Complete: {len(detailed_results)} calculated, {len(skipped_elements)} skipped")

# Sort detailed results by CO2 (descending)
detailed_results.sort(key=lambda x: x['co2_kg'], reverse=True)

# Aggregate by category
by_category = defaultdict(lambda: {
    'count': 0,
    'co2_kg': 0.0,
    'mass_kg': 0.0,
    'elements': []
})

for result in detailed_results:
    cat = result['material_category']
    by_category[cat]['count'] += 1
    by_category[cat]['co2_kg'] += result['co2_kg']
    by_category[cat]['mass_kg'] += result['mass_kg']
    by_category[cat]['elements'].append(result['global_id'])

# Calculate percentages
for cat_data in by_category.values():
    if total_co2 != 0:
        cat_data['percentage'] = round((cat_data['co2_kg'] / total_co2 * 100), 1)
    else:
        cat_data['percentage'] = 0.0

# Sort by CO2 impact
by_category = dict(sorted(by_category.items(), key=lambda x: x[1]['co2_kg'], reverse=True))

# Build summary
completeness = round((len(detailed_results) / len(elements) * 100), 1) if elements else 0

summary = {
    'timestamp': datetime.now().isoformat(),
    'input_file': 'all_classified_elements.json',
    'database_version': database.get('version', 'unknown'),
    'total_elements': len(elements),
    'calculated': len(detailed_results),
    'skipped': len(skipped_elements),
    'total_co2_kg': round(total_co2, 2),
    'total_mass_kg': round(total_mass, 2),
    'completeness_pct': completeness
}

# Build report
report = {
    'summary': summary,
    'by_category': by_category,
    'detailed_results': detailed_results,
    'skipped_elements': skipped_elements
}

# Save report
output_path = '/app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json'
with open(output_path, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\nReport saved to: {output_path}")

# Print summary
print("\n" + "="*70)
print("CO2 CALCULATION REPORT")
print("="*70)
print()
print(f"Input: all_classified_elements.json")
print(f"Elements: {summary['total_elements']} total, {summary['calculated']} calculated ({summary['completeness_pct']:.1f}%)")
print()
print(f"TOTAL CO2 IMPACT: {summary['total_co2_kg']:,.2f} kg CO2-eq")
print(f"Total Mass: {summary['total_mass_kg']:,.2f} kg")
print()
print("Breakdown by Material:")
for cat, data in by_category.items():
    pct = data['percentage']
    print(f"  {cat:16} | {data['count']:2} elements | {data['co2_kg']:10,.2f} kg CO2 ({pct:6.1f}%)")

if len(skipped_elements) > 0:
    print()
    print(f"Skipped: {len(skipped_elements)} elements")
    print()
    print("Top skipped reasons:")
    reasons = defaultdict(int)
    for skip in skipped_elements:
        if skip['warnings']:
            reason = skip['warnings'][0]
            reasons[reason] += 1
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {reason}: {count} elements")

print()
print(f"Output: co2_report.json")
print("="*70)
print("\nCO2 calculation complete!")
