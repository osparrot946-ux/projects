import asyncio
import aiodns
import subprocess
import os
from typing import List, Set
from threading import Lock

# Performance Settings
MAX_CONCURRENT_QUERIES = 2000  # Adjust based on your network/CPU
DNS_RESOLVERS = ["1.1.1.1", "8.8.8.8", "1.0.0.1", "8.8.4.4"]
TIMEOUT = 2.0

class SubdomainScanner:
    def __init__(self, domain: str, wordlist_path: str, output_path: str):
        self.domain = domain
        self.wordlist_path = wordlist_path
        self.output_path = output_path
        self.found_subdomains: Set[str] = set()
        self.lock = asyncio.Lock()
        self.resolver = aiodns.DNSResolver(nameservers=DNS_RESOLVERS, timeout=TIMEOUT)
        self.wildcard_ips: Set[str] = set()

    async def detect_wildcard(self):
        """
        Detects if the domain uses wildcard DNS (points non-existent subs to an IP).
        This significantly increases accuracy by preventing false positives.
        """
        print(f"[*] Checking for wildcard DNS on {self.domain}...")
        random_sub = f"detect-wildcard-{os.urandom(4).hex()}.{self.domain}"
        try:
            result = await self.resolver.query(random_sub, 'A')
            self.wildcard_ips = {ip.host for ip in result}
            print(f"[!] Wildcard detected! Filtering IPs: {self.wildcard_ips}")
        except:
            print("[+] No wildcard DNS detected. Results will be highly accurate.")

    async def resolve_sub(self, semaphore: asyncio.Semaphore, subdomain: str):
        """Attempts to resolve a single subdomain asynchronously."""
        async with semaphore:
            try:
                # We query 'A' records to verify existence
                result = await self.resolver.query(subdomain, 'A')
                
                # Accuracy check: Ensure resolved IPs aren't the wildcard landing page
                resolved_ips = {ip.host for ip in result}
                if not resolved_ips.intersection(self.wildcard_ips):
                    await self.save_result(subdomain)
            except (aiodns.error.DNSError, Exception):
                pass

    async def save_result(self, subdomain: str):
        """Thread-safe/Async-safe saving to file and memory."""
        async with self.lock:
            if subdomain not in self.found_subdomains:
                self.found_subdomains.add(subdomain)
                with open(self.output_path, "a") as f:
                    f.write(subdomain + "\n")

    def run_subfinder(self):
        """Runs Subfinder as a background process to gather initial seeds."""
        print("[*] Launching Subfinder for passive discovery...")
        try:
            # -silent removes banners, -d specifies domain
            result = subprocess.run(
                ["subfinder", "-silent", "-d", self.domain],
                capture_output=True,
                text=True
            )
            subs = [s.strip() for s in result.stdout.splitlines() if s.strip()]
            print(f"[+] Subfinder found {len(subs)} passive subdomains.")
            return subs
        except FileNotFoundError:
            print("[-] Subfinder not found in PATH. Skipping passive scan.")
            return []

    async def brute_force(self):
        """Orchestrates the asynchronous brute-force attack."""
        if not os.path.exists(self.wordlist_path):
            print(f"[-] Wordlist not found at {self.wordlist_path}")
            return

        print(f"[*] Loading wordlist and starting active brute-force...")
        
        # Load wordlist into memory
        with open(self.wordlist_path, "r") as f:
            words = [line.strip() for line in f if line.strip()]

        # Passive results first
        passive_subs = self.run_subfinder()
        for sub in passive_subs:
            await self.save_result(sub)

        await self.detect_wildcard()

        # Create a semaphore to limit concurrency (prevent socket exhaustion)
        sem = asyncio.Semaphore(MAX_CONCURRENT_QUERIES)
        tasks = []

        print(f"[*] Brute-forcing {len(words)} entries using {MAX_CONCURRENT_QUERIES} concurrent slots...")
        
        for word in words:
            full_domain = f"{word}.{self.domain}"
            tasks.append(self.resolve_sub(sem, full_domain))

        # Run tasks and show progress
        await asyncio.gather(*tasks)
        print(f"\n[+] Scan Complete. Total unique subdomains: {len(self.found_subdomains)}")
        print(f"[+] Results saved to: {self.output_path}")

async def main():
    target = input("Enter target domain (e.g., google.com): ").strip()
    wordlist = "wordlist.txt" # Ensure this file exists
    output = "sublist.txt"

    # Clear previous output file
    if os.path.exists(output):
        os.remove(output)

    scanner = SubdomainScanner(target, wordlist, output)
    await scanner.brute_force()

if __name__ == "__main__":
    # Performance note: aiodns requires a selector loop on Windows
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Scan cancelled by user.")
