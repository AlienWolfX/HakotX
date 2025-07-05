import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_ip(ip, timeout=4):
    ip = ip.strip()
    url = f"http://{ip}"

    try:
        response = requests.get(url, timeout=timeout)
        response_hash = hashlib.md5(response.text.encode()).hexdigest()
        response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        logging.info(f"IP {ip} failed to respond within the timeout: {e}")
        return None
    
    if "e474ea77307d75a23761377527e50bb4" in response_hash:
        logging.info(f"IP {ip} is SPU-GE22WD-H")
        return "SPU-GE22WD-H", ip

    elif "Copyright (c) Realtek Semiconductor Corp., 2003. All Rights Reserved." in response.text:
        logging.info(f"IP {ip} is Realtek GPON")
        return "realtek", ip

    elif "add by runt for bug#0001004 on 20190404" in response.text or "/* Added by peichao for mission#0007440 */" in response.text:
        logging.info(f"IP {ip} is Uniway")
        return "uniway", ip

    elif "58c428178693963ffbae98857bb5f263" in response_hash:
        logging.info(f"IP {ip} is ONU4FER1TVASWB")
        return "ONU4FER1TVASWB", ip
    
    elif "b03c4b0b71167fb988046e201a23b8b7" in response_hash:
        logging.info(f"IP {ip} is SPU-GE120W-H")
        return "SPU-GE120W-H", ip

    elif "df1d6d405702aa678f0ef3cf80105874" in response_hash:
        logging.info(f"IP {ip} is KingType(PN_BH2_03-02)")
        return "PN_BH2_03-02", ip

    elif "16330cbd9f45bbe158679410ede94156" in response_hash:
        logging.info(f"IP {ip} is KingType(XPN_RH2_00-07)")
        return "XPN_RH2_00-07", ip

    elif "b55993cb73060a58d829dc134ca2be09" in response_hash:
        logging.info(f"IP {ip} is KingType(AR9331)")
        return "AR9331", ip
    
    elif "82fc2f1160692df5c19a127728037f47" in response_hash: 
        logging.info(f"IP {ip} is KingType(GPNF14C)")
        return "GPNF14C", ip

    else:
        logging.info(f"IP {ip} is Unknown")
        return "unknown", ip

def main():
    # Read IP list from file
    try:
        with open("ips/alive.txt", "r") as file:
            ip_list = file.read().splitlines()
    except Exception as e:
        logging.error(f"Error reading IP list from file: {e}")
        return

    # Create a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_ip = {executor.submit(check_ip, ip): ip for ip in ip_list}

        # Create lists to store results for each IP type
        ip_results = {
            "uniway": [],
            "realtek": [],
            "ONU4FER1TVASWB": [],
            "PN_BH2_03-02": [],
            "SPU-GE22WD-H": [],
            "XPN_RH2_00-07": [],
            "AR9331": [],
            "GPNF14C": [],
            "SPU-GE120W-H": [],
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
            with open(f"ips/{ip_type}.txt", "w") as file:
                file.write("\n".join(sorted_ips))
            logging.info(f"Results for {ip_type} saved to {ip_type}.txt")
        except Exception as e:
            logging.error(f"Error saving results for {ip_type}: {e}")

    # Save failed IPs
    try:
        sorted_failed = sorted(failed_ips, key=lambda ip: int(ipaddress.IPv4Address(ip)))
        with open("ips/sep_failed.txt", "w") as file:
            file.write("\n".join(sorted_failed))
        logging.info("Failed IPs saved to sep_failed.txt")
    except Exception as e:
        logging.error(f"Error saving failed IPs: {e}")

if __name__ == "__main__":
    main()
