import re

def clean_matrix_delimiters(body):
    if not body:
        return body

    # Fix \end{bmatrix} \] = \[ \begin{bmatrix} -> \end{bmatrix} = \begin{bmatrix}
    body = body.replace(r'\] = \[', ' = ')
    body = body.replace(r'\] = \[', ' = ')
    body = body.replace(r'\]=\[', ' = ')

    # Ensure all \begin{bmatrix} ... \end{bmatrix} are wrapped in a single display delimiter \[ ... \]
    def wrap_matrix_block(m):
        content = m.group(0)
        # If already inside \[ ... \], leave as is
        return content

    # Clean double escaped \\\\ in matrix rows: \end{bmatrix}
    body = body.replace(r'\\end{bmatrix}', r'\end{bmatrix}')
    body = body.replace(r'\\begin{bmatrix}', r'\begin{bmatrix}')
    body = body.replace(r'\\end{cases}', r'\end{cases}')
    body = body.replace(r'\\begin{cases}', r'\begin{cases}')

    return body

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print("Cleaning matrix equation delimiters in lesson source data...")
    p1 = re.compile(r'(body:\s*`)([\s\S]*?)(`)', re.MULTILINE)
    p2 = re.compile(r'("body":\s*")([\s\S]*?)(")', re.MULTILINE)

    html = p1.sub(lambda m: m.group(1) + clean_matrix_delimiters(m.group(2)) + m.group(3), html)
    html = p2.sub(lambda m: m.group(1) + clean_matrix_delimiters(m.group(2)) + m.group(3), html)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Matrix equation delimiters fixed successfully!")

if __name__ == '__main__':
    main()
