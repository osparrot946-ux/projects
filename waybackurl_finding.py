import requests
import sys

def get_wayback_urls_robust(domain, include_subs=False):
    """
    Fetches URLs using a streaming text approach to handle massive datasets
    without crashing on JSON parsing errors.
    """
    wildcard = "*." if include_subs else ""
    
    # We remove 'output=json' and use 'fl=original'
    # This returns a simple text list of URLs, one per line.
    api_url = f"http://web.archive.org/cdx/search/cdx?url={wildcard}{domain}/*&fl=original&collapse=urlkey"
    
    print(f"[*] Fetching URLs for: {domain}...")
    
    try:
        # Use stream=True to handle large responses gracefully
        with requests.get(api_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            
            filename = f"{domain}_wayback.txt"
            count = 0
            
            with open(filename, "w", encoding="utf-8") as f:
                # Iterate over lines directly from the server response
                for line in r.iter_lines():
                    if line:
                        url = line.decode('utf-8')
                        f.write(url + "\n")
                        count += 1
            
            return filename, count

    except Exception as e:
        print(f"[!] Error: {e}")
        return None, 0

if __name__ == "__main__":
    target = input("Enter domain: ").strip()
    subs = input("Include subdomains? (y/n): ").strip().lower() == 'y'
    
    file, total = get_wayback_urls_robust(target, subs)
    
    if file:
        print(f"[+] Success! {total} unique URLs saved to {file}")
    else:
        print("[-] Process failed.")
