import re, json

with open('eee-platform.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Let's find all occurrences of R_series or jX_L or Load Z
matches = [m.start() for m in re.finditer(r'R_series|jX_L|Load Z', html)]
print(f"Total occurrences of generic SVG tokens in eee-platform.html: {len(matches)}")

# Map each match to its parent lesson definition
lesson_matches = []
for m in matches:
    # Look back 3000 chars to find lesson id
    block = html[max(0, m-3000):m+500]
    id_matches = re.findall(r'id\s*:\s*"([^"]+)"', block)
    title_matches = re.findall(r'title\s*:\s*"([^"]+)"', block)
    if id_matches:
        lid = id_matches[-1]
        title = title_matches[-1] if title_matches else ""
        lesson_matches.append((lid, title, m))

# Deduplicate by lesson id
unique_map = {}
for lid, title, pos in lesson_matches:
    if lid not in unique_map:
        unique_map[lid] = title

print(f"Unique lessons with generic fallback SVG: {len(unique_map)}")

with open('generic_svg_lessons.json', 'w', encoding='utf-8') as f:
    json.dump(unique_map, f, indent=2)

for i, (lid, title) in enumerate(list(unique_map.items())[:15], 1):
    print(f"{i}. [{lid}] {title}")
