#this code is for testing that the website is vulnerable to clickjacking 
#and also to generate a proof of concept (PoC) for the vulnerability
import requests
def Url_checking(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    return url

def Clickjacking_checking(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        if 'X-Frame-Options' not in response.headers:
            print(f"[+] {url} is vulnerable to clickjacking.")
            return True
        else:
            print(f"[-] {url} is not vulnerable to clickjacking.")
            return False
    except requests.RequestException as e:
        print(f"Error checking {url}: {e}")
        return False
def generate_poc(url):
    poc = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Clickjacking PoC</title>
        <style>
            body, html {{
                margin: 0;
                padding: 0;
                height: 100%;
                width: 100%;
            }}
            iframe {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border: none;
            }}
        </style>
    </head>
    <body>
        <iframe src="{url}"></iframe>
    </body>
    </html>
    """
    with open("clickjacking_poc.html", "w") as file:
        file.write(poc)
    print(f"PoC generated and saved as clickjacking_poc.html for {url}.")
if __name__ == "__main__":
    target_url = input("Enter the URL to check for clickjacking vulnerability: ")
    target_url = Url_checking(target_url)
    if Clickjacking_checking(target_url):
        generate_poc(target_url)
    else:
        print("The target URL is not vulnerable to clickjacking.")

# the location of generated POC is in the same folder or directory where the script is run

