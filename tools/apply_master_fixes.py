import re, json

with open('eee-platform.html.bak_CRITICAL_STUDENT_REPAIR', 'r', encoding='utf-8') as f:
    html = f.read()

# Load active lessons dump for title lookups
with open('all_623_lessons.json', 'r', encoding='utf-8') as f:
    active_lessons = json.load(f)

# Part A: Fix repairLatex function
target_str = '.replace(/\\x08egin/g, \'\\\\\\begin\')'
if target_str not in html:
    print("ERROR: target_str not found in html!")
    exit(1)

pos = html.find('function repairLatex(str){')
pos_end = html.find('.replace(/\\x0b/g, \'\\\\v\')', pos) + len('.replace(/\\x0b/g, \'\\\\v\')')

old_block = html[pos:pos_end]
new_block = '''function repairLatex(str){
  if(!str) return "";
  str = str.replace(/\\\\\\\\/g, '\\\\');
  return str
    // JS escape artifacts from template literals and string evaluation
    .replace(/\\x09ext/g, '\\\\text')
    .replace(/\\x09imes/g, '\\\\times')
    .replace(/\\x09heta/g, '\\\\theta')
    .replace(/\\x09au/g, '\\\\tau')
    .replace(/\\x09an/g, '\\\\tan')
    .replace(/\\x09anh/g, '\\\\tanh')
    .replace(/\\x09ilde/g, '\\\\tilde')
    .replace(/\\x09op/g, '\\\\top')
    .replace(/\\x09o\\b/g, '\\\\to')
    .replace(/\\x0crac/g, '\\\\frac')
    .replace(/\\x0crall/g, '\\\\forall')
    .replace(/\\x08egin/g, '\\\\begin')
    .replace(/\\x08eta/g, '\\\\beta')
    .replace(/\\x08ar/g, '\\\\bar')
    .replace(/\\x08ullet/g, '\\\\bullet')
    .replace(/\\x07lpha/g, '\\\\alpha')
    .replace(/\\x07pprox/g, '\\\\approx')
    .replace(/\\x07ngle/g, '\\\\angle')
    .replace(/\\x0bec/g, '\\\\vec')
    .replace(/\\x08/g, '\\\\b')
    .replace(/\\x0c/g, '\\\\f')
    .replace(/\\x0b/g, '\\\\v')'''

html = html[:pos] + new_block + html[pos_end:]
print("Part A: repairLatex function updated.")

