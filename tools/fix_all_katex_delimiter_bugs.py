import re

def clean_body_delimiters(body):
    if not body:
        return body

    # 1. Replace any $$$ or $$$$ with $$
    body = re.sub(r'\${3,}', '$$', body)

    # 2. Fix trailing dollar sign glued to closing $$ e.g. \text{foo}}$$$ or \text{foo}}$ -> \text{foo}}$$
    body = re.sub(r'(\$\$[^\$]+?\})\$+\$\$', r'\1$$', body)
    body = re.sub(r'(\$\$[^\$]+?)\$+\$\$', r'\1$$', body)

    # 3. Clean raw $ inside \text{...}
    body = re.sub(r'(\\text\{[^}]*?)\$([^}]*?\})', r'\1/kW\2', body)

    # 4. Clean unescaped & in non-matrix math blocks
    def clean_math_block(match):
        left, content, right = match.group(1), match.group(2), match.group(3)
        if any(env in content for env in ['bmatrix', 'pmatrix', 'vmatrix', 'cases', 'matrix', 'align', 'CD']):
            return left + content + right
        content = content.replace(' & ', ' \\& ')
        return left + content + right

    body = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', clean_math_block, body)

    # 5. Clean unescaped % inside math blocks
    def clean_percent(match):
        left, content, right = match.group(1), match.group(2), match.group(3)
        content = re.sub(r'(?<!\\)%', r'\%', content)
        return left + content + right

    body = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', clean_percent, body)

    # 6. Fix matrix row separators: \begin{bmatrix} a \ b \end{bmatrix} -> \begin{bmatrix} a \\ b \end{bmatrix}
    def fix_matrix(match):
        bm = match.group(0)
        # replace single \ with \\ if not a command
        bm = re.sub(r'(?<!\\)\\(?!begin|end|text|frac|times|theta|alpha|beta|gamma|delta|sqrt|partial|left|right|[a-zA-Z])', r'\\\\', bm)
        return bm

    body = re.sub(r'\\begin\{bmatrix\}[\s\S]*?\\end\{bmatrix\}', fix_matrix, body)

    return body

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print("Cleaning all KaTeX delimiter bugs across entire file...")
    # Clean in backtick body strings
    p1 = re.compile(r'(body:\s*`)([\s\S]*?)(`)', re.MULTILINE)
    # Clean in double quote body strings
    p2 = re.compile(r'("body":\s*")([\s\S]*?)(")', re.MULTILINE)

    html = p1.sub(lambda m: m.group(1) + clean_body_delimiters(m.group(2)) + m.group(3), html)
    html = p2.sub(lambda m: m.group(1) + clean_body_delimiters(m.group(2)) + m.group(3), html)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("All KaTeX delimiter bugs cleaned successfully!")

if __name__ == '__main__':
    main()
