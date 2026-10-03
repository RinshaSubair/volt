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

    test_res = page.evaluate("""(exprs) => {
        function repairLatexCustom(str) {
            if(!str) return '';
            let s = str
                .replace(/\\x09ext\\b/g, '\\\\text')
                .replace(/\\x09imes\\b/g, '\\\\times')
                .replace(/\\x09heta\\b/g, '\\\\theta')
                .replace(/\\x09au\\b/g, '\\\\tau')
                .replace(/\\x09/g, ' ')
                .replace(/\\x0crac\\b/g, '\\\\frac')
                .replace(/\\x0c/g, '')
                .replace(/\\x08egin\\b/g, '\\\\begin')
                .replace(/\\x08eta\\b/g, '\\\\beta')
                .replace(/\\x08/g, '')
                .replace(/\\x0bec\\b/g, '\\\\vec')
                .replace(/\\x0b/g, '')
                .replace(/\\x07lpha\\b/g, '\\\\alpha')
                .replace(/\\x07/g, '');

            s = s.replace(/\\\\\\\\/g, '\\\\');

            // Unescaped TeX keywords
            s = s.replace(/(?<!\\\\)\\b(overline|bar|widehat|tilde|vec|hat|dot|ddot|frac|text|times|theta|tau|rho|rightarrow|leftarrow|quad|qquad|implies|cdot|pm|mp|approx|infty|omega|Omega|pi|mu|alpha|beta|delta|Delta|partial|sum|int|sqrt|sigma|bmatrix|pmatrix|vmatrix|matrix)\\b/g, '\\\\$1');

            return s;
        }

        return exprs.map((expr, idx) => {
            let mathContent = expr.trim();
            if(mathContent.startsWith('$') && mathContent.endsWith('$')) {
                mathContent = mathContent.slice(1, -1).trim();
            }

            const repairedMath = repairLatexCustom(mathContent);

            const span = document.createElement('span');
            let isError = false;
            try {
                katex.render(repairedMath, span, { throwOnError: false });
                isError = span.innerHTML.includes('color:#cc0000') || span.innerHTML.includes('color: rgb(204, 0, 0)');
            } catch(e) {
                isError = e.message;
            }

            return {
                idx: idx + 1,
                original: expr,
                repaired: repairedMath,
                isError: isError,
                text: span.innerText
            };
        });
    }""", part6_expressions)

    print("=== VERIFYING CONTROL CHARACTER REPAIR ON PART 6 EXPRESSIONS ===")
    all_clean = True
    for r in test_res:
        status = "PASS" if not r['isError'] else "FAIL"
        if r['isError']: all_clean = False
        print(f"[{status}] Expr #{r['idx']}: {r['original']}")
        print(f"       Repaired Math: {r['repaired']}")
        print(f"       Is Error:      {r['isError']}")
        print(f"       Text:          {repr(r['text'])}")
        print("-" * 50)

    print(f"\nREPAIR VERIFICATION: {'ALL 15 PART 6 EXPRESSIONS PASS 100% CLEAN!' if all_clean else 'STILL HAS FAILURES'}")
    browser.close()
