import sys, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8000/eee-platform.html")
    page.wait_for_function("typeof LESSONS !== 'undefined'")
    page.wait_for_timeout(500)

    comparison = page.evaluate("""() => {
        // Test 1: $R_a$
        const div1 = document.createElement('div');
        div1.id = 'working-token';
        div1.innerHTML = '$R_a$';
        document.body.appendChild(div1);

        // Test 2: $\\frac{Z}{A}$
        const div2 = document.createElement('div');
        div2.id = 'failing-token';
        div2.innerHTML = '$\\\\frac{Z}{A}$';
        document.body.appendChild(div2);

        const before1 = { innerHTML: div1.innerHTML, textContent: div1.textContent };
        const before2 = { innerHTML: div2.innerHTML, textContent: div2.textContent };

        // Call repairLatex on math string
        const mathStr1 = '$R_a$';
        const mathStr2 = '$\\\\frac{Z}{A}$';

        const repaired1 = typeof repairLatex !== 'undefined' ? repairLatex(mathStr1) : mathStr1;
        const repaired2 = typeof repairLatex !== 'undefined' ? repairLatex(mathStr2) : mathStr2;

        // Run renderMath
        if(typeof renderMath !== 'undefined') {
            renderMath(div1);
            renderMath(div2);
        }

        const after1 = { innerHTML: div1.innerHTML, textContent: div1.textContent, katexError: div1.querySelector('.katex-error') ? div1.querySelector('.katex-error').outerHTML : null };
        const after2 = { innerHTML: div2.innerHTML, textContent: div2.textContent, katexError: div2.querySelector('.katex-error') ? div2.querySelector('.katex-error').outerHTML : null };

        // Test direct katex.render on repaired string
        let direct1 = null, direct2 = null, directError1 = null, directError2 = null;
        if(typeof katex !== 'undefined') {
            const span1 = document.createElement('span');
            try { katex.render('R_a', span1, { throwOnError: false }); direct1 = span1.innerHTML; } catch(e) { directError1 = e.message; }

            const span2 = document.createElement('span');
            try { katex.render(repairLatex('\\\\frac{Z}{A}'), span2, { throwOnError: false }); direct2 = span2.innerHTML; directError2 = span2.querySelector('.katex-error') ? span2.querySelector('.katex-error').outerHTML : null; } catch(e) { directError2 = e.message; }
        }

        document.body.removeChild(div1);
        document.body.removeChild(div2);

        return {
            token1: { input: mathStr1, repaired: repaired1, before: before1, after: after1, direct: direct1, directError: directError1 },
            token2: { input: mathStr2, repaired: repaired2, before: before2, after: after2, direct: direct2, directError: directError2 }
        };
    }""")

    print("========================================================")
    print("DOM COMPARISON: WORKING TOKEN vs FAILING TOKEN")
    print("========================================================")
    
    t1 = comparison['token1']
    print("\n--- WORKING TOKEN: $R_a$ ---")
    print(f"  Input: {t1['input']}")
    print(f"  Repaired string: {t1['repaired']}")
    print(f"  Before renderMath innerHTML: {t1['before']['innerHTML']}")
    print(f"  After renderMath innerHTML snippet: {t1['after']['innerHTML'][:200]}")
    print(f"  KaTeX Error Span: {t1['after']['katexError']}")

    t2 = comparison['token2']
    print("\n--- FAILING TOKEN: $\\frac{Z}{A}$ ---")
    print(f"  Input: {t2['input']}")
    print(f"  Repaired string: {t2['repaired']}")
    print(f"  Before renderMath innerHTML: {t2['before']['innerHTML']}")
    print(f"  After renderMath innerHTML snippet: {t2['after']['innerHTML'][:250]}")
    print(f"  KaTeX Error Span: {t2['after']['katexError']}")
    print(f"  Direct katex.render error span: {t2['directError']}")

    browser.close()