# Part B: Topic-Specific SVG Generator
def generate_topic_svg(lid, title):
    title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    if any(k in lid for k in ['buck', 'boost', 'chopper', 'dc-dc']):
        return f'''<svg viewBox='0 0 560 200' width='100%' height='auto' style='max-width:100%;display:block;margin:12px auto;background:#0f172a;border:1px solid #334155;border-radius:8px;' role='img' aria-label='{title_escaped} Diagram'>
  <rect width='560' height='200' fill='#0f172a' rx='8'/>
  <rect x='12' y='10' width='536' height='180' fill='#1e293b' stroke='#334155' stroke-width='1.5' rx='6'/>
  <text x='280' y='32' fill='#38bdf8' font-size='13' font-weight='bold' text-anchor='middle'>{title_escaped}</text>
  <circle cx='60' cy='110' r='20' fill='#0f172a' stroke='#38bdf8' stroke-width='2'/>
  <text x='60' y='114' fill='#38bdf8' font-size='12' font-weight='bold' text-anchor='middle'>V_in</text>
  <line x1='60' y1='55' x2='60' y2='90' stroke='#38bdf8' stroke-width='2'/>
  <line x1='60' y1='130' x2='60' y2='165' stroke='#38bdf8' stroke-width='2'/>
  <line x1='60' y1='55' x2='140' y2='55' stroke='#38bdf8' stroke-width='2'/>
  <rect x='140' y='43' width='50' height='24' fill='#0f172a' stroke='#a855f7' stroke-width='2' rx='3'/>
  <text x='165' y='59' fill='#a855f7' font-size='11' font-weight='bold' text-anchor='middle'>PWM S1</text>
  <line x1='190' y1='55' x2='260' y2='55' stroke='#38bdf8' stroke-width='2'/>
  <line x1='260' y1='55' x2='260' y2='90' stroke='#38bdf8' stroke-width='2'/>
  <polygon points='250,110 270,110 260,90' fill='#0f172a' stroke='#f43f5e' stroke-width='2'/>
  <line x1='250' y1='90' x2='270' y2='90' stroke='#f43f5e' stroke-width='2'/>
  <line x1='260' y1='110' x2='260' y2='165' stroke='#38bdf8' stroke-width='2'/>
  <path d='M 260 55 Q 270 40 280 55 Q 290 40 300 55 Q 310 40 320 55 Q 330 40 340 55' fill='none' stroke='#22c55e' stroke-width='2.5'/>
  <text x='300' y='38' fill='#22c55e' font-size='11' font-weight='bold' text-anchor='middle'>Inductor L</text>
  <line x1='340' y1='55' x2='420' y2='55' stroke='#38bdf8' stroke-width='2'/>
  <line x1='420' y1='55' x2='420' y2='95' stroke='#38bdf8' stroke-width='2'/>
  <line x1='410' y1='95' x2='430' y2='95' stroke='#eab308' stroke-width='2.5'/>
  <line x1='410' y1='105' x2='430' y2='105' stroke='#eab308' stroke-width='2.5'/>
  <line x1='420' y1='105' x2='420' y2='165' stroke='#38bdf8' stroke-width='2'/>
  <rect x='470' y='80' width='30' height='60' fill='#0f172a' stroke='#38bdf8' stroke-width='2' rx='3'/>
  <text x='485' y='114' fill='#38bdf8' font-size='11' font-weight='bold' text-anchor='middle'>R_L</text>
  <line x1='420' y1='55' x2='485' y2='55' stroke='#38bdf8' stroke-width='2'/>
  <line x1='485' y1='55' x2='485' y2='80' stroke='#38bdf8' stroke-width='2'/>
  <line x1='485' y1='140' x2='485' y2='165' stroke='#38bdf8' stroke-width='2'/>
  <line x1='60' y1='165' x2='485' y2='165' stroke='#38bdf8' stroke-width='2'/>
</svg>'''

    elif any(k in lid for k in ['rectifier', 'thyristor', 'scr', 'commutation', 'controlled']):
        return f'''<svg viewBox='0 0 560 200' width='100%' height='auto' style='max-width:100%;display:block;margin:12px auto;background:#0f172a;border:1px solid #334155;border-radius:8px;' role='img' aria-label='{title_escaped} Diagram'>
  <rect width='560' height='200' fill='#0f172a' rx='8'/>
  <rect x='12' y='10' width='536' height='180' fill='#1e293b' stroke='#334155' stroke-width='1.5' rx='6'/>
  <text x='280' y='32' fill='#38bdf8' font-size='13' font-weight='bold' text-anchor='middle'>{title_escaped}</text>
  <circle cx='60' cy='110' r='20' fill='#0f172a' stroke='#38bdf8' stroke-width='2'/>
  <text x='60' y='114' fill='#38bdf8' font-size='12' font-weight='bold' text-anchor='middle'>AC</text>
  <path d='M 52 110 Q 56 102 60 110 T 68 110' stroke='#38bdf8' stroke-width='1.5' fill='none'/>
  <line x1='80' y1='110' x2='150' y2='110' stroke='#38bdf8' stroke-width='2'/>
  <polygon points='230,55 290,110 230,165 170,110' fill='#0f172a' stroke='#f43f5e' stroke-width='2.5'/>
  <text x='230' y='114' fill='#f43f5e' font-size='11' font-weight='bold' text-anchor='middle'>SCR Bridge</text>
  <line x1='150' y1='110' x2='170' y2='110' stroke='#38bdf8' stroke-width='2'/>
  <line x1='230' y1='55' x2='420' y2='55' stroke='#22c55e' stroke-width='2.5'/>
  <text x='320' y='45' fill='#22c55e' font-size='11' font-weight='bold' text-anchor='middle'>+V_DC</text>
  <line x1='230' y1='165' x2='420' y2='165' stroke='#38bdf8' stroke-width='2.5'/>
  <text x='320' y='180' fill='#38bdf8' font-size='11' font-weight='bold' text-anchor='middle'>-V_DC</text>
  <rect x='420' y='80' width='40' height='60' fill='#0f172a' stroke='#eab308' stroke-width='2' rx='3'/>
  <text x='440' y='114' fill='#eab308' font-size='11' font-weight='bold' text-anchor='middle'>R-L Load</text>
  <line x1='420' y1='55' x2='440' y2='55' stroke='#22c55e' stroke-width='2'/>
  <line x1='440' y1='55' x2='440' y2='80' stroke='#22c55e' stroke-width='2'/>
  <line x1='440' y1='140' x2='440' y2='165' stroke='#38bdf8' stroke-width='2'/>
  <line x1='420' y1='165' x2='440' y2='165' stroke='#38bdf8' stroke-width='2'/>
</svg>'''

    elif any(k in lid for k in ['inverter', 'vsi', 'spwm', 'pwm', 'matrix', 'sic-gan', 'solid-state', 'amplifier']):
        return f'''<svg viewBox='0 0 560 200' width='100%' height='auto' style='max-width:100%;display:block;margin:12px auto;background:#0f172a;border:1px solid #334155;border-radius:8px;' role='img' aria-label='{title_escaped} Diagram'>
  <rect width='560' height='200' fill='#0f172a' rx='8'/>
  <rect x='12' y='10' width='536' height='180' fill='#1e293b' stroke='#334155' stroke-width='1.5' rx='6'/>
  <text x='280' y='32' fill='#38bdf8' font-size='13' font-weight='bold' text-anchor='middle'>{title_escaped}</text>
  <line x1='50' y1='55' x2='380' y2='55' stroke='#f43f5e' stroke-width='2.5'/>
  <text x='90' y='48' fill='#f43f5e' font-size='11' font-weight='bold'>+V_DC Bus</text>
  <line x1='50' y1='165' x2='380' y2='165' stroke='#38bdf8' stroke-width='2.5'/>
  <text x='90' y='180' fill='#38bdf8' font-size='11' font-weight='bold'>-V_DC Bus</text>
  <rect x='160' y='65' width='40' height='35' fill='#0f172a' stroke='#22c55e' stroke-width='2' rx='3'/>
  <text x='180' y='86' fill='#22c55e' font-size='10' font-weight='bold' text-anchor='middle'>S1 (IGBT)</text>
  <rect x='160' y='120' width='40' height='35' fill='#0f172a' stroke='#22c55e' stroke-width='2' rx='3'/>
  <text x='180' y='141' fill='#22c55e' font-size='10' font-weight='bold' text-anchor='middle'>S4 (IGBT)</text>
  <line x1='180' y1='55' x2='180' y2='65' stroke='#f43f5e' stroke-width='2'/>
  <line x1='180' y1='100' x2='180' y2='120' stroke='#a855f7' stroke-width='2'/>
  <line x1='180' y1='155' x2='180' y2='165' stroke='#38bdf8' stroke-width='2'/>
  <circle cx='180' cy='110' r='4' fill='#a855f7'/>
  <line x1='180' y1='110' x2='430' y2='110' stroke='#a855f7' stroke-width='2.5'/>
  <circle cx='460' cy='110' r='28' fill='#0f172a' stroke='#eab308' stroke-width='2.5'/>
  <text x='460' y='114' fill='#eab308' font-size='12' font-weight='bold' text-anchor='middle'>AC Load</text>
</svg>'''

    elif any(k in lid for k in ['routh', 'control', 'stability', 'pid', 'feedback', 'bode', 'nyquist', 'state', 'cse-']):
        return f'''<svg viewBox='0 0 560 200' width='100%' height='auto' style='max-width:100%;display:block;margin:12px auto;background:#0f172a;border:1px solid #334155;border-radius:8px;' role='img' aria-label='{title_escaped} Diagram'>
  <rect width='560' height='200' fill='#0f172a' rx='8'/>
  <rect x='12' y='10' width='536' height='180' fill='#1e293b' stroke='#334155' stroke-width='1.5' rx='6'/>
  <text x='280' y='32' fill='#38bdf8' font-size='13' font-weight='bold' text-anchor='middle'>{title_escaped}</text>
  <text x='45' y='105' fill='#38bdf8' font-size='12' font-weight='bold'>R(s)</text>
  <line x1='75' y1='100' x2='120' y2='100' stroke='#38bdf8' stroke-width='2'/>
  <circle cx='135' cy='100' r='15' fill='#0f172a' stroke='#eab308' stroke-width='2'/>
  <text x='135' y='104' fill='#eab308' font-size='14' font-weight='bold' text-anchor='middle'>&#931;</text>
  <line x1='150' y1='100' x2='190' y2='100' stroke='#38bdf8' stroke-width='2'/>
  <rect x='190' y='80' width='70' height='40' fill='#0f172a' stroke='#22c55e' stroke-width='2' rx='4'/>
  <text x='225' y='104' fill='#22c55e' font-size='11' font-weight='bold' text-anchor='middle'>C(s)</text>
  <line x1='260' y1='100' x2='300' y2='100' stroke='#38bdf8' stroke-width='2'/>
  <rect x='300' y='80' width='80' height='40' fill='#0f172a' stroke='#a855f7' stroke-width='2' rx='4'/>
  <text x='340' y='104' fill='#a855f7' font-size='11' font-weight='bold' text-anchor='middle'>G(s) Plant</text>
  <line x1='380' y1='100' x2='470' y2='100' stroke='#38bdf8' stroke-width='2'/>
  <text x='480' y='105' fill='#38bdf8' font-size='12' font-weight='bold'>C(s)</text>
  <line x1='430' y1='100' x2='430' y2='160' stroke='#38bdf8' stroke-width='2'/>
  <line x1='430' y1='160' x2='270' y2='160' stroke='#38bdf8' stroke-width='2'/>
  <rect x='210' y='145' width='60' height='30' fill='#0f172a' stroke='#f43f5e' stroke-width='2' rx='4'/>
  <text x='240' y='164' fill='#f43f5e' font-size='10' font-weight='bold' text-anchor='middle'>H(s)</text>
  <line x1='210' y1='160' x2='135' y2='160' stroke='#38bdf8' stroke-width='2'/>
  <line x1='135' y1='160' x2='135' y2='115' stroke='#38bdf8' stroke-width='2'/>
</svg>'''

    elif any(k in lid for k in ['sensor', 'temperature', 'rtd', 'thermocouple', 'bridge', 'meter', 'measurement', 'instrument', 'err', 'oscilloscope', 'megger', 'earth']):
        return f'''<svg viewBox='0 0 560 200' width='100%' height='auto' style='max-width:100%;display:block;margin:12px auto;background:#0f172a;border:1px solid #334155;border-radius:8px;' role='img' aria-label='{title_escaped} Diagram'>
  <rect width='560' height='200' fill='#0f172a' rx='8'/>
  <rect x='12' y='10' width='536' height='180' fill='#1e293b' stroke='#334155' stroke-width='1.5' rx='6'/>
  <text x='280' y='32' fill='#38bdf8' font-size='13' font-weight='bold' text-anchor='middle'>{title_escaped}</text>
  <polygon points='280,50 360,105 280,160 200,105' fill='#0f172a' stroke='#38bdf8' stroke-width='2'/>
  <text x='230' y='70' fill='#22c55e' font-size='11' font-weight='bold'>R1</text>
  <text x='320' y='70' fill='#22c55e' font-size='11' font-weight='bold'>R2</text>
  <text x='230' y='145' fill='#22c55e' font-size='11' font-weight='bold'>R3</text>
  <text x='320' y='145' fill='#eab308' font-size='11' font-weight='bold'>R_x (Sensor)</text>
  <circle cx='280' cy='105' r='16' fill='#0f172a' stroke='#a855f7' stroke-width='2'/>
  <text x='280' y='109' fill='#a855f7' font-size='11' font-weight='bold' text-anchor='middle'>Null G</text>
  <line x1='200' y1='105' x2='264' y2='105' stroke='#a855f7' stroke-width='1.5'/>
  <line x1='296' y1='105' x2='360' y2='105' stroke='#a855f7' stroke-width='1.5'/>
  <line x1='280' y1='50' x2='280' y2='38' stroke='#f43f5e' stroke-width='2'/>
  <line x1='280' y1='160' x2='280' y2='172' stroke='#38bdf8' stroke-width='2'/>
</svg>'''

    elif any(k in lid for k in ['drive', 'braking', 'scalar', 'vector', 'foc', 'dc-motor', 'induction-motor', 'synchronous', 'potier', 'commutation', 'dc-machines', 'xfmr', 'machine', 'motor']):
        return f'''<svg viewBox='0 0 560 200' width='100%' height='auto' style='max-width:100%;display:block;margin:12px auto;background:#0f172a;border:1px solid #334155;border-radius:8px;' role='img' aria-label='{title_escaped} Diagram'>
  <rect width='560' height='200' fill='#0f172a' rx='8'/>
  <rect x='12' y='10' width='536' height='180' fill='#1e293b' stroke='#334155' stroke-width='1.5' rx='6'/>
  <text x='280' y='32' fill='#38bdf8' font-size='13' font-weight='bold' text-anchor='middle'>{title_escaped}</text>
  <rect x='60' y='75' width='100' height='60' fill='#0f172a' stroke='#38bdf8' stroke-width='2' rx='4'/>
  <text x='110' y='102' fill='#38bdf8' font-size='11' font-weight='bold' text-anchor='middle'>Power Converter</text>
  <text x='110' y='120' fill='#94a3b8' font-size='10' text-anchor='middle'>Drive Stage</text>
  <line x1='160' y1='95' x2='240' y2='95' stroke='#22c55e' stroke-width='2'/>
  <line x1='160' y1='105' x2='240' y2='105' stroke='#22c55e' stroke-width='2'/>
  <line x1='160' y1='115' x2='240' y2='115' stroke='#22c55e' stroke-width='2'/>
  <circle cx='280' cy='105' r='35' fill='#0f172a' stroke='#eab308' stroke-width='2.5'/>
  <text x='280' y='103' fill='#eab308' font-size='14' font-weight='bold' text-anchor='middle'>M</text>
  <text x='280' y='121' fill='#eab308' font-size='10' text-anchor='middle'>3-Phase</text>
  <line x1='315' y1='105' x2='400' y2='105' stroke='#e2e8f0' stroke-width='4'/>
  <rect x='400' y='80' width='90' height='50' fill='#0f172a' stroke='#a855f7' stroke-width='2' rx='4'/>
  <text x='445' y='110' fill='#a855f7' font-size='11' font-weight='bold' text-anchor='middle'>Mechanical Load</text>
</svg>'''

    elif any(k in lid for k in ['hvdc', 'transmission', 'grid', 'power', 'load', 'forecasting', 'hydrogen', 'etap', 'safety', 'loto', 'ppe', 'earth', 'substation', 'generation']):
        return f'''<svg viewBox='0 0 560 200' width='100%' height='auto' style='max-width:100%;display:block;margin:12px auto;background:#0f172a;border:1px solid #334155;border-radius:8px;' role='img' aria-label='{title_escaped} Diagram'>
  <rect width='560' height='200' fill='#0f172a' rx='8'/>
  <rect x='12' y='10' width='536' height='180' fill='#1e293b' stroke='#334155' stroke-width='1.5' rx='6'/>
  <text x='280' y='32' fill='#38bdf8' font-size='13' font-weight='bold' text-anchor='middle'>{title_escaped}</text>
  <circle cx='70' cy='105' r='25' fill='#0f172a' stroke='#38bdf8' stroke-width='2'/>
  <text x='70' y='109' fill='#38bdf8' font-size='12' font-weight='bold' text-anchor='middle'>Gen</text>
  <line x1='95' y1='105' x2='150' y2='105' stroke='#38bdf8' stroke-width='2'/>
  <rect x='150' y='80' width='70' height='50' fill='#0f172a' stroke='#22c55e' stroke-width='2' rx='4'/>
  <text x='185' y='109' fill='#22c55e' font-size='10' font-weight='bold' text-anchor='middle'>Substation</text>
  <line x1='220' y1='105' x2='340' y2='105' stroke='#eab308' stroke-width='2.5'/>
  <text x='280' y='95' fill='#eab308' font-size='11' font-weight='bold' text-anchor='middle'>Transmission Line</text>
  <rect x='340' y='80' width='70' height='50' fill='#0f172a' stroke='#a855f7' stroke-width='2' rx='4'/>
  <text x='375' y='109' fill='#a855f7' font-size='10' font-weight='bold' text-anchor='middle'>Grid Center</text>
  <line x1='410' y1='105' x2='460' y2='105' stroke='#38bdf8' stroke-width='2'/>
  <rect x='460' y='85' width='50' height='40' fill='#0f172a' stroke='#f43f5e' stroke-width='2' rx='4'/>
  <text x='485' y='109' fill='#f43f5e' font-size='11' font-weight='bold' text-anchor='middle'>Load</text>
</svg>'''

    else:
        return f'''<svg viewBox='0 0 560 200' width='100%' height='auto' style='max-width:100%;display:block;margin:12px auto;background:#0f172a;border:1px solid #334155;border-radius:8px;' role='img' aria-label='{title_escaped} Diagram'>
  <rect width='560' height='200' fill='#0f172a' rx='8'/>
  <rect x='12' y='10' width='536' height='180' fill='#1e293b' stroke='#334155' stroke-width='1.5' rx='6'/>
  <text x='280' y='32' fill='#38bdf8' font-size='13' font-weight='bold' text-anchor='middle'>{title_escaped}</text>
  <rect x='50' y='75' width='110' height='60' fill='#0f172a' stroke='#38bdf8' stroke-width='2' rx='4'/>
  <text x='105' y='104' fill='#38bdf8' font-size='11' font-weight='bold' text-anchor='middle'>Input Stage</text>
  <text x='105' y='120' fill='#94a3b8' font-size='10' text-anchor='middle'>Sensors / Data</text>
  <line x1='160' y1='105' x2='210' y2='105' stroke='#38bdf8' stroke-width='2'/>
  <rect x='210' y='75' width='140' height='60' fill='#0f172a' stroke='#22c55e' stroke-width='2' rx='4'/>
  <text x='280' y='104' fill='#22c55e' font-size='11' font-weight='bold' text-anchor='middle'>Processing Unit</text>
  <text x='280' y='120' fill='#94a3b8' font-size='10' text-anchor='middle'>Core Architecture</text>
  <line x1='350' y1='105' x2='400' y2='105' stroke='#38bdf8' stroke-width='2'/>
  <rect x='400' y='75' width='110' height='60' fill='#0f172a' stroke='#a855f7' stroke-width='2' rx='4'/>
  <text x='455' y='104' fill='#a855f7' font-size='11' font-weight='bold' text-anchor='middle'>Output Control</text>
  <text x='455' y='120' fill='#94a3b8' font-size='10' text-anchor='middle'>Actuators / System</text>
</svg>'''

