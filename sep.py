import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_ip(ip, timeout=2):
    ip = ip.strip()
    url = f"http://{ip}"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.info(f"IP {ip} failed to respond within the timeout: {e}")
        return None

    if 'src="admin/LoginFiles/custom.jpg"' in response.text:
        logging.info(f"IP {ip} is XPON")
        return "xpon", ip

    elif "Copyright (c) Realtek Semiconductor Corp., 2003. All Rights Reserved." in response.text:
        logging.info(f"IP {ip} is Realtek GPON")
        return "realtek", ip

    elif "add by runt for bug#0001004 on 20190404" in response.text or "/* Added by peichao for mission#0007440 */" in response.text:
        logging.info(f"IP {ip} is Uniway")
        return "uniway", ip

    elif "Home Gateway" in response.text:
        logging.info(f"IP {ip} is Home Gateway")
        return "home_gateway", ip

    elif '<img src="web/images/logo.png" alt="">' in response.text:
        logging.info(f"IP {ip} is Onu WEB System (mini-httpd)")
        return "mini", ip

    elif "/doc/page/login.asp?_" in response.text:
        logging.info(f"IP {ip} is HIKVision")
        return "hik", ip

    elif f'document.location = "login.asp";;' in response.text:
        logging.info(f"IP {ip} is Onu WEB System (boa)")
        return "boa", ip

    elif "LuCI - Lua Configuration Interface" in response.text:
        logging.info(f"IP {ip} is LuCi")
        return "luci", ip

    else:
        logging.info(f"IP {ip} is Unknown")
        return "unknown", ip

def main():
    # Read IP list from file
    try:
        with open("alive.txt", "r") as file:
            ip_list = file.read().splitlines()
    except Exception as e:
        logging.error(f"Error reading IP list from file: {e}")
        return

    # Create a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(check_ip, ip): ip for ip in ip_list}

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

        # Collect the results and populate the respective IP lists
        for future in as_completed(future_to_ip):
            try:
                result = future.result()
                if result is not None:
                    ip_type, ip = result
                    ip_results[ip_type].append(ip)
            except Exception as e:
                logging.error(f"Error processing IP {future_to_ip[future]}: {e}")

    # Sort IP addresses in each category and save results to files
    for ip_type, ips in ip_results.items():
        try:
            sorted_ips = sorted(ips, key=lambda ip: int(ipaddress.IPv4Address(ip)))
            with open(f"{ip_type}.txt", "w") as file:
                file.write("\n".join(sorted_ips))
            logging.info(f"Results for {ip_type} saved to {ip_type}.txt")
        except Exception as e:
            logging.error(f"Error saving results for {ip_type}: {e}")

if __name__ == "__main__":
    main()
