import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_ip(ip, timeout=4):
    ip = ip.strip()
    url = f"http://{ip}"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.info(f"IP {ip} failed to respond within the timeout: {e}")
        return None
    
    if "Welcome to XPON ONU" in response.text:
        logging.info(f"IP {ip} is Sopto XPON")
        return "sopto", ip

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

    elif f'document.location = "login.asp";;' in response.text:
        logging.info(f"IP {ip} is Onu WEB System (boa)")
        return "boa", ip

    elif "LuCI - Lua Configuration Interface" in response.text:
        logging.info(f"IP {ip} is LuCi")
        return "luci", ip
    
    elif f'document.location = "index.asp";' in response.text: 
        logging.info(f"IP {ip} is GPNF14C")
        return "gpnf14c", ip

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
            "sopto": [],
            "boa": [],
            "luci": [],
            "gpnf14c": [],
            "unknown": [],
        }
        failed_ips = []

        # Collect the results and populate the respective IP lists
        for future in as_completed(future_to_ip):
            try:
                result = future.result()
                if result is not None:
                    ip_type, ip = result
                    ip_results[ip_type].append(ip)
                else:
                    failed_ips.append(future_to_ip[future])
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

    # Save failed IPs
    try:
        sorted_failed = sorted(failed_ips, key=lambda ip: int(ipaddress.IPv4Address(ip)))
        with open("sep_failed.txt", "w") as file:
            file.write("\n".join(sorted_failed))
        logging.info("Failed IPs saved to sep_failed.txt")
    except Exception as e:
        logging.error(f"Error saving failed IPs: {e}")

if __name__ == "__main__":
    main()
