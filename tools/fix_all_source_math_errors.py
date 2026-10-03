import re

def clean_body_text(body):
    if not body:
        return body

    # 1. Replace 3 or 4 trailing dollar signs like }$$$ or }$$$$ with }$$
    body = re.sub(r'\}\${2,}', '}$$', body)
    body = re.sub(r'\${3,}', '$$', body)

    # 2. Replace raw $ inside \text{...} like \text{demand [$/kW]} -> \text{demand [/kW]}
    body = re.sub(r'(\\text\{[^}]*?)\$([^}]*?\})', r'\1/kW\2', body)

    # 3. Replace unescaped & inside headings or text inside math blocks
    def fix_math_block(match):
        left = match.group(1)
        content = match.group(2)
        right = match.group(3)
        # If block contains cases or bmatrix, don't replace & in column separators
        if any(env in content for env in ['bmatrix', 'pmatrix', 'vmatrix', 'cases', 'matrix', 'align', 'CD']):
            return left + content + right
        content = content.replace(' & ', ' \\& ')
        return left + content + right

    body = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', fix_math_block, body)

    # 4. Fix bmatrix single backslash in source: \begin{bmatrix} a \ b \end{bmatrix} -> \begin{bmatrix} a \\ b \end{bmatrix}
    def fix_bmatrix(match):
        bm = match.group(0)
        # Replace single \ with \\ between elements if not a command like \text
        bm = re.sub(r'(?<!\\)\\(?!begin|end|text|frac|times|theta|alpha|beta|gamma|delta|sqrt|partial|left|right|[a-zA-Z])', r'\\\\', bm)
        return bm

    body = re.sub(r'\\begin\{bmatrix\}[\s\S]*?\\end\{bmatrix\}', fix_bmatrix, body)

    return body

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print("Cleaning math source data across eee-platform.html...")

    # Pattern to match body property in LESSONS
    # E.g. body: `...`
    pattern = re.compile(r'(body:\s*`)([\s\S]*?)(`\s*,\s*mcqIds)', re.MULTILINE)

    count = 0
    def replacer(m):
        nonlocal count
        count += 1
        return m.group(1) + clean_body_text(m.group(2)) + m.group(3)

    new_html = pattern.sub(replacer, html)
    print(f"Processed {count} lesson body fields.")

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

    print("Saved clean source data!")

if __name__ == '__main__':
    main()
