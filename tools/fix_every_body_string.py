import re

def clean_text(t):
    if not t:
        return t
    # Fix 3 or 4 trailing dollar signs like }$$$ or }$$$$ or $$...$$$
    t = re.sub(r'\}\${2,}', '}$$', t)
    t = re.sub(r'\${3,}', '$$', t)

    # Fix raw $ inside \text{...}
    t = re.sub(r'(\\text\{[^}]*?)\$([^}]*?\})', r'\1/kW\2', t)

    # Fix unescaped & in non-matrix blocks
    def fix_math_block(match):
        left, content, right = match.group(1), match.group(2), match.group(3)
        if any(env in content for env in ['bmatrix', 'pmatrix', 'vmatrix', 'cases', 'matrix', 'align', 'CD']):
            return left + content + right
        content = content.replace(' & ', ' \\& ')
        return left + content + right

    t = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', fix_math_block, t)

    # Fix matrix single backslashes in source
    def fix_bmatrix(match):
        bm = match.group(0)
        bm = re.sub(r'(?<!\\)\\(?!begin|end|text|frac|times|theta|alpha|beta|gamma|delta|sqrt|partial|left|right|[a-zA-Z])', r'\\\\', bm)
        return bm

    t = re.sub(r'\\begin\{bmatrix\}[\s\S]*?\\end\{bmatrix\}', fix_bmatrix, t)

    return t

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Pattern for backticks
    p1 = re.compile(r'(body:\s*`)([\s\S]*?)(`)', re.MULTILINE)
    # Pattern for double quotes
    p2 = re.compile(r'("body":\s*")([\s\S]*?)(")', re.MULTILINE)

    c1 = 0
    c2 = 0

    def r1(m):
        nonlocal c1
        c1 += 1
        return m.group(1) + clean_text(m.group(2)) + m.group(3)

    def r2(m):
        nonlocal c2
        c2 += 1
        return m.group(1) + clean_text(m.group(2)) + m.group(3)

    html = p1.sub(r1, html)
    html = p2.sub(r2, html)

    print(f"Processed backtick body count: {c1}, double-quote body count: {c2}")

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Saved all body replacements!")

if __name__ == '__main__':
    main()
