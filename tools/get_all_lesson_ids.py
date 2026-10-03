import sys, json, re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8000/eee-platform.html")
    page.wait_for_function("typeof LESSONS !== 'undefined'")
    page.wait_for_timeout(500)

    lessons_dict = page.evaluate("""() => {
        const res = {};
        for(let id in LESSONS) {
            const l = LESSONS[id];
            res[id] = {
                title: l.title || '',
                body: l.body || ''
            };
        }
        return res;
    }""")
    
    print(f"Total Active Lessons: {len(lessons_dict)}")
    
    # Save lesson dictionary to json for fast offline inspection
    with open('all_623_lessons.json', 'w', encoding='utf-8') as f:
        json.dump(lessons_dict, f, indent=2, ensure_ascii=False)
        
    print("Saved all 623 lessons to all_623_lessons.json")
    browser.close()
