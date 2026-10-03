import sys, json, re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

lessons_to_check = [
    'dc-emf-torque',
    'dc-gen-armature-reaction',
    'xfmr-losses-allday-efficiency',
    'pe-1ph-half-bridge-inverter',
    'ac-alt-emf',
    'ct-kcl-kvl-node-mesh'
]

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8000/eee-platform.html")
    page.wait_for_function("typeof LESSONS !== 'undefined'")
    page.wait_for_timeout(500)

    for lid in lessons_to_check:
        print(f"\n==========================================")
        print(f"LESSON: {lid}")
        print(f"==========================================")
        page.evaluate(f"window.location.hash = '#/lesson/{lid}'")
        page.wait_for_timeout(500)

        info = page.evaluate("""() => {
            const container = document.querySelector('.card, .lesson-content-area, main, #app') || document.body;
            if(typeof renderMath !== 'undefined') renderMath(container);

            const text = container.innerText;
            const html = container.innerHTML;

            // Search for raw TeX keywords in innerText
            const rawTexMatches = text.match(/\\\\(?:frac|text|times|theta|cdot|sqrt|Omega|partial|sum|left|right|begin|end)/g) || [];
            
            // Search for red KaTeX error spans
            const redSpans = Array.from(container.querySelectorAll('.katex-error, [style*="rgb(204, 0, 0)"]')).map(el => el.outerHTML);

            // Find SVG diagram title & labels
            const svg = container.querySelector('svg');
            let svgTitle = '';
            let svgTexts = [];
            if(svg) {
                const t = svg.querySelector('text');
                svgTitle = t ? t.textContent : '';
                svgTexts = Array.from(svg.querySelectorAll('text')).map(el => el.textContent.strip ? el.textContent.strip() : el.textContent);
            }

            return {
                rawTexMatches: rawTexMatches,
                redSpans: redSpans,
                svgTitle: svgTitle,
                svgTexts: svgTexts.slice(0, 10),
                textSnippet: text.slice(0, 400),
                htmlSnippet: html.slice(0, 600)
            };
        }""")

        print(f"Raw TeX Matches in visible text: {info['rawTexMatches']}")
        print(f"Red KaTeX Error Spans: {len(info['redSpans'])}")
        if info['redSpans']:
            print(f"  First Red Span: {repr(info['redSpans'][0])}")
        print(f"SVG Diagram Present: {'YES' if info['svgTitle'] else 'NO'}")
        if info['svgTitle']:
            print(f"  SVG Title: {repr(info['svgTitle'])}")
            print(f"  SVG Texts Sample: {info['svgTexts'][:5]}")
        print(f"\nText Snippet:\n{info['textSnippet'][:300]}")

    browser.close()
