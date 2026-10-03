from playwright.sync_api import sync_playwright
import time

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path, headless=True)
    page = browser.new_page()
    page.goto('http://localhost:8000/eee-platform.html', wait_until='domcontentloaded')
    
    # Wait for SYLLABUS
    page.wait_for_function('typeof SYLLABUS !== "undefined"', timeout=10000)
    
    syllabus_len = page.evaluate('() => SYLLABUS.length')
    print('SYLLABUS length:', syllabus_len)

    lessons_len = page.evaluate('() => Object.keys(LESSONS).length')
    print('LESSONS count:', lessons_len)

    browser.close()
