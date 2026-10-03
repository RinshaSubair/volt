import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8000/eee-platform.html")
    page.wait_for_function("typeof LESSONS !== 'undefined'")
    page.wait_for_timeout(500)

    debug_res = page.evaluate("""() => {
        const testStr = '\\\\frac{Z}{A}'; // in JS memory: \\frac{Z}{A}
        const repaired = repairLatex(testStr);

        // Test calling katex.render on repaired
        const span = document.createElement('span');
        let katexHTML = '';
        let katexError = false;
        try {
            katex.render(repaired, span, { throwOnError: false });
            katexHTML = span.innerHTML;
            katexError = span.innerHTML.includes('color:#cc0000') || span.innerHTML.includes('color: rgb(204, 0, 0)');
        } catch(e) {
            katexError = e.message;
        }

        return {
            original: testStr,
            repaired: repaired,
            katexError: katexError,
            katexHTML: katexHTML
        };
    }""")

    print("=== REPAIRLATEX STEP BY STEP DEBUG ===")
    print(f"Original JS String: {repr(debug_res['original'])}")
    print(f"Repaired String:   {repr(debug_res['repaired'])}")
    print(f"KaTeX Error:       {debug_res['katexError']}")
    print(f"KaTeX HTML:        {repr(debug_res['katexHTML'])}")

    browser.close()
