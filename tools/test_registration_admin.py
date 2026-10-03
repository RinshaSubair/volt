import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def run_tests():
    file_path = os.path.abspath("eee-platform.html")
    file_url = "file:///" + file_path.replace("\\", "/")
    admin_path = os.path.abspath("admin.html")
    admin_url = "file:///" + admin_path.replace("\\", "/")

    print(f"Testing Platform: {file_url}")
    print(f"Testing Admin: {admin_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
        
        # Test 1: eee-platform.html has registration elements
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.goto(file_url, wait_until='domcontentloaded')
        
        # Check loginWall is present
        wall = page.query_selector("#loginWall")
        assert wall is not None, "loginWall must be in DOM"
        
        # Check tabs exist
        sign_in_tab = page.query_selector("#authTabSignInBtn")
        reg_tab = page.query_selector("#authTabRegisterBtn")
        assert sign_in_tab is not None, "Sign In tab must exist"
        assert reg_tab is not None, "Register tab must exist"

        # Check fields exist
        assert page.query_selector("#loginEmailInput") is not None, "Login Email input must exist"
        assert page.query_selector("#loginPasswordInput") is not None, "Login Password input must exist"
        assert page.query_selector("#googleSignInBtn") is not None, "Google Sign-In button must exist"
        
        assert page.query_selector("#regNameInput") is not None, "Name input must exist"
        assert page.query_selector("#regEmailInput") is not None, "Email input must exist"
        assert page.query_selector("#regPhoneInput") is not None, "Phone input must exist"
        assert page.query_selector("#sendOtpBtn") is not None, "Send OTP button must exist"
        assert page.query_selector("#regOtpInput") is not None, "OTP input must exist"
        assert page.query_selector("#verifyOtpBtn") is not None, "Verify OTP button must exist"
        assert page.query_selector("#regCollegeInput") is not None, "College input must exist"
        assert page.query_selector("#regSemesterSelect") is not None, "Semester select must exist"
        assert page.query_selector("#regDeptSelect") is not None, "Department select must exist"
        assert page.query_selector("#regReferralSelect") is not None, "Referral select must exist"
        assert page.query_selector("#googleRegisterBtn") is not None, "Google Register button must exist"
        assert page.query_selector("#authPendingPanel") is not None, "Pending screen must exist"
        assert page.query_selector("#authRejectedPanel") is not None, "Rejected screen must exist"
        assert page.query_selector("#adminPortalBtn") is not None, "Admin portal link button must exist"

        print("✓ All Registration, Login, and Status DOM elements verified in eee-platform.html")

        # In Playwright test mode, loginWall is hidden by default for test suite bypass.
        # Explicitly display loginWall to test student registration interactions:
        page.evaluate("() => { document.getElementById('loginWall').style.display = 'flex'; }")

        # Test tab switching
        page.click("#authTabRegisterBtn")
        reg_display = page.evaluate("() => document.getElementById('authRegisterPanel').style.display")
        assert reg_display != "none", "Register panel should be visible after tab click"
        print("✓ Tab switching to Register verified")

        # Test simulated OTP trigger
        page.fill("#regPhoneInput", "9876543210")
        page.click("#sendOtpBtn")
        otp_box_display = page.evaluate("() => document.getElementById('otpVerifyBox').style.display")
        assert otp_box_display == "block", "OTP box should display after Send OTP click"
        print("✓ OTP generation and box display verified")

        page.click("#verifyOtpBtn")
        badge_display = page.evaluate("() => document.getElementById('otpStatusBadge').style.display")
        assert badge_display == "inline-flex", "OTP verified badge should display after OTP verification"
        print("✓ OTP verification badge verified")

        # Test 2: admin.html has React app structure
        admin_page = browser.new_page(viewport={'width': 1280, 'height': 800})
        admin_page.goto(admin_url, wait_until='domcontentloaded')
        admin_root = admin_page.query_selector("#root")
        assert admin_root is not None, "React #root element must exist in admin.html"
        print("✓ React #root verified in admin.html")

        # Check script execution in admin.html
        admin_title = admin_page.title()
        assert "Admin" in admin_title, "Admin page title must mention Admin"
        print(f"✓ Admin page title verified: '{admin_title}'")

        browser.close()
        print("\n🎉 ALL REGISTRATION & ADMIN UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
