import requests
import sys
import re

def is_valid_host(host):
    return re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", host) or re.match(r"^[a-zA-Z0-9.-]+$", host)

def check_server(ip_or_host, use_https=False):
    scheme = "https" if use_https else "http"
    url = f"{scheme}://{ip_or_host}"
    try:
        response = requests.get(url, timeout=5, verify=False)
        server_info = response.headers.get('Server', 'Unknown')
        print(f"[+] Connected to {url}")
        print(f"[+] Server header: {server_info}")

        if server_info.lower() == 'micro_httpd':
            print("[!] Possible vulnerability: Detected micro_httpd server")
        else:
            print("[*] No known vulnerability detected for this server header")
    except requests.exceptions.RequestException as e:
        print(f"[!] Failed to connect to {url}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("Enter IP address or hostname (w/o http/https): ").strip()

    if not is_valid_host(ip):
        print("[!] Invalid IP address or hostname.")
        sys.exit(1)

    print("[*] Checking HTTP...")
    check_server(ip, use_https=False)
    print("[*] Checking HTTPS...")
    check_server(ip, use_https=True)
