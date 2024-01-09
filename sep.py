import requests
from multiprocessing.pool import ThreadPool


def check_ip(ip):
    ip = ip.strip()
    url = f"http://{ip}"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Check for any HTTP errors
    except requests.exceptions.RequestException:
        print(f"IP {ip} failed to respond within the timeout")
        return None

    if 'src="admin/LoginFiles/custom.jpg"' in response.text:
        print(f"IP {ip} is XPON")
        return "xpon", ip

    elif (
        "Copyright (c) Realtek Semiconductor Corp., 2003. All Rights Reserved."
        in response.text
    ):
        print(f"IP {ip} is Realtek GPON")
        return "realtek", ip

    elif "add by runt for bug#0001004 on 20190404" in response.text:
        print(f"IP {ip} is Uniway")
        return "uniway", ip

    elif "Home Gateway" in response.text:
        print(f"IP {ip} is Home Gateway")
        return "home_gateway", ip

    elif '<img src="web/images/logo.png" alt="">' in response.text:
        print(f"IP {ip} is Onu WEB System (mini-httpd)")
        return "mini", ip

    elif "/doc/page/login.asp?_" in response.text:
        print(f"IP {ip} is HIKVision")
        return "hik", ip

    elif "login.asp" in response.text:
        print(f"IP {ip} is Onu WEB System (boa)")
        return "boa", ip

    elif "LuCI - Lua Configuration Interface" in response.text:
        print(f"IP {ip} is LuCi")
        return "luci", ip

    else:
        print("Unknown")
        return "unknown", ip


# Read IP list from file
with open("alive.txt", "r") as file:
    ip_list = file.read().splitlines()

timeout = 2

# Create a ThreadPool with the number of desired workers
pool = ThreadPool(processes=10)

# Create lists to store results for each IP type
ip_results = {
    "uniway": [],
    "realtek": [],
    "home_gateway": [],
    "mini": [],
    "boa": [],
    "luci": [],
    "unknown": [],
    "hik": [],
    "xpon": [],
}

# Use ThreadPool to asynchronously process each IP
results = pool.map(check_ip, ip_list)

# Collect the results and populate the respective IP lists
for result in results:
    if result is not None:
        ip_type, ip = result
        ip_results[ip_type].append(ip)

# Save results to files
for ip_type, ips in ip_results.items():
    with open(f"{ip_type}.txt", "w") as file:
        file.write("\n".join(ips))
