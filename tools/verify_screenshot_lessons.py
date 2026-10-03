import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

path = os.path.abspath('eee-platform.html').replace('\\', '/')
file_url = 'file:///' + path

lessons_to_check = [
    'dcm-armature-reaction',
    'sse-hparam-fet-amplifiers',
    'tfr-losses',
    'emt-biot-savart-ampere',
    'ac-alt-construction',
    'charge',
    'voltage-current-divider',
    'first-second-order-transient-time-response',
    'pe-intro-scope',
    'dsp-circular-convolution'
]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', headless=True)
    pg = b.new_page()
    pg.goto(file_url, wait_until='domcontentloaded')

    res = pg.evaluate('''ids => {
        const out = {};
        const genericKw = ['Input Stage', 'Processing Unit', 'Output Control', 'Sensors / Data', 'Core Architecture', 'Actuators / System', 'R_series', 'jX_L', 'Load Z'];
        
        ids.forEach(id => {
            if (LESSONS[id]) {
                const container = document.createElement('div');
                container.innerHTML = LESSONS[id].body;
                document.body.appendChild(container);
                if (typeof renderMath === 'function') renderMath(container);

                const errors = container.querySelectorAll('.katex-error').length;
                const txt = container.innerText || '';

                const rawFrac = txt.includes('\\frac');
                const rawText = txt.includes('\\text');
                const rawTimes = txt.includes('\\times');
                const rawTheta = txt.includes('\\theta');

                let hasGenericSvg = false;
                const svgs = container.querySelectorAll('svg');
                svgs.forEach(s => {
                    const sHtml = s.outerHTML;
                    genericKw.forEach(kw => {
                        if (sHtml.includes(kw)) hasGenericSvg = true;
                    });
                });

                out[id] = {
                    title: LESSONS[id].title,
                    errors,
                    rawFrac,
                    rawText,
                    rawTimes,
                    rawTheta,
                    svgCount: svgs.length,
                    hasGenericSvg
                };
                document.body.removeChild(container);
            }
        });
        return out;
    }''', lessons_to_check)

    print("="*80)
    print("BROWSER VERIFICATION FOR REQUIRED SCREENSHOT LESSONS:")
    print("="*80)
    for id, r in res.items():
        print(f"ID: {id}")
        print(f"  Title: {r['title']}")
        print(f"  KaTeX Errors: {r['errors']}")
        print(f"  Raw TeX Visible: Frac={r['rawFrac']}, Text={r['rawText']}, Times={r['rawTimes']}, Theta={r['rawTheta']}")
        print(f"  SVGs Present: {r['svgCount']}, Generic Fallback SVG: {r['hasGenericSvg']}")
        print("-" * 60)

    b.close()
