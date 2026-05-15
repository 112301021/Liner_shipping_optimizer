import json
from collections import Counter

with open('pipeline_output.json') as f:
    d = json.load(f)

services = d.get('selected_services', [])
regional_results = d.get('regional_results', [])

print(f'Total selected_services: {len(services)}')
print(f'Total regional_results: {len(regional_results)}')
print()

# Build port -> region mapping from regional results
# Each region has a set of hubs
region_hubs = {}
for r in regional_results:
    region = r.get('region', '')
    hubs = r.get('hub_ports', [])
    region_hubs[region] = set(hubs)

print('Region hub ports:')
for region, hubs in region_hubs.items():
    print(f'  {region}: {sorted(hubs)}')
print()

# Check if any service spans multiple regions
# Since each service has a single 'region' field, check if its ports overlap with other region hubs
inter_regional = []
for svc in services:
    svc_region = svc.get('region', '')
    svc_ports = set(svc.get('ports', []))
    
    for other_region, hubs in region_hubs.items():
        if other_region != svc_region and svc_ports & hubs:
            inter_regional.append({
                'id': svc['id'],
                'ports': svc['ports'],
                'load': svc['load'],
                'svc_region': svc_region,
                'touches': other_region
            })
            break

print(f'Services touching multiple region hubs: {len(inter_regional)}')
for s in inter_regional[:5]:
    print(f"  id={s['id']}, region={s['svc_region']}, touches={s['touches']}, ports={s['ports']}, load={s['load']}")

print()
# Check all regions represented
regions = Counter(s.get('region') for s in services)
print(f'Region distribution: {dict(regions)}')

# Top 10 highest-load services
top = sorted(services, key=lambda x: x.get('load',0), reverse=True)[:10]
print()
print('Top 10 services by load:')
for s in top:
    print(f"  id={s['id']}, region={s['region']}, ports={s['ports']}, load={s['load']}")
