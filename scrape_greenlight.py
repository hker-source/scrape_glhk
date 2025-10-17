from playwright.sync_api import sync_playwright
import time
import json, os, time

USERNAME = "neong"
PASSWORD = "Green!HKG3"
SEARCH_URL = "https://store.greenlighttoys.com/store/products/search.aspx?search=13699"

def scrape():
def scrape(codes):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌐 Navigating to login page...")
        # Login once
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
        page.fill("input[type='text']", USERNAME)
        page.fill("input[type='password']", PASSWORD)
        page.locator("input[type='submit'], button").first.click()
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
        # Loop over product codes
        for code in codes:
            url = f"https://store.greenlighttoys.com/store/products/search.aspx?search={code}"
            print(f"🔍 Scraping {url}")
            page.goto(url)
            page.wait_for_load_state("networkidle")
            html = page.content()
            with open(f"output_{code}.html", "w", encoding="utf-8") as f:
                f.write(html)

        print("✅ All pages scraped.")
        browser.close()

if __name__ == "__main__":
    scrape()
    # Read product codes from environment variable or JSON file
    if os.path.exists("product_codes.json"):
        with open("product_codes.json", "r") as f:
            codes = json.load(f)
    else:
        env_codes = os.getenv("PRODUCT_CODES", "")
        codes = json.loads(env_codes) if env_codes else []

    if not codes:
        print("⚠️ No product codes found, exiting.")
    else:
        scrape(codes)
