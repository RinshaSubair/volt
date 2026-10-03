import re, json

with open('eee-platform.html', 'r', encoding='utf-8') as f:
    html = f.read()

pos = html.find('const LESSONS = {')
if pos == -1:
    print("const LESSONS not found!")
    exit(1)

# Find end of LESSONS object or parse keys
lessons_block = html[pos:]

# Find all lesson keys: "lesson-id": {
pattern = re.compile(r'"([a-zA-Z0-9_-]+)"\s*:\s*\{\s*title\s*:\s*"([^"]+)"')

matches = list(pattern.finditer(lessons_block))
print(f"Total lesson keys found in LESSONS object: {len(matches)}")

# Map each lesson key to its block in LESSONS
lesson_data = {}
for i in range(len(matches)):
    m = matches[i]
    lid = m.group(1)
    title = m.group(2)
    start_pos = pos + m.start()
    end_pos = pos + matches[i+1].start() if i+1 < len(matches) else len(html)
    block = html[start_pos:end_pos]
    
    # Extract SVG inside block
    svg_match = re.search(r'<svg[\s\S]*?</svg>', block)
    svg_text = svg_match.group(0) if svg_match else ""
    
    lesson_data[lid] = {
        'title': title,
        'has_svg': bool(svg_text),
        'svg': svg_text,
        'block_start': start_pos,
        'block_end': end_pos
    }

print(f"Parsed {len(lesson_data)} lessons from LESSONS object.")

# Check for generic SVG fallback tokens: R_series, jX_L, Load Z, Series Impedance, Load Impedance
generic_lessons = {}
for lid, d in lesson_data.items():
    s = d['svg']
    if 'R_series' in s or 'jX_L' in s or 'Load Z' in s or 'Series Impedance' in s or 'Load Impedance' in s:
        generic_lessons[lid] = d['title']

print(f"Lessons with generic SVG fallback (R_series/jX_L/Load Z): {len(generic_lessons)}")

with open('generic_lessons_exact.json', 'w', encoding='utf-8') as f:
    json.dump(generic_lessons, f, indent=2)

for i, (lid, title) in enumerate(list(generic_lessons.items())[:20], 1):
    print(f"{i}. [{lid}] {title}")
