import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', headless=True)
    pg = b.new_page()
    pg.goto('http://localhost:8000/eee-platform.html')

    res = pg.evaluate('''() => {
        const kw = ['Input Stage', 'Processing Unit', 'Output Control', 'Sensors / Data', 'Core Architecture', 'Actuators / System', 'R_series', 'jX_L', 'Load Z', 'V_out'];
        const list = [];
        for (const [id, l] of Object.entries(LESSONS)) {
            const body = l.body || '';
            let foundKw = [];
            kw.forEach(k => {
                if (body.includes(k)) foundKw.push(k);
            });
            if (foundKw.length > 0) {
                list.push({id: id, title: l.title, kw: foundKw});
            }
        }
        return list;
    }''')
    
    with open('generic_lessons.txt', 'w', encoding='utf-8') as f:
        for i, item in enumerate(res):
            f.write(str(i+1) + ". " + item['id'] + " | " + item['title'] + "\n")

    print("Wrote generic_lessons.txt successfully! Total:", len(res))
    b.close()
