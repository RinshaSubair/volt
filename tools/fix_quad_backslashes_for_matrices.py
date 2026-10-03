import re

def fix_matrix_in_template_literal(body):
    if not body:
        return body

    # Fix \begin{bmatrix} ... \end{bmatrix} matrix row breaks in template literals
    def fix_bm(match):
        bm = match.group(0)
        # In template literals, replace single \ or double \\ between matrix items with \\\\
        # so JS evaluates it to \\ in DOM memory!
        bm = re.sub(r'(?<!\\)\\(?![a-zA-Z0-9_\{\}\s]*?begin|end|text|frac|times|theta|alpha|beta|gamma|delta|sqrt|partial|left|right)', r'\\\\\\\\', bm)
        bm = bm.replace(' \\ ', ' \\\\\\\\ ')
        return bm

    body = re.sub(r'\\begin\{(?:bmatrix|pmatrix|vmatrix|matrix|cases)\}[\s\S]*?\\end\{(?:bmatrix|pmatrix|vmatrix|matrix|cases)\}', fix_bm, body)
    return body

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print("Fixing template literal matrix row breaks across entire file...")
    p1 = re.compile(r'(body:\s*`)([\s\S]*?)(`)', re.MULTILINE)
    html = p1.sub(lambda m: m.group(1) + fix_matrix_in_template_literal(m.group(2)) + m.group(3), html)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Matrix row breaks fixed successfully!")

if __name__ == '__main__':
    main()
