import re

with open('eee-platform.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Count of 'body':", text.count('"body":'))
print("Count of 'mcqIds':", text.count('"mcqIds":'))

# Let's inspect a snippet of LESSONS definition
start = text.find('const LESSONS = {')
if start == -1:
    start = text.find('LESSONS = {')

print("LESSONS snippet:")
print(text[start:start+500])
