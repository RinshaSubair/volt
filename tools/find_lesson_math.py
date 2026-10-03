import sys
sys.stdout.reconfigure(encoding='utf-8')
import re

with open('eee-platform.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = '"z-breadboard-prototyping":'
idx = text.find(target)
if idx != -1:
    snippet = text[idx:idx+3500]
    print("Found z-breadboard-prototyping! Snippet:")
    print(snippet)
else:
    print("Not found with exact target:", target)
