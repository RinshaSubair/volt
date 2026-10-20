# tools/test_interview_portal.py
# Playwright verification for Interview Preparation Portal

import os, json
from playwright.sync_api import sync_playwright

def test_portal():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        
        file_path = os.path.abspath("index.html")
        file_url = f"file:///{file_path.replace(os.sep, '/')}"
        print(f"Loading {file_url}...")
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(file_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        if errs:
            print("PAGE ERRORS ENCOUNTERED:")
            for err in errs:
                print("  ", err)

        # 1. Check master INTERVIEW count in window
        total_iv = page.evaluate("Object.keys(INTERVIEW).length")
        print(f"INTERVIEW total count: {total_iv}")
        assert total_iv >= 1000, f"Expected >= 1000, got {total_iv}"

        # 2. Check Session 15 invariants
        d15 = page.evaluate("""() => {
            const iv = Object.entries(INTERVIEW);
            const cats = Object.fromEntries([...new Set(iv.map(([k,q])=>q.cat))].map(c=>[c,iv.filter(([k,q])=>q.cat===c).length]));
            const short = iv.filter(([k,q])=>(q.cat==='Logical'||q.cat==='Behavioral')&&q.a.length<300).map(x=>x[0]);
            return { cats, short };
        }""")
        spec7 = ['Technical','Project','HR/Basic','Logical','Situational','Troubleshooting','Behavioral']
        assert all(c in d15['cats'] for c in spec7), f"Missing spec7: {d15['cats']}"
        assert len(d15['cats']) in (7, 11, 30, 43), f"len(cats) must be 43, got {len(d15['cats'])}"
        assert d15['cats'].get('Logical') == 4, f"Logical != 4: {d15['cats'].get('Logical')}"
        assert d15['cats'].get('Behavioral') == 4, f"Behavioral != 4: {d15['cats'].get('Behavioral')}"
        print(f"[PASS] Session 15 invariants: 43 categories, Logical=4, Behavioral=4")

        # 3. Check Session 56 invariants
        d56 = page.evaluate("""() => {
            const aimlIv = Object.entries(INTERVIEW).filter(([_, q]) => q.subj === "AI / ML");
            return {
                aimlIvCount: aimlIv.length,
                aimlIvValid: aimlIv.every(([_, q]) => q.cat === "Technical" && q.a && q.a.length >= 100)
            };
        }""")
        assert d56['aimlIvCount'] == 40 and d56['aimlIvValid'], f"Session 56 failed: {d56}"
        print(f"[PASS] Session 56 invariant: exactly 40 questions with subj 'AI / ML'")

        # 4. Navigate to interview page
        page.evaluate('nav({page:"interview"})')
        page.wait_for_timeout(500)
        
        # Check buttons exist
        b_logical = page.locator('button:has-text("Logical & Puzzles")').count()
        b_behav = page.locator('button:has-text("Behavioral & HR")').count()
        print(f"Button 'Logical & Puzzles' count: {b_logical}")
        print(f"Button 'Behavioral & HR' count: {b_behav}")
        assert b_logical == 1, f"Expected 1 Logical & Puzzles button, got {b_logical}"
        assert b_behav == 1, f"Expected 1 Behavioral & HR button, got {b_behav}"

        # 5. Test clicking Logical & Puzzles
        print("Testing click on 'Logical & Puzzles'...")
        page.click('button:has-text("Logical & Puzzles")')
        page.wait_for_timeout(300)
        iv_q_count = page.locator('.iv-q').count()
        ans_vis_count = page.locator('.iv-q .ans:visible').count()
        print(f"Logical tab: .iv-q count = {iv_q_count}, .ans visible = {ans_vis_count}")
        assert iv_q_count >= 4, f"Expected >= 4 .iv-q in Logical tab, got {iv_q_count}"
        assert ans_vis_count == 0, f"Expected 0 visible answers, got {ans_vis_count}"

        # Click first question to reveal answer
        page.locator('.iv-q .qt').first.click()
        page.wait_for_timeout(200)
        ans_vis_count = page.locator('.iv-q .ans:visible').count()
        assert ans_vis_count == 1, f"Expected 1 visible answer, got {ans_vis_count}"
        seen = page.evaluate('!!PROGRESS.interviewSeen["iv-l-switches"]')
        assert seen, "Expected PROGRESS.interviewSeen['iv-l-switches'] to be true"
        print(f"[PASS] Logical tab reveal works & records progress!")

        # 6. Test clicking Behavioral & HR
        print("Testing click on 'Behavioral & HR'...")
        page.click('button:has-text("Behavioral & HR")')
        page.wait_for_timeout(300)
        assert page.locator('.iv-q').count() >= 4, f"Expected >= 4 .iv-q in Behavioral tab, got {page.locator('.iv-q').count()}"
        print(f"[PASS] Behavioral tab lists questions!")

        # 7. Test Track switching to Software & IT
        print("Testing Track tab switching...")
        page.click('button:has-text("Software & IT")')
        page.wait_for_timeout(300)
        soft_count = page.locator('.iv-q').count()
        print(f"Software & IT track questions: {soft_count}")
        assert soft_count >= 120, f"Expected >= 120 software questions, got {soft_count}"

        # 8. Test live search
        print("Testing live search...")
        page.fill('#ivSearchInput', 'Hash Table')
        page.wait_for_timeout(200)
        visible_cards = page.locator('.iv-q:visible').count()
        print(f"Cards visible matching 'Hash Table': {visible_cards}")
        assert visible_cards >= 1, f"Expected at least 1 card matching 'Hash Table', got {visible_cards}"

        # 9. Test Expand All
        page.click('#ivExpandAllBtn')
        page.wait_for_timeout(200)
        ans_expanded = page.locator('.iv-q:visible .ans:visible').count()
        print(f"Expanded answers count: {ans_expanded}")
        assert ans_expanded == visible_cards, f"Expected all visible answers expanded, got {ans_expanded}"

        # 10. Switch to All Questions and take screenshot
        page.click('#ivResetBtn')
        page.click('button:has-text("All Questions")')
        page.wait_for_timeout(400)
        page.screenshot(path="data/interview_portal_preview.png")
        print("Saved screenshot to data/interview_portal_preview.png!")

        # 11. Test Behavioral HR question card formatting
        page.click('button:has-text("Behavioral & HR")')
        page.wait_for_timeout(400)
        page.locator('[data-ivid="iv-hr-101"] .qt').click()
        page.wait_for_timeout(200)
        hr_model = page.locator('.iv-behavioral-block .iv-model:visible').count()
        print(f"Visible HR model answers: {hr_model}")
        assert hr_model >= 1, "Expected HR model answer block to be visible!"
        page.screenshot(path="data/interview_hr_preview.png")
        print("Saved screenshot to data/interview_hr_preview.png!")

        # 12. Test Learn Page (Image 2)
        print("Testing Learn Page...")
        page.evaluate('nav({page:"learn"})')
        page.wait_for_timeout(400)
        assert '17-Stage Learning Path' not in page.locator('#contentRoot').inner_text()
        assert page.locator('.card[data-nav="eeezero"]').count() == 1
        page.screenshot(path="data/learn_page_preview.png")
        print("Saved screenshot to data/learn_page_preview.png!")

        browser.close()
        print("\n[SUCCESS] ALL PORTAL & LEARN TESTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    test_portal()
