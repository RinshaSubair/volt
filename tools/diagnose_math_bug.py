import sys, json, re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8000/eee-platform.html")
    page.wait_for_function("typeof LESSONS !== 'undefined'")
    page.wait_for_timeout(500)

    # Let's inspect lessons that have equations like e = (v \times B) or R_a = \frac{Zr_c}{A}
    lesson_ids = page.evaluate("Object.keys(LESSONS)")
    
    print("=== SEARCHING FOR LESSONS WITH MATH DEFECTS / TEX STRINGS ===")
    
    sample_ids = [
        'dcm-emf-torque-derivation', 'dcm-armature-reaction', 'dcm-commutation-process',
        'dcm-lap-wave-windings', 'xfmr-losses-efficiency', 'sse-h-parameter-models',
        'sse-jfet-mosfet-biasing', 'ac-alt-emf-equation'
    ]

    for lid in sample_ids:
        if lid not in lesson_ids:
            # find closest id in LESSONS
            matches = [x for x in lesson_ids if any(k in x for k in lid.split('-')[:2])]
            print(f"ID {lid} not exact, closest in LESSONS: {matches[:3]}")
            if matches:
                lid = matches[0]

        page.evaluate(f"window.location.hash = '#/lesson/{lid}'")
        page.wait_for_timeout(400)

        dom_info = page.evaluate("""(lid) => {
            const container = document.querySelector('.card, .lesson-content-area, main, #app') || document.body;
            if(typeof renderMath !== 'undefined') renderMath(container);

            const redSpans = Array.from(container.querySelectorAll('.katex-error, [style*="rgb(204, 0, 0)"]')).map(el => ({
                text: el.innerText || el.textContent,
                html: el.outerHTML.slice(0, 200),
                parentHTML: el.parentElement ? el.parentElement.outerHTML.slice(0, 300) : ''
            }));

            // Find all raw TeX text nodes
            const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
            const rawTeXNodes = [];
            let n;
            while(n = walker.nextNode()) {
                if(/\\\\(?:times|theta|frac|text|cdot|sqrt|Omega)/.test(n.nodeValue)) {
                    rawTeXNodes.push({
                        val: n.nodeValue,
                        parentTag: n.parentElement ? n.parentElement.tagName : '',
                        parentCls: n.parentElement ? n.parentElement.className : '',
                        parentHTML: n.parentElement ? n.parentElement.outerHTML.slice(0, 250) : ''
                    });
                }
            }

            return {
                id: lid,
                redSpans: redSpans,
                rawNodes: rawTeXNodes.slice(0, 5)
            };
        }""", lid)

        print(f"\n--- Lesson: {lid} ---")
        print(f"  Red KaTeX Spans Count: {len(dom_info['redSpans'])}")
        for r in dom_info['redSpans'][:3]:
            print(f"    Red Text: {repr(r['text'])}")
            print(f"    Parent HTML: {repr(r['parentHTML'])}\n")
        print(f"  Raw TeX Text Nodes Count: {len(dom_info['rawNodes'])}")
        for rn in dom_info['rawNodes']:
            print(f"    Val: {repr(rn['val'])}")
            print(f"    Tag: {rn['parentTag']} Cls: {repr(rn['parentCls'])}")
            print(f"    HTML: {repr(rn['parentHTML'])}\n")

    browser.close()
