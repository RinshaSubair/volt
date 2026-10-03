import re, json

with open('all_623_lessons.json', 'r', encoding='utf-8') as f:
    active_lessons = json.load(f)

with open('eee-platform.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Let's search for every occurrence of generic SVG template in html
# Pattern of generic SVG contains R_series, jX_L, Load Z, Vs
generic_pattern = re.compile(r'<svg[^>]*>[\s\S]*?(?:R_series|jX_L|Load Z)[\s\S]*?</svg>')

matches = list(generic_pattern.finditer(html))
print(f"Total generic SVG elements in HTML: {len(matches)}")

# Map each generic SVG element to the active lesson ID it belongs to
lesson_generic_map = []
for m in matches:
    pos = m.start()
    # Find the active lesson ID whose definition encloses pos
    # Look back 5000 chars and forward 5000 chars for `"lesson_id":` or `id: "lesson_id"`
    snippet_before = html[max(0, pos-8000):pos]
    
    # Find all lesson keys in snippet_before
    found_lids = []
    for lid in active_lessons.keys():
        if f'"{lid}"' in snippet_before or f"'{lid}'" in snippet_before or f'id: "{lid}"' in snippet_before:
            # find last occurrence index
            idx = max(snippet_before.rfind(f'"{lid}"'), snippet_before.rfind(f"'{lid}'"))
            found_lids.append((idx, lid))
    
    if found_lids:
        found_lids.sort()
        best_lid = found_lids[-1][1]
        title = active_lessons[best_lid].get('title', '')
        lesson_generic_map.append((best_lid, title, pos, m.group(0)))

# Deduplicate
unique_generic = {}
for lid, title, pos, svg in lesson_generic_map:
    if lid not in unique_generic:
        unique_generic[lid] = {'title': title, 'pos': pos, 'svg': svg}

print(f"Total unique active lessons with generic fallback SVG: {len(unique_generic)}")

with open('generic_lessons_full_map.json', 'w', encoding='utf-8') as f:
    json.dump(unique_generic, f, indent=2)

for i, (lid, data) in enumerate(list(unique_generic.items())[:30], 1):
    print(f"{i}. [{lid}] {data['title']}")
