import requests

ip = input("Enter IP address (w/o http): ")
url = f"http://{ip}"

try:
    response = requests.get(url, timeout=5)
    server_info = response.headers.get('Server', 'Unknown')
    print(f"Server: {server_info}")
    
    if server_info == 'micro_httpd':
        print("Possible vulnerability")
        
    else:
        print("Not vulnerable")

except requests.exceptions.RequestException as e:
    print(f"Failed to connect: {e}")
