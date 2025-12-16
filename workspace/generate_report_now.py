#!/usr/bin/env python3
import json
from datetime import datetime

# Load files
with open('/app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json') as f:
    d_in = json.load(f)
with open('/app/.claude/skills/ifc-analysis/reference/durability_database.json') as f:
    d_db = json.load(f)

els = d_in['elements']
calc = []
skip = []
tot_c2 = 0
tot_m = 0

for e in els:
    v = e.get('volume_m3')
    m_p = e.get('material_primary', {})
    m_c = m_p.get('category')
    m_s = m_p.get('subcategory')
    et = e.get('element_type', '')

    res = {
        'global_id': e['global_id'],
        'element_name': e['name'],
        'element_type': et,
        'material_category': m_c,
        'volume_m3': v,
        'mass_kg': None,
        'co2_kg': None,
        'co2_factor_used': None,
        'data_source': None,
        'calculation_method': None,
        'confidence': round(e.get('confidence', 0.5), 2),
        'warnings': []
    }

    if not v or v == 0:
        res['calculation_method'] = 'skipped'
        res['warnings'] = ['No volume data']
        skip.append(res)
        continue

    if not m_c:
        res['calculation_method'] = 'skipped'
        res['warnings'] = ['No material']
        skip.append(res)
        continue

    # Find CO2 factor
    if m_c not in d_db['materials']:
        res['calculation_method'] = 'skipped'
        res['warnings'] = ['Material not found']
        skip.append(res)
        continue

    md = d_db['materials'][m_c]
    cf = None

    if m_s in md:
        cf = md[m_s]['embodied_co2_per_kg']
        src = md[m_s]['source']
    elif f'{m_c}_generic' in md:
        cf = md[f'{m_c}_generic']['embodied_co2_per_kg']
        src = md[f'{m_c}_generic']['source']
    elif md:
        fk = list(md.keys())[0]
        cf = md[fk]['embodied_co2_per_kg']
        src = md[fk]['source']

    if cf is None:
        res['calculation_method'] = 'skipped'
        res['warnings'] = ['CO2 factor not found']
        skip.append(res)
        continue

    # Get density
    dn = None
    if m_s in md:
        dn = md[m_s]['density_kg_m3']
    elif f'{m_c}_generic' in md:
        dn = md[f'{m_c}_generic']['density_kg_m3']
    elif md:
        dn = md[list(md.keys())[0]]['density_kg_m3']

    if dn is None:
        res['calculation_method'] = 'skipped'
        res['warnings'] = ['Density not found']
        skip.append(res)
        continue

    # Calculate
    m = v * dn
    co2 = m * cf

    # Reinforcement
    if m_c == 'concrete' and any(t in et.lower() for t in ['col','beam','slab','foot','wall','struct']):
        rs = d_db['reinforcement_ratios']
        rb = 0
        if et in rs: rb = rs[et]/100
        elif 'col' in et.lower(): rb = rs.get('column', 2.5)/100
        elif 'beam' in et.lower(): rb = rs.get('beam', 2.8)/100
        elif 'slab' in et.lower(): rb = rs.get('structural_slab', 2.0)/100
        elif 'foot' in et.lower(): rb = rs.get('footing', 1.5)/100
        elif 'wall' in et.lower() and 'found' in et.lower(): rb = rs.get('foundation_wall', 1.8)/100
        elif 'wall' in et.lower(): rb = rs.get('structural_wall', 2.2)/100

        if rb > 0:
            rm = m * rb
            co2 += rm * 1.65

    res['mass_kg'] = round(m, 2)
    res['co2_kg'] = round(co2, 2)
    res['co2_factor_used'] = cf
    res['data_source'] = src
    res['calculation_method'] = 'volume_based'

    calc.append(res)
    tot_c2 += co2
    tot_m += m

# Sort and aggregate
calc.sort(key=lambda x: x['co2_kg'], reverse=True)

bc = {}
for r in calc:
    cat = r['material_category']
    if cat not in bc:
        bc[cat] = {'count': 0, 'co2_kg': 0, 'mass_kg': 0}
    bc[cat]['count'] += 1
    bc[cat]['co2_kg'] += r['co2_kg']
    bc[cat]['mass_kg'] += r['mass_kg']

for d in bc.values():
    d['percentage'] = round((d['co2_kg'] / tot_c2 * 100), 1) if tot_c2 else 0

bc = dict(sorted(bc.items(), key=lambda x: x[1]['co2_kg'], reverse=True))

# Report
rep = {
    'summary': {
        'timestamp': datetime.now().isoformat(),
        'input_file': 'all_classified_elements.json',
        'database_version': d_db['version'],
        'total_elements': len(els),
        'calculated': len(calc),
        'skipped': len(skip),
        'total_co2_kg': round(tot_c2, 2),
        'total_mass_kg': round(tot_m, 2),
        'completeness_pct': round(len(calc)/len(els)*100, 1) if els else 0
    },
    'by_category': bc,
    'detailed_results': calc,
    'skipped_elements': skip
}

with open('/app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json', 'w') as f:
    json.dump(rep, f, indent=2)

print()
print('='*70)
print('CO2 CALCULATION REPORT')
print('='*70)
print()
print(f'Input: all_classified_elements.json')
print(f'Elements: {len(els)} total, {len(calc)} calculated ({rep["summary"]["completeness_pct"]:.1f}%)')
print()
print(f'TOTAL CO2 IMPACT: {rep["summary"]["total_co2_kg"]:,.2f} kg CO2-eq')
print(f'Total Mass: {rep["summary"]["total_mass_kg"]:,.2f} kg')
print()
print('Breakdown by Material:')
for c, d in bc.items():
    print(f'  {c:16} | {d["count"]:2} elements | {d["co2_kg"]:10,.2f} kg CO2 ({d["percentage"]:6.1f}%)')

if len(skip) > 0:
    print()
    print(f'Skipped: {len(skip)} elements')

print()
print(f'Output: co2_report.json')
print('='*70)
print()
print('CO2 calculation complete!')
