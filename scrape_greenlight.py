from playwright.sync_api import sync_playwright
import json, os, time

USERNAME = "neong"
PASSWORD = "Green!HKG3"

def scrape(codes):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login once
        page.goto("https://store.greenlighttoys.com/Store/Customer/Login.aspx", wait_until="load")
        page.fill("input[type='text']", USERNAME)
        page.fill("input[type='password']", PASSWORD)
        page.locator("input[type='submit'], button").first.click()
        page.wait_for_load_state("networkidle")
        time.sleep(2)

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
