import re, json

with open('eee-platform.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Let's find all lesson definitions in JS.
# Lessons in html are stored in objects like:
# { id: "...", title: "...", ... body: `...` } or "id": "..."

# Let's parse all lesson IDs and their character ranges in html
# We can find `id: "..."` or `"id": "..."`
pattern = re.compile(r'(?:id|["\']id["\'])\s*:\s*["\']([^"\'\n]+)["\']')

matches = list(pattern.finditer(html))
print(f"Total ID matches: {len(matches)}")

# Filter to actual lesson IDs (from all_623_lessons.json)
with open('all_623_lessons.json', 'r', encoding='utf-8') as f:
    active_lessons_dict = json.load(f)

active_ids = set(active_lessons_dict.keys())

lesson_spans = []
for i in range(len(matches)):
    m = matches[i]
    lid = m.group(1)
    if lid in active_ids:
        start_pos = m.start()
        # End pos is start of next active lesson id match, or end of file
        end_pos = len(html)
        for j in range(i+1, len(matches)):
            if matches[j].group(1) in active_ids:
                end_pos = matches[j].start()
                break
        lesson_spans.append((lid, start_pos, end_pos))

print(f"Mapped {len(lesson_spans)} active lesson spans in HTML.")

generic_lessons = []
for lid, start, end in lesson_spans:
    lesson_text = html[start:end]
    if 'R_series' in lesson_text or 'jX_L' in lesson_text or 'Load Z' in lesson_text:
        generic_lessons.append(lid)

print(f"Active lessons containing generic SVG fallback: {len(generic_lessons)}")

with open('generic_lessons_list.json', 'w', encoding='utf-8') as f:
    json.dump(generic_lessons, f, indent=2)

for i, lid in enumerate(generic_lessons[:20], 1):
    title = active_lessons_dict[lid]['title']
    print(f"{i}. [{lid}] {title}")
