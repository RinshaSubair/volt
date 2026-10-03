import re, json

with open('eee-platform.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's extract all lesson definitions with id, title, svg
# Pattern for lesson objects
pattern = re.compile(r'\{\s*id\s*:\s*"([^"]+)"[\s\S]*?title\s*:\s*"([^"]+)"[\s\S]*?svg\s*:\s*`([^`]+)`', re.DOTALL)

lessons = []
for match in pattern.finditer(content):
    lid, title, svg = match.groups()
    lessons.append({
        'id': lid,
        'title': title,
        'svg': svg,
        'start': match.start(),
        'end': match.end()
    })

print(f"Extracted {len(lessons)} lessons with SVG definitions.")

generic_lessons = []
for l in lessons:
    s = l['svg']
    if 'R_series' in s or 'jX_L' in s or 'Load Z' in s or 'Series Impedance' in s or 'Load Impedance' in s:
        generic_lessons.append(l)

print(f"Generic SVG fallback count: {len(generic_lessons)}")

with open('generic_lessons.json', 'w', encoding='utf-8') as f:
    json.dump([{'id': l['id'], 'title': l['title']} for l in generic_lessons], f, indent=2)

print("Saved generic_lessons.json")
