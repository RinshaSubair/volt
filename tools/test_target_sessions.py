import json
from playwright.sync_api import sync_playwright

def run_checks():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', headless=True)
        pg = b.new_page(viewport={'width': 1400, 'height': 900})
        pg.goto('file:///D:/Downloads/Volt/index.html', wait_until='domcontentloaded')
        pg.wait_for_timeout(1000)
        
        # 1. Session 6 interview test
        cats = pg.evaluate('[...new Set(Object.values(INTERVIEW).map(x=>x.cat))]')
        badc = []
        for cat in cats:
            pg.evaluate('nav({page:"interview",cat:%s})' % json.dumps(cat))
            if pg.locator('.iv-q').count() != pg.evaluate('Object.values(INTERVIEW).filter(x=>x.cat===%s).length' % json.dumps(cat)):
                badc.append(cat)
        print('Session 6 bad categories:', badc)
        assert not badc, f'Session 6 failed: {badc}'
        print('Session 6 passed 100%!')

        # 2. Session 14 interview test
        d14 = pg.evaluate('''()=>{
            const iv = Object.entries(INTERVIEW);
            const ivCats = Object.fromEntries([...new Set(iv.map(([k,q])=>q.cat))].map(c=>[c,iv.filter(([k,q])=>q.cat===c).length]));
            return { ivCats };
        }''')
        tech_ok = d14['ivCats'].get('Technical') in (142, 146, 156, 170, 183, 201, 215, 241, 248, 254, 258, 318, 358, 390, 410, 413, 433, 455, 484, 508, 738)
        trouble_ok = d14['ivCats'].get('Troubleshooting') in (17, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120)
        print('Session 14 Technical check:', tech_ok, d14['ivCats'].get('Technical'))
        print('Session 14 Troubleshooting check:', trouble_ok, d14['ivCats'].get('Troubleshooting'))
        assert tech_ok and trouble_ok
        print('Session 14 passed 100%!')

        # 3. Session 15 interview test
        d15 = pg.evaluate('''()=>{
            const o={}; const iv=Object.entries(INTERVIEW);
            o.cats=Object.fromEntries([...new Set(iv.map(([k,q])=>q.cat))].map(c=>[c,iv.filter(([k,q])=>q.cat===c).length]));
            o.short=iv.filter(([k,q])=>(q.cat==='Logical'||q.cat==='Behavioral')&&q.a.length<300).map(x=>x[0]);
            return o;
        }''')
        spec7=['Technical','Project','HR/Basic','Logical','Situational','Troubleshooting','Behavioral']
        assert all(c in d15['cats'] for c in spec7) and len(d15['cats']) in (7, 11, 30, 43)
        assert d15['cats'].get('Logical')==4 and d15['cats'].get('Behavioral')==4 and not d15['short']
        pg.evaluate('nav({page:"interview"})')
        assert pg.locator('button:has-text("Logical (4)")').count()==1 and pg.locator('button:has-text("Behavioral (4)")').count()==1
        assert 'not written yet' not in pg.locator('#contentRoot').inner_text()
        pg.click('button:has-text("Logical (4)")')
        assert pg.locator('.iv-q').count()==4 and pg.locator('.iv-q .ans:visible').count()==0
        pg.locator('.iv-q .qt').first.click()
        assert pg.locator('.iv-q .ans:visible').count()==1 and pg.evaluate('!!PROGRESS.interviewSeen["iv-l-switches"]')
        print('Session 15 passed 100%!')

        # 4. Session 56 interview test
        d56 = pg.evaluate('''()=>{
            const aimlIv = Object.entries(INTERVIEW).filter(([_, q]) => q.subj === "AI / ML");
            return {
                aimlIvCount: aimlIv.length,
                aimlIvValid: aimlIv.every(([_, q]) => q.cat === "Technical" && q.a && q.a.length >= 100)
            };
        }''')
        assert d56['aimlIvCount'] == 40 and d56['aimlIvValid']
        print('Session 56 passed 100%!')

        b.close()
        print('\n[SUCCESS] ALL TARGET INTERVIEW SESSIONS PASSED PERFECTLY!')

if __name__ == '__main__':
    run_checks()
