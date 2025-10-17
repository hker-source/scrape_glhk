name: Run Playwright Scraper and Post to n8n

on:
  workflow_dispatch:
    inputs:
      product_codes:
        description: 'JSON array of product codes'
        required: true
        default: '["13699"]'

jobs:
  scrape-and-post:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          python -m playwright install --with-deps

      - name: Run scraper
        # Run the script which must write into ./scraped_pages/ (create dir if not exists)
        env:
          PRODUCT_CODES: ${{ github.event.inputs.product_codes }}
          GL_USERNAME: ${{ secrets.GL_USERNAME }}
          GL_PASSWORD: ${{ secrets.GL_PASSWORD }}
        run: |
          # ensure output folder exists
          mkdir -p scraped_pages
          # Run your script which should write output files to scraped_pages/
          python scrape_greenlight.py
          # debug: list files
          echo "== files in workspace =="
          pwd
          ls -la
          echo "== files in scraped_pages =="
          ls -la scraped_pages || true

      - name: Zip results
        run: |
          # zip will fail with exit code 12 if path not present; guard it
          if [ -d "scraped_pages" ] && [ "$(ls -A scraped_pages)" ]; then
            zip -r scraped_output.zip scraped_pages
            echo "Zipped scraped_output.zip"
          else
            echo "No scraped output found — failing job"
            ls -la
            exit 1
          fi

      - name: Send result to n8n
        env:
          N8N_WEBHOOK_URL: ${{ secrets.N8N_WEBHOOK_URL }}
          PRODUCT_CODES: ${{ github.event.inputs.product_codes }}
        run: |
          # POST the zip and metadata to n8n
          curl -s -o /tmp/curl_resp.txt -w "%{http_code}" -X POST \
            -H "Accept: */*" \
            -F "file=@scraped_output.zip" \
            -F "product_codes=${PRODUCT_CODES}" \
            "${N8N_WEBHOOK_URL}" > /tmp/statuscode
          cat /tmp/statuscode
          echo
          echo "curl response:"
          cat /tmp/curl_resp.txt || true
