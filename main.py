import concurrent.futures
import socket
import subprocess
import logging
import ipaddress
import signal
import os
import time
import sys
from tqdm import tqdm

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

stop_script = False

def signal_handler(sig, frame):
    global stop_script
    logging.info("Signal received, stopping the script...")
    stop_script = True

def check_ip(ip):
    """Checks if the specified IP address is alive."""
    if stop_script:
        return ip, False
    try:
        socket.setdefaulttimeout(2)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, 80))
        return ip, True
    except (socket.timeout, ConnectionRefusedError, socket.error) as e:
        logging.debug(f"IP {ip} check failed: {e}")
        return ip, False

def process_ip_range(ip_range):
    """Processes a range of IP addresses and returns lists of alive and dead IPs."""
    alive_ips = []
    dead_ips = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_ip, ip): ip for ip in ip_range}

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Checking IPs"):
            if stop_script:
                break
            ip = futures[future]
            try:
                ip, is_alive = future.result()
                if is_alive:
                    alive_ips.append(ip)
                    logging.info(f"IP {ip} is alive")
                else:
                    dead_ips.append(ip)
                    logging.info(f"IP {ip} is dead")
            except Exception as e:
                logging.error(f"Error processing IP {ip}: {e}")

    return alive_ips, dead_ips

def ensure_files_exist():
    """Ensure that alive.txt and dead.txt files exist."""
    files = ["ips/alive.txt", "ips/dead.txt"]
    for file in files:
        try:
            if not os.path.exists(file):
                with open(file, "w") as f:
                    pass 
                logging.info(f"Created {file}")
        except Exception as e:
            logging.error(f"Failed to create {file}: {e}")

def main():
    """Main function that processes a range of IP addresses and saves the results to files."""
    ensure_files_exist()
    
    ip_range1 = [str(ip) for ip in ipaddress.IPv4Network('172.17.0.0/20')]
    ip_range2 = [str(ip) for ip in ipaddress.IPv4Network('172.18.0.0/20')]
    ip_range3 = [str(ip) for ip in ipaddress.IPv4Network('10.17.0.0/20')]
    ip_range4 = [str(ip) for ip in ipaddress.IPv4Network('10.18.0.0/20')]

    ip_range = ip_range1 + ip_range2 + ip_range3 + ip_range4

    logging.info("Starting IP range processing.")
    alive_ips, dead_ips = process_ip_range(ip_range)
    
    if stop_script:
        logging.info("Script stopped before completion.")
        return

    try:
        with open("ips/alive.txt", "w") as alive_file:
            alive_file.write("\n".join(alive_ips))
        logging.info("Alive IPs saved to alive.txt.")
    except Exception as e:
        logging.error(f"Failed to save alive IPs: {e}")

    try:
        with open("ips/dead.txt", "w") as dead_file:
            dead_file.write("\n".join(dead_ips))
        logging.info("Dead IPs saved to dead.txt.")
    except Exception as e:
        logging.error(f"Failed to save dead IPs: {e}")

    # Preparation
    try:
        subprocess.run([sys.executable, "clean.py"], check=True)
        time.sleep(2)
        subprocess.run([sys.executable, "sep.py"], check=True)
        logging.info("Subprocesses completed successfully.")
        time.sleep(2)
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess failed: {e}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
    logging.info("Done!")