# Part B: Find exact generic SVG blocks and replace them safely
matches = [m.start() for m in re.finditer(r'Load Z', html)]
print(f"Part B: Found {len(matches)} generic SVG positions.")

svg_blocks = []
for pos_m in matches:
    start = html.rfind('<svg', 0, pos_m)
    end = html.find('</svg>', pos_m)
    if start != -1 and end != -1 and html.rfind('</svg>', start, pos_m) == -1:
        end += len('</svg>')
        svg_text = html[start:end]
        svg_blocks.append((start, end, svg_text))

print(f"Extracted {len(svg_blocks)} exact SVG blocks.")

# Process replacements from back to front to preserve positions
new_html = html
replacements_count = 0

for start, end, svg_text in reversed(svg_blocks):
    snippet_before = html[max(0, start-8000):start]
    
    found_lids = []
    for lid, ldata in active_lessons.items():
        if f'"{lid}"' in snippet_before or f"'{lid}'" in snippet_before or f'id: "{lid}"' in snippet_before:
            idx = max(snippet_before.rfind(f'"{lid}"'), snippet_before.rfind(f"'{lid}'"))
            found_lids.append((idx, lid, ldata.get('title', '')))
    
    if found_lids:
        found_lids.sort()
        best_lid = found_lids[-1][1]
        title = found_lids[-1][2]
    else:
        title_match = re.search(r'<text[^>]*y=[\'"]32[\'"][^>]*>([^<]+)</text>', svg_text)
        title = title_match.group(1) if title_match else "Technical Visual Diagram"
        best_lid = "generic-visual"

    new_svg = "".join(generate_topic_svg(best_lid, title).splitlines())
    new_html = new_html[:start] + new_svg + new_html[end:]
    replacements_count += 1

print(f"Part B: Replaced {replacements_count} SVG blocks with topic-specific technical diagrams.")

# Save updated HTML
with open('eee-platform.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Saved updated eee-platform.html")
