import re

def clean_lesson_body(body):
    if not body:
        return body

    # 1. Clean triple/quadruple dollar signs $$$$ or $$$ -> $$
    body = re.sub(r'\${3,}', '$$', body)

    # 2. Fix raw $ inside \text{...}
    body = re.sub(r'(\\text\{[^}]*?)\$([^}]*?\})', r'\1USD\2', body)

    # 3. Fix unescaped & inside headings or text inside math blocks
    def clean_math_block(m):
        left, content, right = m.group(1), m.group(2), m.group(3)
        if any(env in content for env in ['bmatrix', 'pmatrix', 'vmatrix', 'cases', 'matrix', 'align', 'CD']):
            return left + content + right
        content = content.replace(' & ', ' \\& ')
        return left + content + right

    body = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', clean_math_block, body)

    # 4. Fix matrix single backslashes in source
    def fix_matrix_breaks(m):
        bm = m.group(0)
        bm = re.sub(r'(?<!\\)\\(?!begin|end|text|frac|times|theta|alpha|beta|gamma|delta|sqrt|partial|left|right|[a-zA-Z])', r'\\\\', bm)
        return bm

    body = re.sub(r'\\begin\{bmatrix\}[\s\S]*?\\end\{bmatrix\}', fix_matrix_breaks, body)

    return body

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print("Cleaning math delimiters and parse errors in all lessons...")
    pattern = re.compile(r'(body:\s*`)([\s\S]*?)(`\s*,\s*mcqIds)', re.MULTILINE)

    def replace_body(match):
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)
        fixed_body = clean_lesson_body(body)
        return prefix + fixed_body + suffix

    new_html = pattern.sub(replace_body, html)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

    print("All math parse errors cleaned successfully!")

if __name__ == '__main__':
    main()
