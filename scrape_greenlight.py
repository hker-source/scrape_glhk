from playwright.sync_api import sync_playwright
import time

USERNAME = "neong"
PASSWORD = "Green!HKG3"
SEARCH_URL = "https://store.greenlighttoys.com/store/products/search.aspx?search=13699"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌐 Navigating to login page...")
        page.goto("https://store.greenlighttoys.com/Store/Customer/Login.aspx", wait_until="load")
        time.sleep(3)

        # Debug: take a screenshot to check what the page looks like (saved as artifact)
        page.screenshot(path="page_before_login.png")

        # Try a few possible selectors
        try:
            page.wait_for_selector("input[name='ctl00$MainContent$LoginUser$UserName']", timeout=10000)
            page.fill("input[name='ctl00$MainContent$LoginUser$UserName']", USERNAME)
        except:
            print("⚠️ Default selector not found, trying alternate...")
            # Try a looser selector that just finds any username field
            page.fill("input[type='text']", USERNAME)

        # Fill password
        try:
            page.fill("input[type='password']", PASSWORD)
        except:
            print("⚠️ Password field not found, skipping...")

        # Click login button — try a few alternatives
        try:
            page.click("input[name='ctl00$MainContent$LoginUser$LoginButton']")
        except:
            print("⚠️ Default login button not found, trying alternative...")
            page.locator("input[type='submit'], button").first.click()

        # Wait for post-login redirect
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        print("🔍 Navigating to search page...")
        page.goto(SEARCH_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        html = page.content()
        with open("output.html", "w", encoding="utf-8") as f:
            f.write(html)

        page.screenshot(path="page_after_login.png")

        print("✅ Scraping done. HTML and screenshots saved.")
        browser.close()

if __name__ == "__main__":
    scrape()
