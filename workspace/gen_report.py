import json, sys
from datetime import datetime
from collections import defaultdict
from pathlib import Path

F_IN = '/app/workspace/.context/session_session_1765555793733_ebch5w/all_classified_elements.json'
F_DB = '/app/.claude/skills/ifc-analysis/reference/durability_database.json'
F_OUT = '/app/workspace/.context/session_session_1765555793733_ebch5w/co2_report.json'

print(f"Loading files...")
with open(F_IN) as f: d_in = json.load(f)
with open(F_DB) as f: d_db = json.load(f)

els = d_in['elements']
print(f"Found {len(els)} elements\n")

def f_co2(mc,ms):
    w=[]
    if mc not in d_db['materials']: return None,"",w
    cd = d_db['materials'][mc]
    if ms in cd: return cd[ms]['embodied_co2_per_kg'],cd[ms]['source'],w
    gk = f"{mc}_generic"
    if gk in cd: return cd[gk]['embodied_co2_per_kg'],cd[gk]['source'],w
    fk = list(cd.keys())[0] if cd else None
    if fk: return cd[fk]['embodied_co2_per_kg'],cd[fk]['source'],[f"fallback:{fk}"]
    return None,"",["not_found"]

def f_den(mc,ms):
    if mc not in d_db['materials']: return None
    cd = d_db['materials'][mc]
    if ms in cd: return cd[ms]['density_kg_m3']
    gk = f"{mc}_generic"
    if gk in cd: return cd[gk]['density_kg_m3']
    fk = list(cd.keys())[0] if cd else None
    return cd[fk]['density_kg_m3'] if fk else None

def f_bar(et):
    rs = d_db['reinforcement_ratios']
    if et in rs: return rs[et]/100
    for t in ['column','beam','slab','footing','wall']:
        if t in et.lower():
            if t=='column': return rs.get('column',2.5)/100
            elif t=='beam': return rs.get('beam',2.8)/100
            elif t=='slab': return rs.get('structural_slab',2.0)/100
            elif t=='footing': return rs.get('footing',1.5)/100
    return 0

det = []
skip = []
tot_co2 = tot_m = 0

for e in els:
    v = e.get('volume_m3')
    mp = e.get('material_primary',{})
    mc = mp.get('category')
    ms = mp.get('subcategory')
    et = e.get('element_type','')

    r = {
        'global_id': e['global_id'],
        'element_name': e['name'],
        'element_type': et,
        'material_category': mc,
        'volume_m3': v,
        'mass_kg': None,
        'co2_kg': None,
        'co2_factor_used': None,
        'data_source': None,
        'calculation_method': None,
        'confidence': e.get('confidence',0.5),
        'warnings': []
    }

    if v is None or v==0:
        r['calculation_method']='skipped'
        r['warnings']=['No volume']
        skip.append(r)
        continue

    if not mc:
        r['calculation_method']='skipped'
        r['warnings']=['No material']
        skip.append(r)
        continue

    cf,src,w = f_co2(mc,ms)
    if cf is None:
        r['calculation_method']='skipped'
        r['warnings']=w
        skip.append(r)
        continue

    dn = f_den(mc,ms)
    if dn is None:
        r['calculation_method']='skipped'
        r['warnings']=['No density']
        skip.append(r)
        continue

    m = v * dn
    r['mass_kg'] = round(m,2)
    c = m * cf

    if mc=='concrete' and any(t in et.lower() for t in ['column','beam','slab','footing','wall']):
        rb = f_bar(et)
        if rb>0:
            rm = m * rb
            c += rm * 1.65

    r['co2_kg'] = round(c,2)
    r['co2_factor_used'] = cf
    r['data_source'] = src
    r['warnings'] = w
    r['calculation_method'] = 'volume_based'

    det.append(r)
    tot_co2 += c
    tot_m += r['mass_kg']

det.sort(key=lambda x: x['co2_kg'], reverse=True)

bc = defaultdict(lambda: {'count':0,'co2_kg':0.0,'mass_kg':0.0})
for r in det:
    bc[r['material_category']]['count']+=1
    bc[r['material_category']]['co2_kg']+=r['co2_kg']
    bc[r['material_category']]['mass_kg']+=r['mass_kg']

for cd in bc.values():
    cd['percentage'] = round((cd['co2_kg']/tot_co2*100),1) if tot_co2 else 0

bc = dict(sorted(bc.items(), key=lambda x: x[1]['co2_kg'], reverse=True))

rep = {
    'summary':{
        'timestamp': datetime.now().isoformat(),
        'input_file': Path(F_IN).name,
        'database_version': d_db['version'],
        'total_elements': len(els),
        'calculated': len(det),
        'skipped': len(skip),
        'total_co2_kg': round(tot_co2,2),
        'total_mass_kg': round(tot_m,2),
        'completeness_pct': round(len(det)/len(els)*100,1)
    },
    'by_category': bc,
    'detailed_results': det,
    'skipped_elements': skip
}

with open(F_OUT,'w') as f: json.dump(rep,f,indent=2)

print("="*70)
print("CO2 CALCULATION REPORT")
print("="*70)
print(f"\nInput: {Path(F_IN).name}")
print(f"Elements: {len(els)} total, {len(det)} calculated ({rep['summary']['completeness_pct']:.1f}%)")
print(f"\nTOTAL CO2 IMPACT: {rep['summary']['total_co2_kg']:,.2f} kg CO2-eq")
print(f"Total Mass: {rep['summary']['total_mass_kg']:,.2f} kg")
print("\nBreakdown by Material:")
for c,d in bc.items():
    print(f"  {c:16} | {d['count']:2} elements | {d['co2_kg']:10,.2f} kg CO2 ({d['percentage']:6.1f}%)")
if len(skip)>0:
    print(f"\nSkipped: {len(skip)} elements")
print(f"\nOutput: {Path(F_OUT).name}")
print("="*70)
print("\nCO2 calculation complete!")
