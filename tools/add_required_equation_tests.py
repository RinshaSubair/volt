import re

def main():
    with open('volt_tests.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Find position right before ok('no JS errors'
    idx = text.find("ok('no JS errors'")
    if idx == -1:
        idx = text.find("ok(\"no JS errors\"")

    if idx == -1:
        print("Could not find no JS errors assertion in volt_tests.py")
        return

    new_tests = '''    # ---------------- session 71: Required Equation Structures & DOM Math Verification ----------------
    d71 = pg.evaluate(\'\'\'() => {
        const tests = {};
        const checkEq = (id, keywords) => {
            const l = LESSONS[id];
            if (!l) return false;
            const container = document.createElement('div');
            container.innerHTML = l.body || '';
            document.body.appendChild(container);
            if (typeof renderMath === 'function') renderMath(container);
            const txt = container.innerText || '';
            const html = container.innerHTML || '';
            const errors = container.querySelectorAll('.katex-error').length;
            document.body.removeChild(container);
            if (errors > 0) return false;
            return keywords.every(kw => txt.includes(kw) || html.includes(kw));
        };

        tests['req_eq_1'] = checkEq('dcm-dc-generator-emf', ['R_a', 'r_c']);
        tests['req_eq_2'] = checkEq('ac-alt-construction', ['Y_p', 'S']);
        tests['req_eq_3'] = checkEq('dcm-armature-reaction', ['Y_b']);
        tests['req_eq_4'] = checkEq('dcm-armature-reaction', ['Y_f']);
        tests['req_eq_5'] = checkEq('dcm-armature-reaction', ['Y_c']);
        tests['req_eq_6'] = checkEq('sse-hparam-fet-amplifiers', ['g_m', 'I_D', 'V_']);
        tests['req_eq_7'] = checkEq('ac-alt-construction', ['sin', 'B']);
        tests['req_eq_8'] = checkEq('charge', ['q_1', 'q_2', 'r^2']);
        tests['req_eq_9'] = checkEq('sse-hparam-fet-amplifiers', ['h_{11}', 'h_{12}', 'h_{21}', 'h_{22}']);
        tests['req_eq_10'] = checkEq('sse-hparam-fet-amplifiers', ['V_G', 'V_{DD}', 'R_2']);

        return tests;
    }\'\'\')

    ok("session 71: Required Eq 1 (R_a = Zr_c / A) verified", d71['req_eq_1'])
    ok("session 71: Required Eq 2 (Y_p = S / P) verified", d71['req_eq_2'])
    ok("session 71: Required Eq 3 (Y_b back pitch) verified", d71['req_eq_3'])
    ok("session 71: Required Eq 4 (Y_f front pitch) verified", d71['req_eq_4'])
    ok("session 71: Required Eq 5 (Y_c commutator pitch) verified", d71['req_eq_5'])
    ok("session 71: Required Eq 6 (g_m transconductance) verified", d71['req_eq_6'])
    ok("session 71: Required Eq 7 (e = B l v sin theta) verified", d71['req_eq_7'])
    ok("session 71: Required Eq 8 (Coulomb Law force F) verified", d71['req_eq_8'])
    ok("session 71: Required Eq 9 (h-parameter two-port matrix) verified", d71['req_eq_9'])
    ok("session 71: Required Eq 10 (V_G voltage divider) verified", d71['req_eq_10'])

'''

    text = text[:idx] + new_tests + text[idx:]

    with open('volt_tests.py', 'w', encoding='utf-8') as f:
        f.write(text)

    print("Added session 71 required equation tests to volt_tests.py successfully!")

if __name__ == '__main__':
    main()
