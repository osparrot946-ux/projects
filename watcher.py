import os
import asyncio
import httpx
import time
import playwright
from playwright.async_api import async_playwright

# Configuration
INPUT_FILE = "sublist.txt"
OUTPUT_DIR = "screenshots"
HTML_REPORT = "result.html"
CONCURRENCY = 10  # How many sites to check at once

# Results storage
captured_data = []

async def take_screenshot(browser_context, url):
    """Uses Playwright to capture a screenshot of a verified live URL."""
    clean_name = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(":", "")
    filepath = os.path.join(OUTPUT_DIR, f"{clean_name}.png")
    
    page = await browser_context.new_page()
    try:
        # Set a strict timeout for the browser
        await page.goto(url, timeout=30000, wait_until="networkidle")
        # Give it a moment to settle animations
        await asyncio.sleep(2) 
        await page.screenshot(path=filepath)
        return {"url": url, "img": filepath, "status": "Success"}
    except Exception as e:
        print(f"[!] Playwright failed for {url}: {str(e)[:50]}")
        return None
    finally:
        await page.close()

async def check_and_screenshot(semaphore, browser_context, target):
    """Checks if a site is live with HTTPX first, then screenshots."""
    async with semaphore:
        # Try HTTPS, fallback to HTTP
        protocols = ["https://", "http://"] if not target.startswith("http") else [""]
        
        for proto in protocols:
            url = f"{proto}{target}" if proto else target
            try:
                print(f"[*] Probing: {url}")
                async with httpx.AsyncClient(verify=False, timeout=10.0, follow_redirects=True) as client:
                    response = await client.get(url)
                    
                    if response.status_code < 400 or response.status_code == 401:
                        print(f"[+] {url} is LIVE ({response.status_code}). Screenshotting...")
                        res = await take_screenshot(browser_context, url)
                        if res:
                            captured_data.append(res)
                        return # Stop if we successfully got one protocol
            except httpx.RequestError:
                continue # Try next protocol
            except Exception as e:
                print(f"[!] HTTPX Error for {url}: {str(e)[:50]}")

def generate_html():
    """Generates a clean tabular report."""
    rows = ""
    for entry in sorted(captured_data, key=lambda x: x["url"]):
        rel_path = os.path.relpath(entry['img'], start=os.path.dirname(os.path.abspath(HTML_REPORT)))
        rows += f"""
        <tr>
            <td><a href="{entry['url']}" target="_blank" style="color:#1a73e8; font-weight:bold; text-decoration:none;">{entry['url']}</a></td>
            <td><a href="{rel_path}" target="_blank"><img src="{rel_path}" style="max-width:400px; border:1px solid #ddd; border-radius:5px;"></a></td>
        </tr>"""

    html = f"""
    <html>
    <head>
        <title>Subdomain Report</title>
        <style>
            body {{ font-family: sans-serif; background:#f8f9fa; padding:40px; }}
            table {{ width:100%; border-collapse:collapse; background:white; box-shadow:0 2px 10px rgba(0,0,0,0.1); }}
            th, td {{ padding:15px; border-bottom:1px solid #eee; text-align:left; }}
            th {{ background:#1a73e8; color:white; }}
        </style>
    </head>
    <body>
        <h2 style="text-align:center;">🔍 Subdomain Visual Scan</h2>
        <table>
            <tr><th>URL</th><th>Screenshot</th></tr>
            {rows}
        </table>
    </body>
    </html>"""
    with open(HTML_REPORT, "w") as f:
        f.write(html)
    print(f"\n[✓] Report created: {HTML_REPORT}")

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE) as f:
        targets = [line.strip() for line in f if line.strip()]

    print(f"[*] Starting scan of {len(targets)} targets...")

    async with async_playwright() as p:
        # Launch browser once
        browser = await p.chromium.launch(headless=True)
        # Create a context that ignores SSL errors globally
        context = await browser.new_context(ignore_https_errors=True, viewport={'width': 1280, 'height': 720})
        
        semaphore = asyncio.Semaphore(CONCURRENCY)
        tasks = [check_and_screenshot(semaphore, context, t) for t in targets]
        await asyncio.gather(*tasks)
        
        await browser.close()

    generate_html()

if __name__ == "__main__":
    asyncio.run(main())

#here is the requirements that should be installed to run this code:
# pip install playwright httpx 
# also install chromium for playwright using: playwright install chromium

