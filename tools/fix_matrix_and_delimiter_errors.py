import re

def fix_body(body):
    if not body:
        return body

    # 1. Fix matrix single backslash: \begin{bmatrix} a \ b \end{bmatrix} -> \begin{bmatrix} a \\ b \end{bmatrix}
    def fix_bmatrix(m):
        content = m.group(0)
        # replace \ with \\ between items if single backslash
        content = content.replace(r' \ ', r' \\ ')
        content = content.replace(r'\ ', r'\\ ')
        return content

    body = re.sub(r'\\begin\{(?:bmatrix|pmatrix|vmatrix|matrix|cases)\}[\s\S]*?\\end\{(?:bmatrix|pmatrix|vmatrix|matrix|cases)\}', fix_bmatrix, body)

    # 2. Fix unescaped & inside headings in math mode
    def fix_math_block(m):
        left, content, right = m.group(1), m.group(2), m.group(3)
        if any(env in content for env in ['bmatrix', 'pmatrix', 'vmatrix', 'cases', 'matrix', 'align', 'CD']):
            return left + content + right
        content = content.replace(' & ', ' \\& ')
        return left + content + right

    body = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', fix_math_block, body)

    # 3. Fix unescaped % inside math mode
    def fix_percent(m):
        left, content, right = m.group(1), m.group(2), m.group(3)
        content = re.sub(r'(?<!\\)%', r'\%', content)
        return left + content + right

    body = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', fix_percent, body)

    return body

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Update renderMath in html so text node processing NEVER destroys matrix \\ row breaks
    print("Updating renderMath text node backslash handling...")
    html = html.replace(
        r"node.nodeValue = node.nodeValue.replace(/\\\\/g, '\\');",
        r"const val = node.nodeValue; node.nodeValue = (val.includes('bmatrix') || val.includes('pmatrix') || val.includes('cases')) ? val : val.replace(/\\\\/g, '\\');"
    )

    print("Cleaning matrix row breaks and unescaped delimiters in lesson bodies...")
    p1 = re.compile(r'(body:\s*`)([\s\S]*?)(`)', re.MULTILINE)
    p2 = re.compile(r'("body":\s*")([\s\S]*?)(")', re.MULTILINE)

    html = p1.sub(lambda m: m.group(1) + fix_body(m.group(2)) + m.group(3), html)
    html = p2.sub(lambda m: m.group(1) + fix_body(m.group(2)) + m.group(3), html)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Matrix and delimiter fixes applied successfully!")

if __name__ == '__main__':
    main()
