from playwright.sync_api import sync_playwright
import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Get Script #8
scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', text, re.DOTALL)
sc8 = scripts[7] # 0-indexed 7
lines = sc8.split('\n')
print(f"Total lines in Script #8: {len(lines)}")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', headless=True)
    page = b.new_page()
    page.goto('about:blank')

    # Find the line of the error using CDP session or binary test
    # Let's use CDP console/runtime domain to get exact line and column!
    cdp = page.context.new_cdp_session(page)
    cdp.send("Runtime.enable")
    
    res = cdp.send("Runtime.compileScript", {
        "expression": sc8,
        "sourceURL": "script8.js",
        "persistScript": False
    })
    print("CompileScript result:", res)

    b.close()
