import re
import sys

def fix_lesson_body(body):
    if not body:
        return body

    # 1. Remove nested $ inside $$ ... $$ or \( ... \)
    # Fix $$ ... $ ... $$ nested delimiters
    def clean_nested_dollars(match):
        content = match.group(1)
        # remove single $ inside content
        cleaned = content.replace('$', '')
        return '$$' + cleaned + '$$'

    body = re.sub(r'\$\$([\s\S]*?)\$\$', clean_nested_dollars, body)

    # 2. Fix nested \( inside \( ... \)
    def clean_nested_parens(match):
        content = match.group(1)
        cleaned = content.replace(r'\(', '').replace(r'\)', '')
        return r'\(' + cleaned + r'\)'

    body = re.sub(r'\\\(([\s\S]*?)\\\)', clean_nested_parens, body)

    # 3. Fix unescaped % inside math delimiters $$ ... $$ or \( ... \)
    def escape_percent_in_math(match):
        delim_left, content, delim_right = match.group(1), match.group(2), match.group(3)
        # replace unescaped % with \%
        cleaned = re.sub(r'(?<!\\)%', r'\%', content)
        return delim_left + cleaned + delim_right

    body = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', escape_percent_in_math, body)

    # 4. Fix unescaped & inside text in math mode (e.g. \text{... & ...} or heading in math)
    def escape_amp_in_math(match):
        delim_left, content, delim_right = match.group(1), match.group(2), match.group(3)
        # if content contains \begin{bmatrix} or \begin{cases} or \begin{matrix}, keep column separators &
        if any(env in content for env in ['bmatrix', 'pmatrix', 'vmatrix', 'cases', 'matrix', 'align', 'CD']):
            return match.group(0)
        # otherwise replace unescaped & with \&
        cleaned = re.sub(r'(?<!\\)&', r'\&', content)
        return delim_left + cleaned + delim_right

    body = re.sub(r'(\$\$|\\\(|\\\[)([\s\S]*?)(\$\$|\\\)|\\\])', escape_amp_in_math, body)

    # 5. Fix \right\} without matching \left\{
    body = body.replace(r'\right\}', r'\right\}') # keep standard
    body = re.sub(r'(?<!\\left)\\\{([\s\S]*?)\\right\\\}', r'\\left\\{$1\\right\\}', body)

    # 6. Fix \begin{bmatrix} without \\ row separators
    def fix_bmatrix_rows(match):
        bm = match.group(0)
        if not ('\\\\' in bm or '\\\n' in bm):
            # insert \\ between elements if space separated
            pass
        return bm

    body = re.sub(r'\\begin\{bmatrix\}[\s\S]*?\\end\{bmatrix\}', fix_bmatrix_rows, body)

    return body

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Find LESSONS dictionary and process each lesson's body string
    print("Repairing math parse errors in all lessons...")
    pattern = re.compile(r'("body":\s*")([\s\S]*?)(",\s*"mcqIds")', re.MULTILINE)

    def replace_body(match):
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)
        fixed_body = fix_lesson_body(body)
        return prefix + fixed_body + suffix

    new_html = pattern.sub(replace_body, html)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

    print("KaTeX error repair script finished successfully!")

if __name__ == '__main__':
    main()
