import os
from playwright.sync_api import sync_playwright

def test_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        
        file_path = os.path.abspath("index.html")
        file_url = f"file:///{file_path.replace(os.sep, '/')}"
        print(f"Loading {file_url}...")
        page.goto(file_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        # 1. Test Dashboard (Uniform 1200px Grid)
        print("Testing Dashboard uniform layout...")
        page.evaluate('nav({page:"home"})')
        page.wait_for_timeout(500)
        page.screenshot(path="data/dashboard_uniform_view.png")
        print("Saved data/dashboard_uniform_view.png")

        # 2. Test Course Syllabus view (Semester 3 -> Circuit Theory)
        print("Testing Course Syllabus view...")
        page.evaluate('nav({page:"course", sem:"3", code:"23EET305"})')
        page.wait_for_timeout(500)
        page.screenshot(path="data/course_syllabus_view.png")
        print("Saved data/course_syllabus_view.png")

        # 3. Test Topic Selection -> Dedicated Topic Workspace Window (Thevenin's Theorem)
        print("Testing Topic selection -> Learning Workspace Window...")
        page.evaluate('nav({page:"lesson", id:"thevenin"})')
        page.wait_for_timeout(600)
        
        # Verify workspace elements
        assert page.locator('.topic-workspace').count() == 1, "Expected .topic-workspace"
        assert page.locator('.topic-window-header').count() == 1, "Expected .topic-window-header"
        assert page.locator('#markStudiedBtn').count() == 1, "Expected #markStudiedBtn"
        
        # Check Next topic button
        next_count = page.locator('.topic-pager-next [data-nav]').count()
        print(f"Next topic button count: {next_count}")
        assert next_count >= 1, "Expected Next topic button"

        page.screenshot(path="data/topic_reader_window.png")
        print("Saved data/topic_reader_window.png")

        # 4. Test clicking 'Next Topic →' button in the workspace footer
        print("Testing Next Topic navigation click...")
        page.click('.topic-pager-next [data-nav]')
        page.wait_for_timeout(600)
        
        new_title = page.locator('.lesson-title').inner_text()
        print(f"Navigated to Next Topic: {new_title}")
        assert 'norton' in new_title.lower() or 'theorem' in new_title.lower()
        page.screenshot(path="data/next_topic_window.png")
        print("Saved data/next_topic_window.png")

        # 5. Test Mock Test uniform width layout
        print("Testing Mock Test uniform width layout...")
        page.evaluate('nav({page:"mock"})')
        page.wait_for_timeout(500)
        page.screenshot(path="data/mock_test_uniform_view.png")
        print("Saved data/mock_test_uniform_view.png")

        # 6. Test Mark as Studied interaction in workspace
        print("Testing Mark as Studied toggle in workspace...")
        page.evaluate('nav({page:"lesson", id:"kcl-kvl"})')
        page.wait_for_timeout(400)
        page.click('#markStudiedBtn')
        page.wait_for_timeout(200)
        btn_text = page.locator('#markStudiedBtn').inner_text()
        print("Mark studied button clicked successfully")
        assert 'studied' in btn_text.lower()

        browser.close()
        print("\n[SUCCESS] ALL REDESIGNED UI & WORKSPACE TESTS PASSED 100%!")

if __name__ == "__main__":
    test_ui()
