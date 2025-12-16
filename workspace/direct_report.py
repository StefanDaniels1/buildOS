import json, sys; exec("""
f_in = '/app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json'
f_db = '/app/.claude/skills/ifc-analysis/reference/durability_database.json'
f_out = '/app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json'

with open(f_in) as f: cd = json.load(f)
with open(f_db) as f: db = json.load(f)

els = cd['elements']
print(f'Loaded {len(els)} elements')

def f_co2(mc, ms):
    if mc not in db['materials']: return None, 'not_found', []
    cd_ = db['materials'][mc]
    if ms in cd_: return cd_[ms]['embodied_co2_per_kg'], cd_[ms]['source'], []
    gk = f'{mc}_generic'
    if gk in cd_: return cd_[gk]['embodied_co2_per_kg'], cd_[gk]['source'], []
    fk = list(cd_.keys())[0] if cd_ else None
    return (cd_[fk]['embodied_co2_per_kg'], cd_[fk]['source'], [f'fallback:{fk}']) if fk else (None, 'not_found', [])

def f_den(mc, ms):
    if mc not in db['materials']: return None
    cd_ = db['materials'][mc]
    if ms in cd_: return cd_[ms]['density_kg_m3']
    gk = f'{mc}_generic'
    if gk in cd_: return cd_[gk]['density_kg_m3']
    fk = list(cd_.keys())[0] if cd_ else None
    return cd_[fk]['density_kg_m3'] if fk else None

def f_bar(et):
    rs = db['reinforcement_ratios']
    if et in rs: return rs[et]/100
    el = et.lower()
    if 'column' in el: return rs.get('column', 2.5)/100
    if 'beam' in el: return rs.get('beam', 2.8)/100
    if 'slab' in el or 'structural' in el: return rs.get('structural_slab', 2.0)/100
    if 'footing' in el: return rs.get('footing', 1.5)/100
    if 'wall' in el and 'foundation' in el: return rs.get('foundation_wall', 1.8)/100
    if 'wall' in el: return rs.get('structural_wall', 2.2)/100
    return 0

det, skip, tot_co2, tot_m = [], [], 0, 0

for e in els:
    v = e.get('volume_m3')
    mp = e.get('material_primary', {})
    mc = mp.get('category')
    ms = mp.get('subcategory')
    et = e.get('element_type', '')

    r = {'global_id': e['global_id'], 'element_name': e['name'], 'element_type': et, 'material_category': mc, 'volume_m3': v, 'mass_kg': None, 'co2_kg': None, 'co2_factor_used': None, 'data_source': None, 'calculation_method': None, 'confidence': round(e.get('confidence', 0.5), 2), 'warnings': []}

    if v is None or v == 0:
        r['calculation_method'] = 'skipped'
        r['warnings'] = ['No volume data - cannot calculate CO2']
        skip.append(r)
        continue

    if not mc:
        r['calculation_method'] = 'skipped'
        r['warnings'] = ['No material category - cannot calculate CO2']
        skip.append(r)
        continue

    cf, src, w = f_co2(mc, ms)
    if cf is None:
        r['calculation_method'] = 'skipped'
        r['warnings'] = w
        skip.append(r)
        continue

    dn = f_den(mc, ms)
    if dn is None:
        r['calculation_method'] = 'skipped'
        r['warnings'] = ['Cannot determine material density']
        skip.append(r)
        continue

    m = v * dn
    r['mass_kg'] = round(m, 2)
    c = m * cf

    if mc == 'concrete' and any(t in et.lower() for t in ['column', 'beam', 'slab', 'footing', 'wall', 'structural']):
        rb = f_bar(et)
        if rb > 0:
            rm = m * rb
            c += rm * 1.65

    r['co2_kg'] = round(c, 2)
    r['co2_factor_used'] = cf
    r['data_source'] = src
    r['warnings'] = w
    r['calculation_method'] = 'volume_based'

    det.append(r)
    tot_co2 += c
    tot_m += r['mass_kg']

det.sort(key=lambda x: x['co2_kg'], reverse=True)

bc = {}
for r in det:
    cat = r['material_category']
    if cat not in bc: bc[cat] = {'count': 0, 'co2_kg': 0.0, 'mass_kg': 0.0}
    bc[cat]['count'] += 1
    bc[cat]['co2_kg'] += r['co2_kg']
    bc[cat]['mass_kg'] += r['mass_kg']

for d in bc.values(): d['percentage'] = round((d['co2_kg']/tot_co2*100), 1) if tot_co2 else 0

bc = dict(sorted(bc.items(), key=lambda x: x[1]['co2_kg'], reverse=True))

from datetime import datetime
rep = {'summary': {'timestamp': datetime.now().isoformat(), 'input_file': 'all_classified_elements.json', 'database_version': db.get('version', 'unknown'), 'total_elements': len(els), 'calculated': len(det), 'skipped': len(skip), 'total_co2_kg': round(tot_co2, 2), 'total_mass_kg': round(tot_m, 2), 'completeness_pct': round(len(det)/len(els)*100, 1) if els else 0}, 'by_category': bc, 'detailed_results': det, 'skipped_elements': skip}

with open(f_out, 'w') as f: json.dump(rep, f, indent=2)

print()
print('='*70)
print('CO2 CALCULATION REPORT')
print('='*70)
print()
print(f'Input: all_classified_elements.json')
print(f'Elements: {len(els)} total, {len(det)} calculated ({rep[\"summary\"][\"completeness_pct\"]:.1f}%)')
print()
print(f'TOTAL CO2 IMPACT: {rep[\"summary\"][\"total_co2_kg\"]:,.2f} kg CO2-eq')
print(f'Total Mass: {rep[\"summary\"][\"total_mass_kg\"]:,.2f} kg')
print()
print('Breakdown by Material:')
for c, d in bc.items():
    print(f'  {c:16} | {d[\"count\"]:2} elements | {d[\"co2_kg\"]:10,.2f} kg CO2 ({d[\"percentage\"]:6.1f}%)')

if len(skip) > 0:
    print()
    print(f'Skipped: {len(skip)} elements')

print()
print(f'Output: co2_report.json')
print('='*70)
print()
print('CO2 calculation complete!')
""")
