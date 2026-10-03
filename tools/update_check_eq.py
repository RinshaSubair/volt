import re

def main():
    with open('volt_tests.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Find checkEq definition in volt_tests.py
    old_check_eq = '''        const checkEq = (id, keywords) => {
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
        };'''

    new_check_eq = '''        const checkEq = (id, keywords) => {
            const l = LESSONS[id];
            if (!l) return false;
            const rawBody = l.body || '';
            const hasRawKw = keywords.every(kw => rawBody.includes(kw));
            if (!hasRawKw) return false;

            const container = document.createElement('div');
            container.innerHTML = rawBody;
            document.body.appendChild(container);
            if (typeof renderMath === 'function') renderMath(container);
            const katexCount = container.querySelectorAll('.katex').length;
            const errors = container.querySelectorAll('.katex-error').length;
            document.body.removeChild(container);

            return katexCount > 0 && errors === 0;
        };'''

    if old_check_eq in text:
        text = text.replace(old_check_eq, new_check_eq)
        print("Updated checkEq in volt_tests.py!")
    else:
        print("Could not find exact old_check_eq block")

    with open('volt_tests.py', 'w', encoding='utf-8') as f:
        f.write(text)

    print("volt_tests.py checkEq updated successfully!")

if __name__ == '__main__':
    main()
