from playwright.sync_api import sync_playwright

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path, headless=True)
    page = browser.new_page()
    
    page.on("console", lambda msg: print("CONSOLE:", msg.type, msg.text))
    page.on("pageerror", lambda err: print("PAGE ERROR:", err))
    
    page.goto('http://localhost:8000/eee-platform.html')
    page.wait_for_timeout(3000)
    
    browser.close()
