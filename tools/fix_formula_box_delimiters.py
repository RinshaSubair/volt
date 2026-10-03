import re

def fix_formula_boxes(html):
    # Match <div class="formula-box"> ... </div> blocks
    pattern = re.compile(r'(<div class="formula-box">)([\s\S]*?)(</div>)', re.MULTILINE)

    def clean_box(m):
        prefix = m.group(1)
        content = m.group(2)
        suffix = m.group(3)

        # Check if content has <h4> or <h3> or <ul>
        # We only want to wrap raw math equations in \[ ... \] or $$\begin{aligned}...\end{aligned}$$
        lines = content.split('\n')
        new_lines = []
        in_math = False
        math_lines = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                new_lines.append(line)
                continue

            # If it's HTML tag like <h4>, <ul>, <li>, <strong>, keep as is
            if trimmed.startswith('<h') or trimmed.startswith('<ul') or trimmed.startswith('<li') or trimmed.startswith('<p') or trimmed.startswith('<h4>') or trimmed.startswith('<ul>') or trimmed.startswith('<li>'):
                if math_lines:
                    # Flush accumulated math lines wrapped in display delimiters
                    m_text = '\n'.join(math_lines).replace('$$', '').replace('\\[', '').replace('\\]', '').strip()
                    if '\\\\' in m_text:
                        new_lines.append(r'\[ \begin{aligned} ' + m_text + r' \end{aligned} \]')
                    else:
                        new_lines.append(r'\[ ' + m_text + r' \]')
                    math_lines = []
                new_lines.append(line)
            else:
                # It's an equation line inside formula-box
                # Strip raw $$ at end if present
                clean_line = trimmed.replace('$$', '').replace('\\[', '').replace('\\]', '').strip()
                if clean_line:
                    math_lines.append(clean_line)

        if math_lines:
            m_text = '\n'.join(math_lines).replace('$$', '').replace('\\[', '').replace('\\]', '').strip()
            if '\\\\' in m_text:
                new_lines.append(r'\[ \begin{aligned} ' + m_text + r' \end{aligned} \]')
            else:
                new_lines.append(r'\[ ' + m_text + r' \]')

        return prefix + '\n' + '\n'.join(new_lines) + '\n' + suffix

    return pattern.sub(clean_box, html)

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print("Wrapping raw math in formula-box elements in display delimiters...")
    new_html = fix_formula_boxes(html)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

    print("Formula box delimiters fixed successfully!")

if __name__ == '__main__':
    main()
