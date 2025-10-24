from playwright.sync_api import sync_playwright, Error as PlaywrightError
import json, os, time, sys

USERNAME = "neong"
PASSWORD = "Green!HKG3"

def scrape(codes):
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except PlaywrightError as e:
            print("ERROR: Playwright failed to launch the browser.")
            print(str(e))
            print()
            print("Hint: Playwright browser binaries are missing. Run:")
            print("  python -m playwright install --with-deps chromium")
            print("In CI, add a workflow step that runs that command before running this script.")
            raise

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
            # Extract visible text rather than raw HTML to make downstream parsing simpler.
            try:
                body_text = page.locator("body").inner_text()
            except Exception:
                # Fallback: full page content if body extraction fails
                body_text = page.content()
            # Prepend a small header with metadata to help downstream parsing if needed
            header = f"URL: {url}\nPRODUCT_CODE: {code}\nSCRAPED_AT: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n\n"
            out_path = f"output_{code}.txt"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(header)
                f.write(body_text)

        print("✅ All pages scraped.")
        browser.close()

if __name__ == "__main__":
    # Read product codes from environment variable or JSON file
    if os.path.exists("product_codes.json"):
        with open("product_codes.json", "r") as f:
            codes = json.load(f)
    else:
        env_codes = os.getenv("PRODUCT_CODES", "")
        try:
            codes = json.loads(env_codes) if env_codes else []
        except json.JSONDecodeError:
            # Better fallback: tolerate bracketed lists with trailing commas like "[30576,30577,]"
            s = env_codes.strip()
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1]
            # split on commas, strip whitespace and surrounding quotes
            parts = [p.strip().strip('"').strip("'") for p in s.split(",")]
            # keep non-empty parts
            codes = [p for p in parts if p != ""]

    # Normalize and filter out falsy entries (None, empty string, etc.)
    normalized = []
    for item in codes:
        if item is None:
            continue
        # If it's already a number, keep as int
        if isinstance(item, (int, float)):
            try:
                normalized.append(int(item))
            except Exception:
                normalized.append(item)
            continue
        # Otherwise treat as string: strip and try to convert to int
        s = str(item).strip()
        if not s:
            continue
        # Remove stray brackets that may survive parsing (e.g., "]" or "[")
        if s in ("[", "]"):
            continue
        try:
            normalized.append(int(s))
        except ValueError:
            normalized.append(s)

    # Final filter to remove falsy values (this handles empty strings, None, 0 if you don't want zeros remove that case)
    codes = list(filter(None, normalized))

    if not codes:
        print("⚠️ No product codes found, exiting.")
        sys.exit(0)
    else:
        scrape(codes)
