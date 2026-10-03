import sys, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

part6_expressions = [
    r"$R_a$",
    r"$e = (v \times B)l$",
    r"$e = Blv\sin\theta$",
    r"$\frac{Z}{A}$",
    r"$\text{total coils}$",
    r"$Y_p = \frac{S}{P}$",
    r"$Y_b = \frac{2Z}{P} \pm k$",
    r"$Y_f = Y_b \pm 2m$",
    r"$A = P$",
    r"$A = 2$",
    r"$g_m = \frac{\partial I_D}{\partial V_{GS}}$",
    r"$F = I_c l B \sin\theta$",
    r"$Q = ne$",
    r"$F = \frac{1}{4\pi\epsilon_0}\frac{|q_1q_2|}{r^2}$",
    r"$V_G = V_{DD}\frac{R_2}{R_1+R_2}$"
]

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8000/eee-platform.html")
    page.wait_for_function("typeof LESSONS !== 'undefined'")
    page.wait_for_timeout(500)

    print("=== TESTING PART 6 REQUIRED MATH EXPRESSIONS ===")

    results = page.evaluate("""(exprs) => {
        const testContainer = document.createElement('div');
        testContainer.id = 'part6-test-container';
        document.body.appendChild(testContainer);

        const res = [];

        exprs.forEach((expr, idx) => {
            const div = document.createElement('div');
            div.className = 'test-expr-box';
            div.innerHTML = expr;
            testContainer.appendChild(div);

            // Trigger renderMath
            if(typeof renderMath !== 'undefined') renderMath(div);

            const text = div.innerText;
            const html = div.innerHTML;

            const hasRawTex = /\\\\(?:frac|text|times|theta|partial|sqrt|Omega)/.test(text);
            const redSpans = Array.from(div.querySelectorAll('.katex-error, [style*="rgb(204, 0, 0)"]')).map(e => e.outerHTML);
            const hasKatex = !!div.querySelector('.katex');

            res.push({
                idx: idx + 1,
                expr: expr,
                renderedText: text,
                hasKatex: hasKatex,
                hasRawTex: hasRawTex,
                redSpansCount: redSpans.length,
                redSpans: redSpans,
                htmlSnippet: html.slice(0, 150)
            });
        });

        document.body.removeChild(testContainer);
        return res;
    }""", part6_expressions)

    all_pass = True
    for r in results:
        status = "PASS" if (r['hasKatex'] and not r['hasRawTex'] and r['redSpansCount'] == 0) else "FAIL"
        if status == "FAIL": all_pass = False
        print(f"[{status}] Expr #{r['idx']}: {r['expr']}")
        print(f"       Rendered Text: {repr(r['renderedText'])}")
        print(f"       KaTeX Present: {r['hasKatex']}, Raw TeX: {r['hasRawTex']}, Red Spans: {r['redSpansCount']}")
        if r['redSpans']:
            print(f"       Red Span HTML: {repr(r['redSpans'][0])}")
        print("-" * 50)

    print(f"\nPart 6 Expressions Overall Test Status: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
    browser.close()
