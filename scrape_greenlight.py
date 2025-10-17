from playwright.sync_api import sync_playwright 
import json

USERNAME = "neong"
PASSWORD = "Green!HKG3"
SEARCH_URL = "https://store.greenlighttoys.com/store/products/search.aspx?search=13699"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Step 1: Go to login page
        page.goto("https://store.greenlighttoys.com/Store/Customer/Login.aspx")

        # Step 2: Fill in login form
        page.fill("input[name='ctl00$MainContent$LoginUser$UserName']", USERNAME)
        page.fill("input[name='ctl00$MainContent$LoginUser$Password']", PASSWORD)

        # Step 3: Submit form
        page.click("input[name='ctl00$MainContent$LoginUser$LoginButton']")

        # Wait until redirected after login
        page.wait_for_load_state("networkidle")

        # Step 4: Go to target page
        page.goto(SEARCH_URL)
        page.wait_for_load_state("networkidle")

        # Step 5: Extract page HTML
        html = page.content()

        # Save result
        with open("output.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("✅ Page saved as output.html")
        browser.close()

if __name__ == "__main__":
    scrape()
