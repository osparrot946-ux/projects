# this code will help in checking DMARC records for a given domain
#also this code is checking to spf records 
# Make sure to install the dnspython library before running this code
# You can install it using pip: pip install dnspython
import dns.resolver
import re

def get_spf(domain):
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 6
        resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Use Google's DNS servers
        # you can also use other DNS servers if needed like 1.1.1.1,1.0.0.1 for cloudflare

        answers = resolver.resolve(domain, 'TXT')
        for rdata in answers:
            for txt_string in rdata.strings:
                decoded_string = txt_string.decode()
                if decoded_string.startswith('v=spf1'):
                    return decoded_string
        return "No SPF record found"
    except Exception as e:
        return f"Error retrieving SPF record: {e}"

def get_dmarc(domain):
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 6
        resolver.nameservers = ['8.8.8.8', '8.8.4.4']

        dmarc_domain = f"_dmarc.{domain}"
        answers = resolver.resolve(dmarc_domain, 'TXT')
        for rdata in answers:
            for txt_string in rdata.strings:
                decoded_string = txt_string.decode()
                if decoded_string.startswith('v=DMARC1'):
                    return decoded_string
        return "No DMARC record found"
    except Exception as e:
        return f"Error retrieving DMARC record: {e}"

def check_email_auth_records(domain):
    print(f"Checking DNS records for domain: {domain}\n")
    print("SPF Record:")
    print(get_spf(domain))
    print("\nDMARC Record:")
    print(get_dmarc(domain))

if __name__ == "__main__":
    domain_to_check = input("Enter the domain to check: ")
    check_email_auth_records(domain_to_check)

