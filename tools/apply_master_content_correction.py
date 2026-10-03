import re
import json
import sys

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Clean control characters from source text
    print("Cleaning control character corruptions...")
    html = html.replace('\x09ext', r'\\text')
    html = html.replace('\x09imes', r'\\times')
    html = html.replace('\x09heta', r'\\theta')
    html = html.replace('\x09au', r'\\tau')
    html = html.replace('\x09an', r'\\tan')
    html = html.replace('\x09anh', r'\\tanh')
    html = html.replace('\x09ilde', r'\\tilde')
    html = html.replace('\x09op', r'\\top')
    html = html.replace('\x09o', r'\\to')
    html = html.replace('\x0c', r'\\f')
    html = html.replace('\x08', r'\\b')
    html = html.replace('\x07', r'\\a')
    html = html.replace('\x0b', r'\\v')
    html = html.replace('\x09', r'\\t')

    # 2. Fix specific malformed equations mentioned by user
    print("Fixing explicit malformed math expressions...")
    
    html = html.replace(
        r"\text{PolePitch(Yp)} = \frac\text{TotalSlots(S)}P = \frac{Z2P}\text{coilsides}",
        r"\( Y_p = \frac{\text{Total Slots } (S)}{P} = \frac{S}{P} \)"
    )
    html = html.replace(
        r"\text{PolePitch(Yp)}=\frac\text{TotalSlots(S)}P",
        r"\( Y_p = \frac{S}{P} \)"
    )
    html = html.replace(
        r"R_a = \frac{Z/A} \cdot r_c A",
        r"\( R_a = \frac{Z \, r_c}{A^2} = \left(\frac{Z}{A}\right) r_c \)"
    )
    html = html.replace(
        r"\begin{bmatrix} v_1 i_2 \end{bmatrix}",
        r"\[ \begin{bmatrix} v_1 \\ i_2 \end{bmatrix} = \begin{bmatrix} h_{11} & h_{12} \\ h_{21} & h_{22} \end{bmatrix} \begin{bmatrix} i_1 \\ v_2 \end{bmatrix} \]"
    )
    html = html.replace(
        r"R_a = \frac{Z/A}",
        r"\( R_a = \frac{Z r_c}{A} \)"
    )

    # 3. Topic-Specific Technical SVGs
    print("Replacing generic visual fallbacks with topic-specific technical SVGs...")

    topic_svgs = {
        'ac-alt-construction': '''<svg viewBox="0 0 600 300" width="100%" height="260" xmlns="http://www.w3.org/2000/svg"><rect width="600" height="300" fill="#0f172a" rx="8"/><circle cx="250" cy="150" r="110" fill="none" stroke="#38bdf8" stroke-width="4"/><circle cx="250" cy="150" r="70" fill="#1e293b" stroke="#f59e0b" stroke-width="3"/><circle cx="250" cy="150" r="25" fill="#334155" stroke="#94a3b8" stroke-width="2"/><text x="250" y="155" fill="#f8fafc" font-family="sans-serif" font-size="12" text-anchor="middle">Shaft</text><text x="250" y="105" fill="#f59e0b" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="middle">N Pole</text><text x="250" y="205" fill="#f59e0b" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="middle">S Pole</text><text x="250" y="28" fill="#38bdf8" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle">Stator Core &amp; 3-Phase Slot Windings</text><circle cx="250" cy="40" r="6" fill="#ef4444"/><circle cx="360" cy="150" r="6" fill="#22c55e"/><circle cx="250" cy="260" r="6" fill="#3b82f6"/><path d="M 420 80 Q 460 30 500 80 T 580 80" fill="none" stroke="#ef4444" stroke-width="2"/><path d="M 420 150 Q 460 100 500 150 T 580 150" fill="none" stroke="#22c55e" stroke-width="2"/><path d="M 420 220 Q 460 170 500 220 T 580 220" fill="none" stroke="#3b82f6" stroke-width="2"/><text x="500" y="30" fill="#f8fafc" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">3-Phase Output EMF</text><text x="550" y="75" fill="#ef4444" font-family="sans-serif" font-size="11">e_A</text><text x="550" y="145" fill="#22c55e" font-family="sans-serif" font-size="11">e_B</text><text x="550" y="215" fill="#3b82f6" font-family="sans-serif" font-size="11">e_C</text></svg>''',
        
        'emt-biot-savart-ampere': '''<svg viewBox="0 0 600 300" width="100%" height="260" xmlns="http://www.w3.org/2000/svg"><rect width="600" height="300" fill="#0f172a" rx="8"/><path d="M 100 250 L 100 50" stroke="#38bdf8" stroke-width="5" marker-end="url(#arrow)"/><text x="80" y="150" fill="#38bdf8" font-family="sans-serif" font-size="14" font-weight="bold">Current I</text><circle cx="100" cy="150" r="6" fill="#ef4444"/><text x="115" y="155" fill="#ef4444" font-family="sans-serif" font-size="12">I dℓ</text><line x1="100" y1="150" x2="280" y2="100" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4"/><text x="190" y="115" fill="#f59e0b" font-family="sans-serif" font-size="12">Vector r</text><circle cx="280" cy="100" r="5" fill="#38bdf8"/><text x="295" y="105" fill="#f8fafc" font-family="sans-serif" font-size="13" font-weight="bold">Point P</text><path d="M 280 100 L 260 50" stroke="#22c55e" stroke-width="3"/><text x="270" y="45" fill="#22c55e" font-family="sans-serif" font-size="13" font-weight="bold">d B = (μ_0 I / 4π r²) dℓ × r̂</text><ellipse cx="480" cy="150" rx="70" ry="90" fill="none" stroke="#a855f7" stroke-width="3" stroke-dasharray="6"/><line x1="480" y1="260" x2="480" y2="40" stroke="#38bdf8" stroke-width="4"/><text x="490" y="70" fill="#38bdf8" font-family="sans-serif" font-size="13" font-weight="bold">Enclosed Current I_enc</text><text x="480" y="270" fill="#a855f7" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Closed Amperian Loop (∮ B·dℓ = μ_0 I_enc)</text></svg>''',

        'emt-coulombs-law-fields': '''<svg viewBox="0 0 600 280" width="100%" height="250" xmlns="http://www.w3.org/2000/svg"><rect width="600" height="280" fill="#0f172a" rx="8"/><circle cx="150" cy="140" r="30" fill="#ef4444"/><text x="150" y="146" fill="#ffffff" font-family="sans-serif" font-size="18" font-weight="bold" text-anchor="middle">+q₁</text><circle cx="450" cy="140" r="30" fill="#3b82f6"/><text x="450" y="146" fill="#ffffff" font-family="sans-serif" font-size="18" font-weight="bold" text-anchor="middle">-q₂</text><line x1="180" y1="140" x2="420" y2="140" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5"/><text x="300" y="130" fill="#f8fafc" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle">Distance r</text><path d="M 180 140 Q 300 80 420 140" fill="none" stroke="#38bdf8" stroke-width="2"/><path d="M 180 140 Q 300 200 420 140" fill="none" stroke="#38bdf8" stroke-width="2"/><text x="300" y="40" fill="#38bdf8" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle">Electric Force F = (1 / 4πε₀) · (|q₁ q₂| / r²)</text><text x="80" y="145" fill="#22c55e" font-family="sans-serif" font-size="13" font-weight="bold">F_21 (Attraction)</text><text x="490" y="145" fill="#22c55e" font-family="sans-serif" font-size="13" font-weight="bold">F_12 (Attraction)</text></svg>''',

        'charge': '''<svg viewBox="0 0 600 280" width="100%" height="250" xmlns="http://www.w3.org/2000/svg"><rect width="600" height="280" fill="#0f172a" rx="8"/><circle cx="150" cy="140" r="30" fill="#ef4444"/><text x="150" y="146" fill="#ffffff" font-family="sans-serif" font-size="18" font-weight="bold" text-anchor="middle">+q₁</text><circle cx="450" cy="140" r="30" fill="#3b82f6"/><text x="450" y="146" fill="#ffffff" font-family="sans-serif" font-size="18" font-weight="bold" text-anchor="middle">-q₂</text><line x1="180" y1="140" x2="420" y2="140" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5"/><text x="300" y="130" fill="#f8fafc" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle">Distance r</text><path d="M 180 140 Q 300 80 420 140" fill="none" stroke="#38bdf8" stroke-width="2"/><path d="M 180 140 Q 300 200 420 140" fill="none" stroke="#38bdf8" stroke-width="2"/><text x="300" y="40" fill="#38bdf8" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle">Electric Force F = (1 / 4πε₀) · (|q₁ q₂| / r²)</text><text x="80" y="145" fill="#22c55e" font-family="sans-serif" font-size="13" font-weight="bold">F_21 (Attraction)</text><text x="490" y="145" fill="#22c55e" font-family="sans-serif" font-size="13" font-weight="bold">F_12 (Attraction)</text></svg>''',

        'sse-hparam-fet-amplifiers': '''<svg viewBox="0 0 600 300" width="100%" height="260" xmlns="http://www.w3.org/2000/svg"><rect width="600" height="300" fill="#0f172a" rx="8"/><rect x="180" y="60" width="240" height="180" fill="#1e293b" stroke="#38bdf8" stroke-width="3" rx="6"/><text x="300" y="90" fill="#f8fafc" font-family="sans-serif" font-size="15" font-weight="bold" text-anchor="middle">Transistor h-Parameter Two-Port</text><line x1="50" y1="100" x2="180" y2="100" stroke="#38bdf8" stroke-width="3"/><line x1="50" y1="200" x2="180" y2="200" stroke="#38bdf8" stroke-width="3"/><circle cx="50" cy="100" r="5" fill="#38bdf8"/><circle cx="50" cy="200" r="5" fill="#38bdf8"/><text x="30" y="105" fill="#38bdf8" font-family="sans-serif" font-size="13" font-weight="bold">v₁</text><text x="110" y="90" fill="#f59e0b" font-family="sans-serif" font-size="12" font-weight="bold">i₁ →</text><line x1="420" y1="100" x2="550" y2="100" stroke="#38bdf8" stroke-width="3"/><line x1="420" y1="200" x2="550" y2="200" stroke="#38bdf8" stroke-width="3"/><circle cx="550" cy="100" r="5" fill="#38bdf8"/><circle cx="550" cy="200" r="5" fill="#38bdf8"/><text x="570" y="105" fill="#38bdf8" font-family="sans-serif" font-size="13" font-weight="bold">v₂</text><text x="470" y="90" fill="#f59e0b" font-family="sans-serif" font-size="12" font-weight="bold">← i₂</text><text x="240" y="140" fill="#22c55e" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">h₁₁ (h_ie)</text><text x="240" y="180" fill="#22c55e" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">h₁₂ v₂ (h_re)</text><text x="360" y="140" fill="#a855f7" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">h₂₁ i₁ (h_fe)</text><text x="360" y="180" fill="#a855f7" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">h₂₂ (h_oe)</text><text x="300" y="275" fill="#38bdf8" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">[v₁ ; i₂] = [h₁₁ h₁₂ ; h₂₁ h₂₂] · [i₁ ; v₂]</text></svg>'''
    }

    print("Updating topic-specific SVGs...")
    for lesson_id, svg_code in topic_svgs.items():
        pattern = re.compile(rf'"{re.escape(lesson_id)}":\s*\{{[\s\S]*?\n\s*\}},', re.MULTILINE)
        m = pattern.search(html)
        if m:
            block = m.group(0)
            block_sub = re.sub(r'<svg[\s\S]*?<\/svg>', svg_code, block)
            html = html.replace(block, block_sub)

    # 4. Remove ALL remaining generic SVGs containing any of the keywords
    print("Strictly purging all generic SVGs...")
    generic_kw = ['Input Stage', 'Processing Unit', 'Output Control', 'Sensors / Data', 'Core Architecture', 'Actuators / System', 'R_series', 'jX_L', 'Load Z', 'V_out']

    def remove_generic_svgs(match):
        svg_str = match.group(0)
        for kw in generic_kw:
            if kw in svg_str:
                return ""
        return svg_str

    html = re.sub(r'<svg[\s\S]*?<\/svg>', remove_generic_svgs, html)

    # Clean up empty parent wrapper containers if left behind
    html = re.sub(r'<div class="card" style="[^"]*"><div style="text-anchor:middle[^"]*">\s*<\/div><\/div>', '', html)

    # Save updated file
    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Purge completed successfully!")

if __name__ == '__main__':
    main()
