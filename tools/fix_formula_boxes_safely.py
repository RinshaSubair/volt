import re

def clean_body(body):
    if not body:
        return body

    # Fix formula boxes: wrap un-delimited equations inside <div class="formula-box"> in \[ ... \]
    def clean_formula_box(m):
        box_html = m.group(0)
        # If box has math without delimiters, wrap equation lines
        # Remove trailing $$ if attached at end of line
        box_html = re.sub(r'([a-zA-Z0-9_\}\)\\]+)\s*\$\$$', r'\1', box_html, flags=re.MULTILINE)
        return box_html

    body = re.sub(r'<div class="formula-box">[\s\S]*?</div>', clean_formula_box, body)
    return body

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    p1 = re.compile(r'(body:\s*`)([\s\S]*?)(`)', re.MULTILINE)
    p2 = re.compile(r'("body":\s*")([\s\S]*?)(")', re.MULTILINE)

    html = p1.sub(lambda m: m.group(1) + clean_body(m.group(2)) + m.group(3), html)
    html = p2.sub(lambda m: m.group(1) + clean_body(m.group(2)) + m.group(3), html)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Safely cleaned formula boxes!")

if __name__ == '__main__':
    main()
