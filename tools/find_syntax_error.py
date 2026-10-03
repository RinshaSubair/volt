import re

with open('eee-platform.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
script_code = scripts[0]

# Let's inspect where repairLatex was modified in script_code
pos = script_code.find('function repairLatex')
print("Snippet around repairLatex:")
print(repr(script_code[pos:pos+600]))
