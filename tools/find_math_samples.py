import json, re

with open('all_623_lessons.json', 'r', encoding='utf-8') as f:
    lessons = json.load(f)

print("=== SEARCHING LESSONS FOR USER-MENTIONED MATH FORMULAS ===")

keywords = [
    'times', 'theta', 'Blv', 'Zr_c', 'armature', 'commutation', 'lap', 'wave',
    'transformer losses', 'all-day efficiency', 'h-parameter', 'jfet', 'mosfet',
    'sin', 'frac', 'text'
]

matches = {}
for id, l in lessons.items():
    text = l['title'] + " " + l['body']
    for kw in keywords:
        if kw in text:
            if kw not in matches: matches[kw] = []
            matches[kw].append((id, l['title']))

for kw, list_l in matches.items():
    print(f"\nKeyword: '{kw}' (Found in {len(list_l)} lessons)")
    for id, title in list_l[:3]:
        print(f"  - {id}: {title}")
