import re

with open('eee-platform.html.bak_CRITICAL_STUDENT_REPAIR', 'r', encoding='utf-8') as f:
    html = f.read()

matches = [m.start() for m in re.finditer(r'R_series', html)]
print(f"Total R_series occurrences: {len(matches)}")

svg_blocks = []
for pos in matches:
    start = html.rfind('<svg', 0, pos)
    end = html.find('</svg>', pos)
    if start != -1 and end != -1:
        end += len('</svg>')
        svg_text = html[start:end]
        svg_blocks.append((start, end, svg_text))

print(f"Extracted {len(svg_blocks)} exact SVG blocks containing R_series.")
print(f"Sample block length: {len(svg_blocks[0][2])}")
print("Sample SVG block start:", svg_blocks[0][2][:80])
