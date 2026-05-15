import json
from collections import Counter

with open('pipeline_output.json') as f:
    d = json.load(f)

services = d.get('selected_services', [])
print(f'[1] selected_services count: {len(services)}')

sample = services[0] if services else {}
required_keys = {'id', 'ports', 'load', 'region'}
missing = required_keys - set(sample.keys())
print(f'[2] Sample keys: {list(sample.keys())}')
print(f'[2] Missing keys: {list(missing)}')
if sample:
    print(f'[2] Sample: id={sample.get("id")}, region={sample.get("region")}, ports={sample.get("ports")}, load={sample.get("load")}')

regions = Counter(s.get('region') for s in services)
print(f'[3] Region distribution: {dict(regions)}')

multi_port = [s for s in services if len(s.get('ports', [])) > 2]
print(f'[4] Multi-port services: {len(multi_port)}')

major_flows = [s for s in services if s.get('load', 0) >= 300]
print(f'[5] Major flows (load >= 300 TEU): {len(major_flows)}')

print()
if len(services) > 0 and not missing:
    print('[PASS] Data structure is valid - routes ready for animation!')
else:
    print('[FAIL] Issues found in data structure.')
